import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/** 登出时仅清除旧版全局 key（按用户隔离的聊天记录保留，供同账号再次登录恢复） */
function clearLegacyHomeCaches() {
  try {
    localStorage.removeItem('home_chat_history')
    localStorage.removeItem('home_current_note')
    localStorage.removeItem('mindmap_mermaid_source')
    sessionStorage.removeItem('mindmap_pending_mermaid_source')
  } catch {
    /* ignore */
  }
}

export const useUserStore = defineStore('user', () => {
  // 安全地从 localStorage 获取数据
  let storedToken = ''
  let storedUser = null
  
  try {
    storedToken = localStorage.getItem('token') || ''
    const userStr = localStorage.getItem('user')
    storedUser = userStr && userStr !== 'null' ? JSON.parse(userStr) : null
  } catch (e) {
    console.error('Failed to parse user data from localStorage:', e)
    // 清除可能损坏的数据
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  const token = ref(storedToken)
  const user = ref(storedUser)
  /** 登录/登出时递增，供首页等 keep-alive 页面感知账号切换 */
  const authSessionEpoch = ref(0)

  const isLoggedIn = computed(() => {
    const result = !!token.value && !!user.value
    return result
  })

  function login(tokenValue, userData) {
    const noteStore = useNoteStore()
    noteStore.setNotes([])
    clearLegacyHomeCaches()
    authSessionEpoch.value += 1
    token.value = tokenValue
    user.value = userData
    localStorage.setItem('token', tokenValue)
    localStorage.setItem('user', JSON.stringify(userData))
  }

  async function logout() {
    const noteStore = useNoteStore()
    noteStore.setNotes([])

    // 先通知后端撤销令牌（此时 token 还在，API 拦截器能正常携带）
    try {
      const { userApi } = await import('@/api/user')
      await userApi.logout()
    } catch {
      // 后端不可用时静默忽略，前端照常清理
    }

    // 再清除本地状态；authSessionEpoch 须最后递增，避免 keep-alive 首页在仍“已登录”时误拉接口
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    clearLegacyHomeCaches()
    authSessionEpoch.value += 1
  }

  return {
    token,
    user,
    authSessionEpoch,
    isLoggedIn,
    login,
    logout
  }
})

export const useNoteStore = defineStore('note', () => {
  const notes = ref([])

  function setNotes(data) {
    notes.value = data
  }

  function addNote(note) {
    notes.value.unshift(note)
  }

  function updateNote(id, updatedNote) {
    const index = notes.value.findIndex(n => n.id === id)
    if (index !== -1) {
      notes.value[index] = { ...notes.value[index], ...updatedNote }
    }
  }

  function deleteNote(id) {
    notes.value = notes.value.filter(n => n.id !== id)
  }

  return {
    notes,
    setNotes,
    addNote,
    updateNote,
    deleteNote
  }
})