import api from './index'

/** 本地大模型可能较慢，默认 10 分钟；可通过环境变量覆盖 */
const AI_REQUEST_TIMEOUT_MS =
  Number(import.meta.env.VITE_AI_REQUEST_TIMEOUT_MS) || 600_000

export const aiApi = {
  generateNote(data) {
    return api.post('/v1/ai/generate-note', data, { timeout: AI_REQUEST_TIMEOUT_MS })
  },

  summarizeNote(data) {
    return api.post('/v1/ai/summarize-note', data, { timeout: AI_REQUEST_TIMEOUT_MS })
  },

  translateNote(data) {
    return api.post('/v1/ai/translate-note', data, { timeout: AI_REQUEST_TIMEOUT_MS })
  },

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
