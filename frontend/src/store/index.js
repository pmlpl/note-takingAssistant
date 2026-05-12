import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

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

  const isLoggedIn = computed(() => {
    const result = !!token.value && !!user.value
    return result
  })

  function login(tokenValue, userData) {
    token.value = tokenValue
    user.value = userData
    localStorage.setItem('token', tokenValue)
    localStorage.setItem('user', JSON.stringify(userData))
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return {
    token,
    user,
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