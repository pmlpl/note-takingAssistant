import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAIStore = defineStore('ai', () => {
  // AI 聊天记录（按页面分类）
  const chatHistories = ref({
    home: [],           // 首页 AI 助手
    generate: [],       // AI 生成页面
    summarize: []       // AI 总结页面
  })

  // 当前正在思考的状态
  const thinkingStates = ref({
    home: false,
    generate: false,
    summarize: false
  })

  // 添加聊天消息
  function addMessage(page, message) {
    if (!chatHistories.value[page]) {
      chatHistories.value[page] = []
    }
    chatHistories.value[page].push(message)

    // 保存到 localStorage（可选）
    saveToLocalStorage()
  }

  // 设置思考状态
  function setThinking(page, isThinking) {
    thinkingStates.value[page] = isThinking
  }

  // 清除某个页面的聊天记录
  function clearHistory(page) {
    chatHistories.value[page] = []
    saveToLocalStorage()
  }

  // 保存到 localStorage
  function saveToLocalStorage() {
    try {
      localStorage.setItem('ai_chat_histories', JSON.stringify(chatHistories.value))
    } catch (e) {
      console.error('Failed to save AI chat histories:', e)
    }
  }

  // 从 localStorage 恢复
  function loadFromLocalStorage() {
    try {
      const saved = localStorage.getItem('ai_chat_histories')
      if (saved) {
        chatHistories.value = JSON.parse(saved)
      }
    } catch (e) {
      console.error('Failed to load AI chat histories:', e)
    }
  }

  // 初始化时加载
  loadFromLocalStorage()

  return {
    chatHistories,
    thinkingStates,
    addMessage,
    setThinking,
    clearHistory
  }
})
