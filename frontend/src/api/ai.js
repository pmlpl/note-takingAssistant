import api from './index'
import { useUserStore } from '@/store'
import { streamPlainTextPost } from '@/utils/streamPlainTextPost'

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
