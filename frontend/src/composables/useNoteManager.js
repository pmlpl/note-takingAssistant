/**
 * 笔记管理 Composable
 * 负责笔记的加载、查看、编辑等操作
 */
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { noteApi } from '@/api/note'
import api from '@/api/index'  // 导入 api 实例用于覆盖上传
import { ElMessage } from 'element-plus'
import { renderContentToSafeHtml } from '@/utils/htmlSanitize'
import { MESSAGE_DURATION } from '@/utils/common'
import { MAX_IMPORT_SIZE } from '@/config/api'

export function useNoteManager() {
  const router = useRouter()
  
  // 状态
  const recentNotes = ref([])
  const currentNote = ref(null)
  const allNotes = ref([])
  
  // 计算属性
  const renderedContent = computed(() => {
    if (!currentNote.value?.content) return ''
    return renderContentToSafeHtml(currentNote.value.content)
  })
  
  const filteredNotes = computed(() => {
    return allNotes.value
  })
  
  /**
   * 加载最近笔记
   */
  async function loadRecentNotes() {
    try {
      const notes = await noteApi.getRecentNotes()
      recentNotes.value = notes
    } catch (error) {
      console.error('加载最近笔记失败:', error)
      ElMessage.error({ message: '加载最近笔记失败', duration: MESSAGE_DURATION.SHORT })
    }
  }
  
  /**
   * 加载所有笔记
   */
  async function loadAllNotes() {
    try {
      const notes = await noteApi.getNotes()
      allNotes.value = notes
    } catch (error) {
      console.error('加载所有笔记失败:', error)
    }
  }
  
  /**
   * 查看笔记（完全异步，不阻塞UI）
   */
  function viewNote(note) {
    setTimeout(async () => {
      try {
        // 立即更新标题
        currentNote.value = { ...note, loading: true }
        
        // 强制 Vue 更新 DOM
        await new Promise(resolve => setTimeout(resolve, 0))
        
        // 获取完整内容
        const fullNote = await noteApi.getNote(note.id)
        currentNote.value = fullNote
        
        // 显示成功提示
        ElMessage.success({ message: '加载成功', duration: MESSAGE_DURATION.SHORT })
        
        // 后台更新列表
        updateRecentNotesWithCurrent(fullNote)
      } catch (error) {
        console.error('❌ 加载笔记详情失败:', error)
        ElMessage.error({ message: '加载笔记失败', duration: MESSAGE_DURATION.SHORT })
      }
    }, 0)
  }
  
  /**
   * 更新最近笔记列表
   */
  async function updateRecentNotesWithCurrent(note) {
    if (!note || !note.id) return
    
    const index = recentNotes.value.findIndex(n => n.id === note.id)
    
    if (index > -1) {
      recentNotes.value.splice(index, 1)
      recentNotes.value.unshift(note)
    } else {
      recentNotes.value.unshift(note)
      if (recentNotes.value.length > 5) {
        recentNotes.value = recentNotes.value.slice(0, 5)
      }
    }
    
    // 异步同步到 Redis（不阻塞UI）
    setTimeout(async () => {
      try {
        const noteIds = recentNotes.value.map(n => n.id)
        await noteApi.updateRecentNotesOrder(noteIds)
      } catch (error) {
        console.error('❌ 同步最近笔记顺序失败:', error)
      }
    }, 0)
  }
  
  /**
   * 创建新笔记
   */
  function createNewNote() {
    router.push('/notes/edit')
  }
  
  /**
   * 编辑笔记
   */
  function editNote(note) {
    router.push(`/notes/edit/${note.id}`)
  }
  
  /**
   * 跳转到历史笔记
   */
  function goToHistory() {
    router.push('/notes/history')
  }
  
  /**
   * 导入笔记（后台异步处理）
   */
  function importNote() {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.txt,.md,.docx'
    
    input.onchange = (e) => {
      const file = e.target.files[0]
      if (!file) return
      
      if (file.size > MAX_IMPORT_SIZE) {
        ElMessage.error({ message: `文件大小不能超过${MAX_IMPORT_SIZE / 1024 / 1024}MB`, duration: MESSAGE_DURATION.SHORT })
        return
      }
      
      ElMessage.info({ message: '正在解析文件...', duration: MESSAGE_DURATION.SHORT })
      
      // 后台处理文件
      setTimeout(async () => {
        await processImportedFile(file)
      }, 0)
    }
    
    input.click()
  }
  
  /**
   * 处理导入的文件
   */
  async function processImportedFile(file) {
    try {
      ElMessage.info({ message: '正在上传文件...', duration: MESSAGE_DURATION.SHORT })
      
      // 使用后端提供的 import 接口（会自动缓存到Redis）
      const importedNote = await noteApi.importNote(file)
      
      ElMessage.success({ message: `笔记「${importedNote.title}」导入成功！`, duration: MESSAGE_DURATION.SHORT })
      
      // 立即更新最近笔记列表（同步操作，不等待API）
      updateRecentNotesWithCurrent(importedNote)
      
      // 后台重新加载以确保数据一致性
      loadRecentNotes()
      
      // 显示导入的笔记
      currentNote.value = importedNote
    } catch (error) {
      console.error('导入笔记失败:', error)
      
      // 处理重复笔记错误
      if (error.response?.status === 409) {
        await handleDuplicateNote(error, file)
      } else if (error.code === 'ECONNRESET' || error.message.includes('ECONNRESET')) {
        ElMessage.error({ message: '网络连接中断，请检查网络后重试', duration: MESSAGE_DURATION.NORMAL })
      } else {
        ElMessage.error({ message: error.response?.data?.detail || error.message || '导入失败，请重试', duration: MESSAGE_DURATION.SHORT })
      }
    }
  }
  
  /**
   * 处理重复笔记
   */
  async function handleDuplicateNote(error, file) {
    const { ElMessageBox } = await import('element-plus')
    
    await ElMessageBox.confirm(
      error.response?.data?.detail || '笔记已存在，是否覆盖？',
      '重复笔记',
      { confirmButtonText: '覆盖', cancelButtonText: '取消', type: 'warning' }
    )
    
    // 用户选择覆盖，重新上传并设置 overwrite=true
    const formData = new FormData()
    formData.append('file', file)
    
    try {
      const importedNote = await api.post('/v1/note/import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120_000
      })
      
      ElMessage.success({ message: `笔记「${importedNote.data.title}」已覆盖！`, duration: MESSAGE_DURATION.SHORT })
      
      // 立即更新最近笔记列表（同步操作）
      updateRecentNotesWithCurrent(importedNote.data)
      
      // 后台重新加载以确保数据一致性
      loadRecentNotes()
      
      currentNote.value = importedNote.data
    } catch (err) {
      console.error('覆盖笔记失败:', err)
      ElMessage.error({ message: '覆盖失败，请重试', duration: MESSAGE_DURATION.SHORT })
    }
  }
  
  return {
    // 状态
    recentNotes,
    currentNote,
    allNotes,
    renderedContent,
    filteredNotes,
    
    // 方法
    loadRecentNotes,
    loadAllNotes,
    viewNote,
    createNewNote,
    editNote,
    goToHistory,
    importNote,
    updateRecentNotesWithCurrent
  }
}
