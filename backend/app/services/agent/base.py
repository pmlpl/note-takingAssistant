"""Agent 基类

每个专业 Agent 继承 BaseAgent，拥有自己的：
- name / display_name / emoji: 标识信息
- system_prompt: 角色定位
- tools: 可用工具列表（工具名 -> 工具实现函数）
- tools_definition: 工具的 JSON Schema

执行流程（由 Coordinator 或上层调用）：
    async for event in agent.run(message, history, *, db, db_user):
        yield event

事件类型（SSE 事件流）：
- thinking: 思考过程
- tool_start / tool_end: 工具调用开始/结束
- delta: 文本增量
- done: 完成（携带 agent_name 标识是哪个 Agent 完成的）
- error: 错误
"""
from __future__ import annotations

import json
import logging
from abc import ABC
from typing import Any, AsyncIterator, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserDB
from app.services.llm_runtime import openai_client_and_model_for_user
from app.utils.llm_errors import format_llm_error

logger = logging.getLogger(__name__)

# 每个 Agent 的最大工具调用轮数
MAX_TOOL_ROUNDS = 5
# 工具结果字符上限
MAX_TOOL_RESULT_CHARS = 4000
# 最终回答切片大小
FINAL_ANSWER_CHUNK_SIZE = 80


def sse_event(event_type: str, data: Optional[Dict[str, Any]] = None) -> str:
    """构造一条 SSE 事件：`data: {json}\\n\\n`"""
    payload = {"type": event_type}
    if data is not None:
        payload.update(data)
    return "data: " + json.dumps(payload, ensure_ascii=False) + "\n\n"


