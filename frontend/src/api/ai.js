import api from './index'
import { useUserStore } from '@/store'
import { streamPlainTextPost } from '@/utils/streamPlainTextPost'
import { streamSseEventsPost } from '@/utils/streamSseEvents'

/** 本地大模型可能较慢，默认 10 分钟；可通过环境变量覆盖 */
const AI_REQUEST_TIMEOUT_MS =
  Number(import.meta.env.VITE_AI_REQUEST_TIMEOUT_MS) || 600_000

function authHeaders() {
  const userStore = useUserStore()
  const token = userStore.token || ''
  return token ? { Authorization: `Bearer ${token}` } : {}
}

/**
 * 流式翻译：使用 fetch 读取 text/plain，避免 axios 无法消费 SSE/流式 body。
 * @param {object} opts
 * @param {string} opts.content
 * @param {string} opts.targetLang
 * @param {(accumulated: string) => void} opts.onChunk 每次收到增量后传入当前全文
 * @param {AbortSignal} [opts.signal]
 * @returns {Promise<string>} 最终完整译文
 */
export async function translateNoteStream({ content, targetLang, onChunk, signal }) {
  return streamPlainTextPost({
    url: '/api/v1/ai/translate-note-stream',
    body: { content, targetLang },
    headers: authHeaders(),
    onChunk,
    signal
  })
}

/**
 * 流式生成笔记：fetch 消费 text/plain。
 * @param {object} opts
 * @param {string} opts.topic
 * @param {string} [opts.keywords]
 * @param {number} [opts.wordCount]
 * @param {string[]} [opts.images] data URL 列表
 * @param {{ filename: string, content: string }[]} [opts.referenceNotes]
 * @param {(accumulated: string) => void} opts.onChunk
 * @param {AbortSignal} [opts.signal]
 * @returns {Promise<string>} 完整 Markdown
 */
export async function generateNoteStream({
  topic,
  keywords,
  wordCount,
  images,
  referenceNotes,
  onChunk,
  signal
}) {
  return streamPlainTextPost({
    url: '/api/v1/ai/generate-note-stream',
    body: {
      topic,
      keywords: keywords || undefined,
      wordCount: wordCount ?? 600,
      images: images || [],
      referenceNotes: referenceNotes || []
    },
    headers: authHeaders(),
    onChunk,
    signal
  })
}

/**
 * 首页 AI 助手：流式对话，响应体为纯文本增量。
 * @param {object} opts
 * @param {string} opts.message
 * @param {{ role: string, content: string }[]} [opts.history]
 * @param {(accumulated: string) => void} opts.onChunk
 * @param {AbortSignal} [opts.signal]
 * @returns {Promise<string>}
 */
export async function chatStream({ message, history, onChunk, signal }) {
  return streamPlainTextPost({
    url: '/api/v1/ai/chat-stream',
    body: { message, history: history || [] },
    headers: authHeaders(),
    onChunk,
    signal
  })
}

/**
 * Agent 流式对话：SSE 事件流，支持工具调用过程展示。
 *
 * 事件类型：
 * - { type: 'thinking', text: string } 模型在调用工具前的思考说明
 * - { type: 'tool_start', id: string, name: string, args: object } 开始执行工具
 * - { type: 'tool_end', id: string, name: string, result: object } 工具执行结束
 * - { type: 'delta', text: string } 最终回答的文本增量
 * - { type: 'done', finish_reason?: string } 完成
 * - { type: 'error', message: string } 错误
 *
 * @param {object} opts
 * @param {string} opts.message
 * @param {{ role: string, content: string }[]} [opts.history]
 * @param {number} [opts.conversationId] 对话 ID（持久化场景传入）
 * @param {(event: object) => void} opts.onEvent
 * @param {AbortSignal} [opts.signal]
 * @returns {Promise<void>}
 */
export async function agentChatStream({
  message,
  history,
  conversationId,
  onEvent,
  signal
}) {
  return streamSseEventsPost({
    url: '/api/v1/ai/agent-chat-stream',
    body: {
      message,
      history: history || [],
      conversation_id: conversationId ?? undefined
    },
    headers: authHeaders(),
    onEvent,
    signal
  })
}

/**
 * AI 对话历史持久化相关接口
 */
export async function listConversations() {
  return api.get('/v1/ai/conversations').then((r) => r.data ?? r)
}

export async function createConversation(title) {
  return api.post('/v1/ai/conversations', { title: title || undefined }).then((r) => r.data ?? r)
}

export async function getConversation(conversationId) {
  return api.get(`/v1/ai/conversations/${conversationId}`).then((r) => r.data ?? r)
}

export async function renameConversation(conversationId, title) {
  return api
    .patch(`/v1/ai/conversations/${conversationId}`, { title })
    .then((r) => r.data ?? r)
}

export async function deleteConversation(conversationId) {
  return api.delete(`/v1/ai/conversations/${conversationId}`).then((r) => r.data ?? r)
}

export const aiApi = {
  generateNote(data) {
    return api.post('/v1/ai/generate-note', data, { timeout: AI_REQUEST_TIMEOUT_MS })
  },

  summarizeNote(data) {
    return api.post('/v1/ai/summarize-note', data, { timeout: AI_REQUEST_TIMEOUT_MS })
  },

  translateNoteStream,
  generateNoteStream,
  chatStream,
  agentChatStream,

  // 对话历史持久化
  listConversations,
  createConversation,
  getConversation,
  renameConversation,
  deleteConversation,

  /**
   * AI 对话接口
   * @param {Object} data - 对话数据
   * @param {string} data.message - 用户消息
   * @param {Array} data.history - 聊天历史（可选）
   * @returns {Promise} 返回 AI 回复
   */
  chat(data) {
    return api.post('/v1/ai/chat', data, { timeout: AI_REQUEST_TIMEOUT_MS })
  }
}
