/**
 * AI 助手 Composable
 * 负责 AI 对话、笔记上传等功能
 */
import { ref } from 'vue'
import { aiApi } from '@/api/ai'
import { noteApi } from '@/api/note'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'
import { MESSAGE_DURATION, hasMeaningfulNoteText, shouldAttachNoteContext, composeUserMessageWithNoteContext } from '@/utils/common'
import mammoth from 'mammoth'

export function useAIAssistant() {
  // 状态
  const aiMessage = ref('')
  const chatHistory = ref([])
  const isAiThinking = ref(false)
  const chatMessagesRef = ref(null)
  const uploadedNoteContent = ref(null)
  const uploadedNoteName = ref('')
  const showNoteSelector = ref(false)
  
  /**
   * 发送消息（完全异步，不阻塞UI）
   */
  async function sendMessage() {
    if (!aiMessage.value.trim() || isAiThinking.value) return
    
    const userMessage = aiMessage.value.trim()
    aiMessage.value = ''

    const hasNoteContext =
      uploadedNoteContent.value && shouldAttachNoteContext(uploadedNoteContent.value)

    // 添加用户消息（附带本条是否绑定了笔记上下文，供气泡下展示）
    chatHistory.value.push({
      role: 'user',
      content: userMessage,
      timestamp: new Date(),
      contextNoteTitle: hasNoteContext ? (uploadedNoteName.value || '笔记') : undefined
    })
    
    await scrollToBottom()
    isAiThinking.value = true
    
    // 后台异步执行 AI 请求
    const aiPromise = (async () => {
      try {
        let messages = chatHistory.value.slice(0, -1).slice(-10).map(msg => ({
          role: msg.role,
          content: msg.content
        }))

        let messageForApi = userMessage
        if (hasNoteContext) {
          messageForApi = composeUserMessageWithNoteContext(
            userMessage,
            uploadedNoteName.value,
            uploadedNoteContent.value
          )
        }

        const result = await aiApi.chat({
          message: messageForApi,
          history: messages
        })
        
        chatHistory.value.push({
          role: 'assistant',
          content: result.data?.reply || '抱歉，我暂时无法回答这个问题。',
          timestamp: new Date()
        })
      } catch (error) {
        console.error('AI 回复失败:', error)
        ElMessage.error({ message: 'AI 服务暂时不可用，请稍后重试', duration: MESSAGE_DURATION.SHORT })
        chatHistory.value.push({
          role: 'assistant',
          content: '抱歉，服务暂时不可用，请稍后重试。',
          timestamp: new Date()
        })
      } finally {
        isAiThinking.value = false
        await scrollToBottom()
      }
    })()
    
    // 立即返回，不等待
  }
  
  /**
   * 发送快捷消息
   */
  function sendQuickMessage(message) {
    aiMessage.value = message
    sendMessage()
  }
  
  /**
   * 渲染消息内容（支持 Markdown）
   */
  function renderMessage(content) {
    return marked.parse(content)
  }
  
  /**
   * 格式化时间
   */
  function formatTime(timestamp) {
    const date = new Date(timestamp)
    const hours = date.getHours().toString().padStart(2, '0')
    const minutes = date.getMinutes().toString().padStart(2, '0')
    return `${hours}:${minutes}`
  }
  
  /**
   * 滚动到底部
   */
  async function scrollToBottom() {
    await new Promise(resolve => setTimeout(resolve, 0))
    if (chatMessagesRef.value) {
      chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
    }
  }
  
  /**
   * 上传笔记到 AI
   */
  function uploadNoteToAI() {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.txt,.md,.docx'
    
    input.onchange = async (e) => {
      const file = e.target.files[0]
      if (!file) return
      
      if (file.size > 10 * 1024 * 1024) {
        ElMessage.error({ message: '文件大小不能超过10MB', duration: MESSAGE_DURATION.SHORT })
        return
      }
      
      try {
        ElMessage.info({ message: '正在读取文件...', duration: MESSAGE_DURATION.SHORT })
        
        let content = ''
        
        if (file.name.endsWith('.docx')) {
          const arrayBuffer = await file.arrayBuffer()
          const result = await mammoth.convertToHtml({ arrayBuffer })
          content = result.value.replace(/<[^>]*>/g, '')
        } else if (file.name.endsWith('.md') || file.name.endsWith('.txt')) {
          content = await file.text()
        } else {
          ElMessage.error({ message: '不支持的文件格式', duration: MESSAGE_DURATION.SHORT })
          return
        }
        
        if (!hasMeaningfulNoteText(content)) {
          ElMessage.error({ message: '文件内容为空', duration: MESSAGE_DURATION.SHORT })
          return
        }
        
        uploadedNoteContent.value = content
        uploadedNoteName.value = file.name
        
        ElMessage.success({ 
          message: `已上传笔记《${file.name}》，现在可以提问了`, 
          duration: MESSAGE_DURATION.SHORT 
        })
      } catch (error) {
        console.error('读取文件失败:', error)
        ElMessage.error({ message: '读取文件失败，请重试', duration: MESSAGE_DURATION.SHORT })
      }
    }
    
    input.click()
  }
  
  /**
   * 清除上传的笔记
   */
  function clearUploadedNote() {
    uploadedNoteContent.value = null
    uploadedNoteName.value = ''
    ElMessage.success({ message: '已清除上传的笔记', duration: MESSAGE_DURATION.SHORT })
  }
  
  /**
   * 处理输入事件，检测 /note 命令
   */
  function handleInput(value) {
    if (value.includes('/note')) {
      showNoteSelector.value = true
    } else {
      showNoteSelector.value = false
    }
  }
  
  /**
   * 关闭笔记选择器
   */
  function closeNoteSelector() {
    showNoteSelector.value = false
    if (aiMessage.value.endsWith('/note')) {
      aiMessage.value = aiMessage.value.slice(0, -5)
    }
  }
  
  /**
   * 解析 GET /note/:id 返回体
   */
  function unwrapNoteResponse(res) {
    if (!res || typeof res !== 'object') return null
    if ('content' in res || 'title' in res || 'id' in res) return res
    if (res.data && typeof res.data === 'object') return res.data
    return res
  }

  /**
   * 选择笔记作为上下文
   */
  async function selectNoteForContext(note) {
    const id = note?.id
    if (id == null) {
      ElMessage.error({ message: '笔记数据无效，请刷新后重试', duration: MESSAGE_DURATION.SHORT })
      return
    }
    try {
      const raw = await noteApi.getNote(id)
      const fullNote = unwrapNoteResponse(raw)
      if (!fullNote) {
        ElMessage.error({ message: '加载笔记失败：响应无效', duration: MESSAGE_DURATION.SHORT })
        return
      }
      const content = fullNote.content
      const title = fullNote.title ?? note.title ?? '未命名笔记'
      if (!shouldAttachNoteContext(content)) {
        ElMessage.warning({
          message: '该笔记正文为空，请先编辑笔记再作为上下文',
          duration: MESSAGE_DURATION.NORMAL
        })
        return
      }
      if (!hasMeaningfulNoteText(content)) {
        ElMessage.info({
          message: '笔记以图表或富文本为主，已尽量提交源码供 AI 参考',
          duration: MESSAGE_DURATION.NORMAL
        })
      }
      uploadedNoteContent.value = typeof content === 'string' ? content : String(content)
      uploadedNoteName.value = title
      showNoteSelector.value = false

      if (aiMessage.value.endsWith('/note')) {
        aiMessage.value = aiMessage.value.slice(0, -5)
      }

      ElMessage.success({
        message: `已选择笔记《${title}》作为上下文`,
        duration: MESSAGE_DURATION.SHORT
      })
    } catch (error) {
      console.error('selectNoteForContext:', error)
      ElMessage.error({ message: '加载笔记失败', duration: MESSAGE_DURATION.SHORT })
    }
  }
  
  return {
    // 状态
    aiMessage,
    chatHistory,
    isAiThinking,
    chatMessagesRef,
    uploadedNoteContent,
    uploadedNoteName,
    showNoteSelector,
    
    // 方法
    sendMessage,
    sendQuickMessage,
    renderMessage,
    formatTime,
    uploadNoteToAI,
    clearUploadedNote,
    handleInput,
    closeNoteSelector,
    selectNoteForContext
  }
}