class BaseAgent(ABC):
    """专业 Agent 基类"""

    # --- 子类必须实现的属性 ---
    name: str = "base"
    display_name: str = "基础 Agent"
    emoji: str = "🤖"
    system_prompt: str = ""

    # --- 子类可选覆盖 ---
    tools_definition: List[Dict[str, Any]] = []  # OpenAI Function Calling 格式
    tool_handlers: Dict[str, callable] = {}  # tool_name -> async handler(db, user_id, args)

    # ============== 对外主入口 ==============
    async def run(
        self,
        message: str,
        history: Optional[List[Any]] = None,
        *,
        db: AsyncSession,
        db_user: UserDB,
    ) -> AsyncIterator[str]:
        """执行 Agent 主流程，yield SSE 事件"""
        messages = self._build_messages(message, history)

        try:
            client, model = openai_client_and_model_for_user(db_user)
        except Exception as e:
            yield sse_event("error", {"message": format_llm_error("AI助手", e)})
            return

        use_tools = len(self.tools_definition) > 0

        for round_idx in range(MAX_TOOL_ROUNDS):
            try:
                kwargs: Dict[str, Any] = {
                    "model": model,
                    "messages": messages,
                    "temperature": 0.5,
                    "max_tokens": 2048,
                }
                if use_tools:
                    kwargs["tools"] = self.tools_definition
                    kwargs["tool_choice"] = "auto"  # 让模型自主选择是否调用工具
                response = await client.chat.completions.create(**kwargs)
            except Exception as e:
                if use_tools and self._looks_like_tools_unsupported(e):
                    logger.warning(
                        f"模型 {model} 不支持 tools 参数，[{self.name}] 降级"
                    )
                    use_tools = False
                    async for evt in self._fallback_plain_stream(client, model, messages):
                        yield evt
                    return
                logger.exception(f"[{self.name}] 调用模型失败")
                yield sse_event("error", {"message": format_llm_error("AI助手", e)})
                return

            if not response.choices:
                yield sse_event("error", {"message": "LLM 返回空 choices"})
                return

            choice = response.choices[0]
            msg = choice.message

            tool_calls = getattr(msg, "tool_calls", None)
            if not tool_calls:
                # 没有工具调用：msg.content 就是最终回答，直接输出（不要作为 thinking 推）
                final_text = (msg.content or "").strip()
                async for evt in self._emit_final_answer(final_text):
                    yield evt
                return

            # 有工具调用：msg.content 是思考过程
            if msg.content and msg.content.strip():
                yield sse_event("thinking", {"text": msg.content.strip(), "agent": self.name})

            messages.append(
                {
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments or "{}",
                            },
                        }
                        for tc in tool_calls
                    ],
                }
            )

            for tc in tool_calls:
                tool_name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except Exception:
                    args = {}

                yield sse_event(
                    "tool_start",
                    {"id": tc.id, "name": tool_name, "args": args, "agent": self.name},
                )

                result = await self._execute_tool(
                    tool_name, args, db=db, db_user=db_user
                )
                result_text = self._truncate_tool_result(result)

                try:
                    result_json = json.dumps(result, ensure_ascii=False)
                except Exception:
                    result_json = str(result)
                if len(result_json) <= MAX_TOOL_RESULT_CHARS:
                    tool_end_data = {"id": tc.id, "name": tool_name, "result": result}
                else:
                    tool_end_data = {
                        "id": tc.id,
                        "name": tool_name,
                        "result": {"truncated": True, "preview": result_text[:200]},
                    }
                tool_end_data["agent"] = self.name
                yield sse_event("tool_end", tool_end_data)

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result_text,
                    }
                )

            if round_idx == MAX_TOOL_ROUNDS - 1:
                messages.append(
                    {
                        "role": "system",
                        "content": "已经达到工具调用上限，请直接基于现有信息给出最终回答，不要再调用工具。",
                    }
                )

        # 达到轮数上限，强制生成最终回答
        try:
            final_response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.5,
                max_tokens= 2048,
            )
            final_text = (
                (final_response.choices[0].message.content or "").strip()
                or "抱歉，工具调用次数已达上限，未能给出最终回答。"
            )
            async for evt in self._emit_final_answer(final_text):
                yield evt
        except Exception as e:
            logger.exception(f"[{self.name}] 最终回答生成失败")
            yield sse_event("error", {"message": format_llm_error("AI助手", e)})

    # ============== 工具执行 ==============
    async def _execute_tool(
        self,
        tool_name: str,
        args: Dict[str, Any],
        *,
        db: AsyncSession,
        db_user: UserDB,
    ) -> Dict[str, Any]:
        """执行工具调用（复用 agent_service 中的实现作为兜底）"""
        handler = self.tool_handlers.get(tool_name)
        if handler:
            try:
                return await handler(db=db, user_id=db_user.id, args=args, db_user=db_user)
            except Exception as e:
                logger.exception(f"[{self.name}] 工具 {tool_name} 执行失败")
                return {"error": f"工具执行失败：{str(e)}"}
        # 兜底：调 agent_service 中的 _execute_tool
        from app.services.agent_service import _execute_tool as _legacy_execute_tool

        return await _legacy_execute_tool(tool_name, args, db=db, db_user=db_user)

    # ============== 辅助方法 ==============
    def _build_messages(
        self, message: str, history: Optional[List[Any]] = None
    ) -> List[Dict[str, Any]]:
        """构造发给模型的 messages，每个 Agent 用自己的 system_prompt"""
        conversation: List[Dict[str, Any]] = []
        system_extras: List[str] = []

        for msg in (history or [])[-10:]:
            if isinstance(msg, dict):
                role = str(msg.get("role") or "user")
                content = str(msg.get("content") or "")
            else:
                role = "user"
                content = str(getattr(msg, "content", "") or "")
            if role == "system":
                if content:
                    system_extras.append(content)
                continue
            if role not in ("user", "assistant"):
                role = "user"
            conversation.append({"role": role, "content": content})

        system_content = self.system_prompt
        if system_extras:
            system_content += "\n\n# 附加上下文\n" + "\n\n".join(system_extras)

        messages: List[Dict[str, Any]] = [{"role": "system", "content": system_content}]
        messages.extend(conversation)
        messages.append({"role": "user", "content": message})
        return messages

    def _looks_like_tools_unsupported(self, exc: Exception) -> bool:
        s = str(exc).lower()
        keywords = (
            "tool", "function", "not support", "unsupported",
            "unrecognized", "unknown argument", "unknown parameter", "400",
        )
        return any(k in s for k in keywords) and "401" not in s and "auth" not in s

    def _truncate_tool_result(self, result: Any) -> str:
        try:
            text = json.dumps(result, ensure_ascii=False)
        except Exception:
            text = str(result)
        if len(text) > MAX_TOOL_RESULT_CHARS:
            text = text[:MAX_TOOL_RESULT_CHARS] + "...（结果过长，已截断）"
        return text

    async def _emit_final_answer(self, text: str) -> AsyncIterator[str]:
        if not text:
            text = "抱歉，我暂时无法回答这个问题。"
        chunks = []
        for i in range(0, len(text), FINAL_ANSWER_CHUNK_SIZE):
            chunks.append(text[i : i + FINAL_ANSWER_CHUNK_SIZE])

        for chunk in chunks:
            yield sse_event("delta", {"text": chunk, "agent": self.name})
        yield sse_event("done", {"finish_reason": "stop", "agent": self.name})

    async def _fallback_plain_stream(
        self, client, model: str, messages: List[Dict[str, Any]]
    ) -> AsyncIterator[str]:
        try:
            stream = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=2048,
                stream=True,
            )
            async for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if delta and delta.content is not None:
                    yield sse_event("delta", {"text": delta.content, "agent": self.name})
            yield sse_event("done", {"finish_reason": "stop", "agent": self.name})
        except Exception as e:
            logger.exception(f"[{self.name}] 降级流式失败")
            yield sse_event("error", {"message": format_llm_error("AI助手", e)})
