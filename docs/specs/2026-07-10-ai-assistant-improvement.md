# AI 助手功能改进方案

> **归档说明**：本方案核心已由 commit `ba99667`（2026-07-10「重构 AI 助手为单一主 Agent 架构」）实现：`agent-chat-stream` 端点、`ai_conversations`/`ai_messages` 持久化、`services/agent/` 多 Agent 工具调用均已落地。归档保留，不再作为待办。

## 一、现状分析

### 1.1 当前能力

现有 AI 助手位于首页右侧面板（HomeAiChatPanel），具备以下能力：

| 能力 | 说明 |
|------|------|
| 基础对话 | 与用户进行自然语言问答 |
| 笔记上下文 | 支持上传笔记文件或通过 `/note` 选择笔记作为上下文 |
| 思维导图快捷命令 | 一键生成思维导图提示词 |
| 历史记录（前端） | 前端内存保留最近若干条对话，刷新即丢失 |
| 流式输出 | 支持流式对话（chat-stream 接口） |

### 1.2 相关 AI 功能（分散在独立页面）

| 功能 | 页面 | 说明 |
|------|------|------|
| AI 生成笔记 | /ai/generate | 根据主题生成完整笔记 |
| AI 总结笔记 | /ai/summarize | 分析笔记质量，给出优缺点和建议 |
| 笔记翻译 | /ai/translate | 全文翻译，保留 Markdown 结构 |
| 知识图谱 | /kg | 基于笔记生成知识图谱 |

### 1.3 核心问题

**问题1：功能碎片化**
- AI 助手只能纯对话，无法主动调用笔记工具
- 生成、总结、翻译、思维导图都在独立页面，用户需要手动跳转
- 各功能之间没有串联，无法完成"找笔记→总结→翻译"这类复合任务

**问题2：无主动工具调用能力**
- AI 助手只能"说"，不能"做"
- 用户想总结笔记，得自己先复制内容、打开总结页、粘贴、点击生成
- 不能像真正的助手一样说一声就自动完成

**问题3：对话历史无持久化**
- 历史存在前端 `chatHistory.value`（内存）
- 刷新页面、换设备就没了
- 没有对话会话管理

**问题4：单模型单角色**
- 所有任务都用同一个提示词（CHAT_SYSTEM_PROMPT）
- 总结、翻译、生成等专业任务由通用对话模型完成，质量不如专用页面

---

## 二、改进目标

将 AI 助手从"纯对话机器人"升级为"**多工具多 Agent 智能助手**"，实现：

1. **自然语言驱动**：用户说一句话，助手自动判断该用什么工具、按什么顺序执行
2. **功能整合**：把生成、总结、翻译、思维导图等功能都接入 AI 助手，不再需要跳转页面
3. **多 Agent 协作**：不同任务交给不同专业 Agent，质量更高
4. **持久化记忆**：对话历史存数据库，支持多设备同步
5. **向下兼容**：现有独立 AI 页面保留，AI 助手作为统一入口

---

## 三、具体改进方案

### 3.1 方案一：Function Calling 工具调用（优先级：高）

**目标**：让 AI 助手能主动调用笔记相关工具。

#### 新增工具列表

| 工具名称 | 功能描述 | 对应现有代码 |
|----------|---------|-------------|
| `search_notes` | 搜索用户的笔记，返回匹配的笔记列表 | 基于 note CRUD 新增 |
| `get_note_content` | 获取指定笔记的完整内容 | 基于 note CRUD |
| `summarize_note` | 总结笔记内容，输出摘要和关键要点 | note_analyzer.py |
| `generate_note` | 根据主题生成新的笔记 | note_generator.py |
| `translate_note` | 翻译笔记内容到指定语言 | note_translator.py |
| `create_note` | 创建新笔记保存到数据库 | note CRUD |

#### 实现思路

1. 后端新建 `app/services/agent_service.py`，实现带工具调用的对话逻辑
2. 定义 `tools_definition`（JSON Schema 格式）
3. 实现 `tools_mapping`（工具名 → 实际函数映射）
4. 对话流程：
   ```
   用户消息 → 模型判断是否需要工具 → 需要则执行工具 → 结果回传模型 → 生成最终回答
   ```

#### 后端改动

- 新增 `app/services/agent_service.py`（Agent 对话服务，含工具调用）
- 修改 `app/api/v1/ai.py`，新增 `/api/v1/ai/agent-chat` 接口
- 复用 `note_generator.py`、`note_analyzer.py`、`note_translator.py` 中的逻辑

#### 前端改动

- 修改 `useAIAssistant.js`，调用新的 agent-chat 接口
- 增加工具调用过程的可视化（可选）

---

### 3.2 方案二：多 Agent 协作（优先级：中）

**目标**：不同任务交给专业 Agent，提升回答质量。

#### Agent 角色设计

| Agent | 角色 | 适用场景 |
|-------|------|---------|
| 通用对话 Agent | 笔记助手总调度 | 闲聊、简单问答、任务分发 |
| 搜索 Agent | 笔记检索专家 | 查找笔记、获取内容 |
| 总结 Agent | 笔记分析专家 | 总结、提炼要点、质量评估 |
| 生成 Agent | 笔记创作专家 | 根据主题生成新笔记 |
| 翻译 Agent | 多语言翻译专家 | 笔记翻译、术语保留 |
| 思维导图 Agent | 结构化表达专家 | 生成思维导图 Mermaid 代码 |

