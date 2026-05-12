import api from './index'

export const aiApi = {
  generateNote(data) {
    return api.post('/v1/ai/generate-note', data)
  },
  
  summarizeNote(data) {
    return api.post('/v1/ai/summarize-note', data)
  },
  
  /**
   * AI 对话接口
   * @param {Object} data - 对话数据
   * @param {string} data.message - 用户消息
   * @param {Array} data.history - 聊天历史（可选）
   * @returns {Promise} 返回 AI 回复
   */
  chat(data) {
    return api.post('/v1/ai/chat', data)
  }
}