#### 实现思路

1. 新建 `app/services/agent/coordinator.py`（调度员）
2. 新建 `app/services/agent/agents/`（各专业 Agent）
3. Coordinator 先分析用户意图，决定调用哪些 Agent、按什么顺序
4. 各 Agent 依次执行，结果汇总后返回

#### 与方案一的关系

- 方案一是基础（让模型能调用工具）
- 方案二是进阶（让多个专业 Agent 协作）
- 可以先做方案一，再逐步升级到方案二

---

### 3.3 方案三：对话历史持久化（优先级：高）

**目标**：用户的对话历史存数据库，支持多设备同步。

#### 数据模型设计

新建 `ai_conversations` 表：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| user_id | Integer | 所属用户 |
| title | String | 对话标题（自动生成） |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 最后更新时间 |

新建 `ai_messages` 表：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| conversation_id | Integer | 所属对话 |
| role | String | user / assistant / tool |
| content | Text | 消息内容 |
| created_at | DateTime | 创建时间 |

#### 后端改动

- 新增 `app/models/ai_conversation.py`（对话模型）
- 新增 `app/crud/ai_conversation.py`（CRUD 操作）
- 修改 AI 接口，支持 `conversation_id` 参数
- 新增对话列表接口、创建对话接口、删除对话接口

#### 前端改动

- 左侧增加对话列表（类似 ChatGPT）
- 支持新建对话、切换对话、删除对话
- `chatHistory` 从后端加载而不是纯内存

---

### 3.4 方案四：流式输出增强（优先级：低）

**目标**：现有流式输出已不错，增加工具调用过程的流式展示。

#### 增强内容

- 展示 Agent 的"思考过程"（工具调用前的分析）
- 展示工具执行进度（"正在搜索笔记..."、"正在总结..."）
- 中间结果实时更新，不用等全部完成

---

## 四、实施路径建议

### 第一阶段：工具调用（1-2周）

```
第1步：定义工具 Schema 和工具映射
第2步：实现带 Function Calling 的 Agent 对话服务
第3步：新增 agent-chat 接口
第4步：前端 AI 助手接入新接口
第5步：测试、联调
```

**产出**：AI 助手能主动搜索笔记、获取内容、总结、翻译

### 第二阶段：持久化记忆（1周）

```
第1步：设计数据库表结构，写 Alembic 迁移
第2步：实现对话 CRUD 接口
第3步：前端增加对话列表组件
第4步：联调测试
```

**产出**：对话历史不丢失，支持多设备同步

### 第三阶段：多 Agent 协作（2周，可选）

```
第1步：实现 Coordinator 调度员
第2步：拆分各专业 Agent
第3步：实现 Agent 间结果传递
第4步：前端展示多 Agent 协作过程
```

**产出**：复杂任务自动拆分，质量更高

### 第四阶段：优化打磨（持续）

- 提示词优化
- 工具调用准确度提升
- 性能优化
- 错误处理增强

---

## 五、技术要点

### 5.1 工具调用格式

使用 OpenAI 兼容的 Function Calling 格式（与 DeepSeek、通义千问等兼容）：

```python
tools_definition = [
    {
        "type": "function",
        "function": {
            "name": "search_notes",
            "description": "搜索用户的笔记，返回匹配的笔记列表",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "limit": {"type": "integer", "description": "返回数量上限", "default": 5}
                },
                "required": ["query"]
            }
        }
    }
]
```

### 5.2 与现有代码复用

| 现有模块 | 复用到哪 |
|---------|---------|
| `note_generator.py` | generate_note 工具 |
| `note_analyzer.py` | summarize_note 工具 |
| `note_translator.py` | translate_note 工具 |
| `crud/note.py` | search_notes、get_note_content、create_note 工具 |
| `llm_runtime.py` | 模型客户端（用户 BYOK 支持） |
| `chat_service.py` | 基础对话逻辑，增加工具调用分支 |

### 5.3 兼容性保证

- 现有 `/chat`、`/chat-stream` 接口保留
- 新增 `/agent-chat`、`/agent-chat-stream` 接口
- 前端 AI 助手默认使用新接口，可降级到旧接口
- 独立 AI 页面（生成、总结、翻译）保持不变

---

## 六、预期效果

| 指标 | 改进前 | 改进后 |
|------|--------|--------|
| 可用功能 | 纯对话 | 对话 + 6种工具 |
| 完成"总结笔记"操作 | 3步（复制→跳转→粘贴） | 1步（说一句话） |
| 对话历史 | 前端内存，刷新丢失 | 数据库持久化 |
| 任务复杂度上限 | 单轮问答 | 多步骤复合任务 |
| 回答专业性 | 通用模型 | 专业 Agent 分工 |

---

## 七、风险与注意事项

1. **Token 消耗增加**：工具调用需要多次 API 请求，成本上升
   - 缓解：合理设置 max_tokens，简单任务直接回答不调工具

2. **响应时间变长**：多轮工具调用 + 多 Agent 串行，耗时增加
   - 缓解：流式输出 + 进度展示，让用户感知在工作

3. **工具调用准确率**：模型可能调错工具或传错参数
   - 缓解：完善的参数校验 + 错误兜底 + 提示词优化

4. **数据库压力**：每次对话存多条消息，数据量增长快
   - 缓解：定期清理历史、设置保留上限、按用户分表
