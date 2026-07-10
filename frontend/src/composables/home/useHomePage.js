import { ref, computed, onMounted, onActivated, onBeforeUnmount, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store'
import { noteApi } from '@/api/note'
import { aiApi } from '@/api/ai'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  renderMarkdownToSafeHtml,
  sanitizeHtml,
  isLikelyHtmlContent
} from '@/utils/htmlSanitize'
import {
  MESSAGE_DURATION,
  hasMeaningfulNoteText,
  shouldAttachNoteContext,
  composeUserMessageWithNoteContext,
  extractMindmapDiagramSource,
  setMindmapNavBridgeSource,
  prepareMermaidSourceForRender,
  AI_MINDMAP_QUICK_PROMPT,
  MINDMAP_LOCAL_STORAGE_KEY,
  MINDMAP_PENDING_SESSION_KEY
} from '@/utils/common'

export const HOME_PAGE_KEY = Symbol('homePage')

export function useHomePage() {
/** 首页 AI 助手：聊天（含用户/助手）在内存与 localStorage 中最多保留条数，超出丢弃最早消息 */
const HOME_CHAT_MAX_MESSAGES = 40

/** 首页 AI 流式对话超时（与翻译/生成页一致） */
const HOME_CHAT_STREAM_MS =
  Number(import.meta.env.VITE_AI_REQUEST_TIMEOUT_MS) || 600_000

let homeChatSaveDebounceTimer = null
function scheduleDebouncedSaveChatHistory() {
  clearTimeout(homeChatSaveDebounceTimer)
  homeChatSaveDebounceTimer = setTimeout(() => {
    homeChatSaveDebounceTimer = null
    saveChatHistory()
  }, 350)
}

let homeChatScrollRaf = 0
function scheduleHomeChatScroll() {
  if (homeChatScrollRaf) return
  homeChatScrollRaf = requestAnimationFrame(async () => {
    homeChatScrollRaf = 0
    await scrollToBottom()
  })
}

/** 当前首页 AI 流式请求的 AbortController（用户点「停止」或离开页面时中止） */
let homeChatAbortController = null
/** 区分用户主动停止与超时等中止，用于提示文案 */
let homeChatStopWasUser = false

const router = useRouter()
const userStore = useUserStore()

/** 绑定到首页数据的账号 id；切换用户时必须清空 keep-alive 内的状态 */
const homeBoundUserId = ref(null)
const boundAuthEpoch = ref(-1)

/** 当前登录用户在 localStorage 中的隔离标识（无 id 时用 username，避免多人共用 guest） */
function homeUserScope() {
  const u = userStore.user
  if (!u) return null
  if (u.id != null && u.id !== '') return `u${u.id}`
  if (u.email) return `email_${u.email}`
  if (u.username) return `name_${u.username}`
  return null
}

function homeStorageKey(suffix) {
  const scope = homeUserScope()
  if (!scope) return `home_${suffix}_guest`
  return `home_${suffix}_${scope}`
}

const recentNotes = ref([])
const currentNote = ref(null)
const aiMessage = ref('')
const chatHistory = ref([])  // 聊天历史
const isAiThinking = ref(false)  // AI 是否正在思考（首包前显示打字动画）
/** 从发送请求到流结束整段过程，用于禁用发送/快捷操作与显示「停止」 */
const isAiOutputInProgress = ref(false)
const chatMessagesRef = ref(null)  // 聊天消息容器引用
const uploadedNoteContent = ref(null)  // 上传的笔记内容（给AI看，不显示在输入框）
const uploadedNoteName = ref('')  // 上传的笔记文件名
const showNoteSelector = ref(false)  // 是否显示笔记选择器
const allNotes = ref([])  // 所有笔记列表
/** 聊天区未贴底时显示「↓」跳转按钮 */
const showScrollToLatestBtn = ref(false)

// ==================== 视图模式（全部/仅AI/仅笔记）====================
const viewMode = ref('all')  // 'all' | 'chat' | 'note'

function setViewMode(mode) {
  viewMode.value = mode
  // 切换后延迟触发一次重排，确保滚动容器尺寸更新
  setTimeout(() => {
    scrollChatToLatest()
  }, 50)
}

// ==================== 对话历史（持久化到后端）====================
/** 当前激活的对话 id（null 表示尚未绑定到任何对话，发送首条消息时由后端创建） */
const currentConversationId = ref(null)
/** 对话列表（侧边抽屉用），按 updated_at 倒序 */
const conversationList = ref([])
/** 抽屉是否展开 */
const showConversationDrawer = ref(false)
/** 列表加载中 */
const isLoadingConversations = ref(false)

function clearHomeUiState() {
  recentNotes.value = []
  allNotes.value = []
  currentNote.value = null
  chatHistory.value = []
  aiMessage.value = ''
  uploadedNoteContent.value = null
  uploadedNoteName.value = ''
  showNoteSelector.value = false
  isAiThinking.value = false
  isAiOutputInProgress.value = false
  homeChatAbortController?.abort()
  homeChatAbortController = null
  // 清空对话历史相关状态
  currentConversationId.value = null
  conversationList.value = []
  showConversationDrawer.value = false
  isLoadingConversations.value = false
}

// 过滤后的笔记列表（用于搜索）
const filteredNotes = computed(() => {
  return allNotes.value
})

/** 与翻译页一致：富文本 HTML 只消毒；纯 Markdown 再走 marked */
function noteContentToSafeHtml(content) {
  if (!content) return ''
  return isLikelyHtmlContent(content)
    ? sanitizeHtml(content)
    : renderMarkdownToSafeHtml(content)
}

// 渲染当前笔记（HTML 笔记保留表格/图片等 DOM）
const renderedContent = computed(() => {
  if (!currentNote.value?.content) return ''
  return noteContentToSafeHtml(currentNote.value.content)
})

onMounted(async () => {
  await ensureHomeSessionForCurrentUser()
})

onActivated(async () => {
  await ensureHomeSessionForCurrentUser()
})

onBeforeUnmount(() => {
  homeChatStopWasUser = false
  homeChatAbortController?.abort()
  homeChatAbortController = null
})

watch(
  () => [userStore.user?.id, userStore.user?.email, userStore.authSessionEpoch],
  () => {
    void ensureHomeSessionForCurrentUser()
  }
)

/** 切换账号后 keep-alive 仍保留旧状态：按用户 id + 登录世代重置并重新拉取 */
async function ensureHomeSessionForCurrentUser() {
  if (!userStore.isLoggedIn) {
    if (homeBoundUserId.value != null) {
      homeBoundUserId.value = null
      boundAuthEpoch.value = -1
      clearHomeUiState()
    }
    return
  }

  try {
    localStorage.removeItem('home_chat_history')
    localStorage.removeItem('home_current_note')
  } catch {
    /* ignore */
  }

  const uid = userStore.user?.id
  const epoch = userStore.authSessionEpoch

  if (uid == null || uid === undefined) {
    if (homeBoundUserId.value != null) {
      homeBoundUserId.value = null
      boundAuthEpoch.value = -1
      clearHomeUiState()
    }
    return
  }

  const uidNum = Number(uid)
  if (homeBoundUserId.value === uidNum && boundAuthEpoch.value === epoch) {
    return
  }

  homeBoundUserId.value = uidNum
  boundAuthEpoch.value = epoch
  clearHomeUiState()

  await bootstrapHomeData()
}

async function bootstrapHomeData() {
  if (!userStore.isLoggedIn) return

  // 阶段二：优先从后端加载对话历史；保留 localStorage 仅作旧数据兜底
  await loadConversationList()
  if (conversationList.value.length > 0) {
    // 自动选中最近一条对话
    await switchConversation(conversationList.value[0].id)
  } else {
    // 没有历史对话：清空 chatHistory，等待用户首条消息触发后端创建新对话
    chatHistory.value = []
    currentConversationId.value = null
  }

  await loadCurrentNoteFromCache()

  const noteId = router.currentRoute.value.query.noteId

  if (noteId) {
    try {
      ElMessage.success({ message: '加载成功', duration: MESSAGE_DURATION.SHORT })

      const fullNote = await noteApi.getNote(String(noteId))

      currentNote.value = fullNote

      saveCurrentNoteToCache(fullNote)

      await loadRecentNotes()

      updateRecentNotesWithCurrent(fullNote)

      router.replace({ path: '/home' })
    } catch (error) {
      ElMessage.error({ message: '加载笔记失败', duration: MESSAGE_DURATION.SHORT })
    }
  } else {
    await loadRecentNotes()
  }

  await loadAllNotes()

  await nextTick()
  onChatScroll()
}

watch(
  () => chatHistory.value.length,
  async () => {
    await nextTick()
    onChatScroll()
  }
)

watch(isAiThinking, async () => {
  await nextTick()
  onChatScroll()
})

// 监听路由query参数变化（解决从其他页面跳转回来时不刷新的问题）
watch(
  () => router.currentRoute.value.query.noteId,
  async (newNoteId) => {
    if (newNoteId) {
      try {
        // 获取完整的笔记内容
        const fullNote = await noteApi.getNote(String(newNoteId))
        
        // 更新当前笔记
        currentNote.value = fullNote
        
        // 重新加载最近笔记列表
        await loadRecentNotes()
        
        // 将当前查看的笔记移到列表最前面
        updateRecentNotesWithCurrent(fullNote)
        
        // 清除URL中的query参数
        router.replace({ path: '/home' })
        
        ElMessage.success({ message: '加载成功', duration: MESSAGE_DURATION.SHORT })
      } catch (error) {
        console.error('加载笔记失败:', error)
        ElMessage.error({ message: '加载笔记失败', duration: MESSAGE_DURATION.SHORT })
      }
    }
  }
)

async function loadRecentNotes() {
  if (!userStore.isLoggedIn) return
  try {
    // 使用新的 API 获取最近笔记（从 Redis 缓存）
    const notes = await noteApi.getRecentNotes()
    recentNotes.value = notes
  } catch (error) {
    if (!userStore.isLoggedIn) return
    ElMessage.error('加载最近笔记失败')
  }
}

// 加载所有笔记（/note 选择器依赖此列表）
async function loadAllNotes() {
  if (!userStore.isLoggedIn) {
    allNotes.value = []
    return
  }
  try {
    const notes = await noteApi.getNotes()
    allNotes.value = Array.isArray(notes) ? notes : []
  } catch (error) {
    allNotes.value = []
    if (!userStore.isLoggedIn) return
    console.error('加载笔记列表失败（/note 将无选项）:', error)
    ElMessage.error({ message: '加载笔记列表失败，请刷新页面重试', duration: MESSAGE_DURATION.NORMAL })
  }
}

// 更新最近笔记列表，将当前笔记移到最前面
function updateRecentNotesWithCurrent(note) {
  if (!note || !note.id) return
  
  // 移除所有重复的笔记（不只是第一个）
  recentNotes.value = recentNotes.value.filter(n => n.id !== note.id)
  
  // 添加到最前面
  recentNotes.value.unshift(note)
  
  // 保持列表最多20个笔记
  if (recentNotes.value.length > 20) {
    recentNotes.value = recentNotes.value.slice(0, 20)
  }
  
  // 异步同步到后端Redis缓存
  setTimeout(async () => {
    try {
      const noteIds = recentNotes.value.map(n => n.id)
      await noteApi.updateRecentNotesOrder(noteIds)
    } catch (error) {
      console.error('❌ 同步最近笔记顺序失败:', error)
    }
  }, 0)
}

function createNewNote() {
  router.push('/notes/edit')
}

function importNote() {
  // 创建文件输入元素
  const input = document.createElement('input')
  input.type = 'file'
  // 只允许选择支持的格式
  input.accept = '.txt,.md,.docx'
  
  input.onchange = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    
    // 验证文件大小（限制为20MB）
    if (file.size > 20 * 1024 * 1024) {
      ElMessage.error({ message: '文件大小不能超过20MB', duration: MESSAGE_DURATION.SHORT })
      return
    }
    
    try {
      ElMessage.info({ message: '正在读取文件...', duration: MESSAGE_DURATION.SHORT })
      
      let content = ''
      let title = file.name.replace(/\.[^/.]+$/, '') // 去掉扩展名
      
      // 根据文件类型解析
      if (file.name.endsWith('.docx')) {
        // 使用 Mammoth 解析 Word 文件（按需加载，减轻首页首包）
        const arrayBuffer = await file.arrayBuffer()
        const mammoth = (await import('mammoth')).default
        const result = await mammoth.convertToHtml({ arrayBuffer })
        content = result.value
      } else if (file.name.endsWith('.md')) {
        // Markdown 文件直接读取
        content = await file.text()
      } else if (file.name.endsWith('.txt')) {
        // 文本文件直接读取
        content = await file.text()
      } else {
        ElMessage.error({ message: '不支持的文件格式', duration: MESSAGE_DURATION.SHORT })
        return
      }
      
      if (!content.trim()) {
        ElMessage.error({ message: '文件内容为空', duration: MESSAGE_DURATION.SHORT })
        return
      }
      
      // 直接保存到数据库（会自动出现在历史笔记中）
      ElMessage.info({ message: '正在保存笔记...', duration: MESSAGE_DURATION.SHORT })
      
      const savedNote = await noteApi.createNote({
        title: title,
        content: content,
        tags: '导入',
        is_favorite: false  // 导入的笔记默认不加入"我的笔记"
      })
      
      ElMessage.success({ message: `笔记「${savedNote.title}」已导入到历史笔记！`, duration: MESSAGE_DURATION.SHORT })
      
      // 显示在预览窗口
      currentNote.value = savedNote
      
      // 重新加载所有笔记（历史笔记页面会看到）
      loadAllNotes()
      
      // 更新最近笔记列表（实时同步）
      updateRecentNotesWithCurrent(savedNote)
      
    } catch (error) {
      console.error('导入笔记失败:', error)
      
      // 处理重复笔记错误
      if (error.response?.status === 409) {
        await handleDuplicateImport(error, file.name)
      } else {
        ElMessage.error({ message: error.message || '导入失败，请重试', duration: MESSAGE_DURATION.SHORT })
      }
    }
  }
  
  // 触发文件选择
  input.click()
}

// 处理重复导入
async function handleDuplicateImport(error, fileName) {
  const { ElMessageBox } = await import('element-plus')
  
  await ElMessageBox.confirm(
    error.response?.data?.detail || '笔记已存在，是否覆盖？',
    '重复笔记',
    { confirmButtonText: '覆盖', cancelButtonText: '取消', type: 'warning' }
  )
  
  try {
    // 获取已存在的笔记ID并删除
    const existingNotes = await noteApi.getNotes()
    const title = fileName.replace(/\.[^/.]+$/, '')
    const duplicateNote = existingNotes.find(n => n.title === title)
    
    if (duplicateNote) {
      await noteApi.deleteNote(duplicateNote.id)
    }
    
    // 重新导入（这里需要重新解析文件，简化处理：提示用户重新导入）
    ElMessage.info({ message: '请重新导入文件以完成覆盖', duration: MESSAGE_DURATION.NORMAL })
  } catch (err) {
    console.error('覆盖笔记失败:', err)
    ElMessage.error({ message: '覆盖失败，请重试', duration: MESSAGE_DURATION.SHORT })
  }
}

async function viewNote(note) {
  // 完全不等待任何异步操作，立即执行
  // 使用 setTimeout 确保在下一个事件循环执行，避免被其他任务阻塞
  setTimeout(async () => {
    try {
      // 1. 立即更新 currentNote（同步操作）
      currentNote.value = { ...note, loading: true }
      
      // 2. 强制 Vue 更新 DOM
      await nextTick()
      
      // 3. 异步获取完整内容
      const fullNote = await noteApi.getNote(note.id)
      
      // 4. 更新为完整内容
      currentNote.value = fullNote
      
      // 5. 保存到 localStorage 缓存
      saveCurrentNoteToCache(fullNote)
      
      // 6. 再次强制更新 DOM
      await nextTick()
      
      // 7. 显示成功提示
      ElMessage.success({ message: '加载成功', duration: MESSAGE_DURATION.SHORT })
      
      // 8. 异步更新最近笔记列表（不阻塞）
      updateRecentNotesWithCurrent(fullNote)
    } catch (error) {
      ElMessage.error({ message: '加载笔记失败', duration: MESSAGE_DURATION.SHORT })
    }
  }, 0)
}

function editNote(note) {
  router.push(`/notes/edit/${note.id}`)
}

// 加入我的笔记
async function addToMyNotes(note) {
  try {
    await noteApi.updateNote(note.id, { is_favorite: true })
    
    // 更新本地数据
    note.is_favorite = true
    
    // 如果 currentNote 是同一个对象，也需要更新
    if (currentNote.value && currentNote.value.id === note.id) {
      currentNote.value.is_favorite = true
    }
    
    ElMessage.success({ message: '已加入我的笔记', duration: MESSAGE_DURATION.SHORT })
    
    // 重新加载所有笔记
    loadAllNotes()
  } catch (error) {
    console.error('加入我的笔记失败:', error)
    ElMessage.error({ message: '操作失败，请重试', duration: MESSAGE_DURATION.SHORT })
  }
}

function goToHistory() {
  // 跳转到历史笔记页面（显示所有笔记）
  router.push('/notes/history')
}

function selectNote(note) {
  currentNote.value = note
}

function viewAllNotes() {
  router.push('/notes/list')
}

// ==================== AI 助手功能 ====================

// 发送快捷消息
function sendQuickMessage(message) {
  aiMessage.value = message
  sendMessage()
}

function sendMindmapQuickPrompt() {
  sendQuickMessage(AI_MINDMAP_QUICK_PROMPT)
}

/** 从 AI 回复提取可渲染的 Mermaid 源码并跳转思维导图页 */
function openMindmapPreviewFromMessage(markdown) {
  const raw = extractMindmapDiagramSource(markdown)
  const src = prepareMermaidSourceForRender(raw)
  if (!raw) {
    ElMessage.warning({
      message: '未识别到可渲染的 Mermaid 图表（需要 flowchart/graph 等语法或 ```mermaid 代码块）',
      duration: MESSAGE_DURATION.LONG
    })
    return
  }
  setMindmapNavBridgeSource(src)
  try {
    sessionStorage.setItem(MINDMAP_PENDING_SESSION_KEY, src)
    localStorage.setItem(MINDMAP_LOCAL_STORAGE_KEY, src)
  } catch (e) {
    console.error(e)
    ElMessage.error({ message: '无法暂存导图数据，请检查浏览器存储权限', duration: MESSAGE_DURATION.SHORT })
    return
  }
  router.push({ name: 'Mindmap' })
}

function onChatScroll() {
  const el = chatMessagesRef.value
  if (!el) {
    showScrollToLatestBtn.value = false
    return
  }
  const dist = el.scrollHeight - el.scrollTop - el.clientHeight
  showScrollToLatestBtn.value = dist > 48
}

async function scrollChatToLatest() {
  await scrollToBottom()
}

// 上传笔记到 AI 助手
function uploadNoteToAI() {
  // 创建文件输入元素
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.txt,.md,.docx'
  
  input.onchange = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    
    // 验证文件大小（限制为10MB）
    if (file.size > 10 * 1024 * 1024) {
      ElMessage.error({ message: '文件大小不能超过10MB', duration: MESSAGE_DURATION.SHORT })
      return
    }
    
    try {
      ElMessage.info({ message: '正在读取文件...', duration: MESSAGE_DURATION.SHORT })
      
      let content = ''
      
      // 根据文件类型解析
      if (file.name.endsWith('.docx')) {
        // 使用 Mammoth 解析 Word 文件（按需加载）
        const arrayBuffer = await file.arrayBuffer()
        const mammoth = (await import('mammoth')).default
        const result = await mammoth.convertToHtml({ arrayBuffer })
        content = result.value.replace(/<[^>]*>/g, '') // 去掉HTML标签
      } else if (file.name.endsWith('.md')) {
        // Markdown 文件直接读取
        content = await file.text()
      } else if (file.name.endsWith('.txt')) {
        // 文本文件直接读取
        content = await file.text()
      } else {
        ElMessage.error({ message: '不支持的文件格式', duration: MESSAGE_DURATION.SHORT })
        return
      }
      
      if (!content.trim()) {
        ElMessage.error({ message: '文件内容为空', duration: MESSAGE_DURATION.SHORT })
        return
      }
      
      // 存储上传的笔记内容（不显示在输入框）
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
  
  // 触发文件选择
  input.click()
}

// 清除上传的笔记
function clearUploadedNote() {
  uploadedNoteContent.value = null
  uploadedNoteName.value = ''
  ElMessage.success({ message: '已清除上传的笔记', duration: MESSAGE_DURATION.SHORT })
}

// 发送消息（完全异步，不阻塞UI）
function stopAiChatOutput() {
  if (!isAiOutputInProgress.value) return
  homeChatStopWasUser = true
  homeChatAbortController?.abort()
}

function sendMessage() {
  if (!aiMessage.value.trim() || isAiOutputInProgress.value) return
  
  const userMessage = aiMessage.value.trim()
  aiMessage.value = ''

  const hasNoteContext =
    uploadedNoteContent.value && shouldAttachNoteContext(uploadedNoteContent.value)

  // 添加用户消息到聊天历史（附带本条是否绑定了笔记上下文，用于气泡下展示）
  chatHistory.value.push({
    role: 'user',
    content: userMessage,
    timestamp: new Date(),
    contextNoteTitle: hasNoteContext ? (uploadedNoteName.value || '笔记') : undefined
  })
  saveChatHistory()

  // 立即滚动到底部（不等待）
  scrollToBottom()
  
  // 显示 AI 思考状态
  isAiThinking.value = true
  isAiOutputInProgress.value = true
  
  // 在后台异步执行 AI 请求，完全不阻塞其他操作
  // 不使用 await，让它在后台独立运行
  ;(async () => {
    const streamAbort = new AbortController()
    homeChatAbortController = streamAbort
    const timeoutId = setTimeout(() => streamAbort.abort(), HOME_CHAT_STREAM_MS)
    let assistantIdx = -1

    try {
      // 构建消息历史：过滤掉空内容消息（如仅有 thinking/toolCalls 的中间步骤）
      let messages = chatHistory.value.slice(0, -1).slice(-10)
        .filter(msg => msg.content && String(msg.content).trim())
        .map(msg => ({
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

      // 创建 assistant 消息占位（在首个事件到来时延迟显示，避免空消息）
      const ensureAssistantMsg = () => {
        if (assistantIdx < 0) {
          chatHistory.value.push({
            role: 'assistant',
            content: '',
            thinking: '',
            thinkingCollapsed: true,
            hasDelta: false,
            toolCalls: [],
            agents: [],
            currentAgent: null,
            timestamp: new Date()
          })
          assistantIdx = chatHistory.value.length - 1
          isAiThinking.value = false
        }
        return chatHistory.value[assistantIdx]
      }

      await aiApi.agentChatStream({
        message: messageForApi,
        history: messages,
        conversationId: currentConversationId.value ?? undefined,
        signal: streamAbort.signal,
        onEvent: (evt) => {
          if (!evt || typeof evt !== 'object') return
          switch (evt.type) {
            case 'agent_start': {
              const ag = {
                name: evt.agent,
                display_name: evt.display_name || evt.agent,
                emoji: evt.emoji || '🤖',
                reason: evt.reason || '',
                status: 'running'
              }
              const msg = ensureAssistantMsg()
              msg.agents = msg.agents || []
              msg.agents.push(ag)
              msg.currentAgent = evt.agent
              break
            }
            case 'agent_end': {
              const msg = ensureAssistantMsg()
              msg.agents = msg.agents || []
              const idx = msg.agents.findIndex(a => a.name === evt.agent)
              if (idx >= 0) {
                msg.agents[idx].status = evt.success === false ? 'error' : 'done'
              }
              msg.currentAgent = null
              break
            }
            case 'sub_agent_start': {
              const msg = ensureAssistantMsg()
              msg.subAgents = msg.subAgents || []
              msg.subAgents.push({
                name: evt.agent,
                display_name: evt.display_name || evt.agent,
                emoji: evt.emoji || '',
                tool: evt.tool || '',
                status: 'running'
              })
              msg.currentSubAgent = evt.agent
              break
            }
            case 'sub_agent_end': {
              const msg = ensureAssistantMsg()
              msg.subAgents = msg.subAgents || []
              const idx = msg.subAgents.findIndex(a => a.name === evt.agent)
              if (idx >= 0) {
                msg.subAgents[idx].status = 'done'
              }
              msg.currentSubAgent = null
              break
            }
            case 'thinking': {
              const msg = ensureAssistantMsg()
              const cur = String(msg.thinking || '')
              msg.thinking = cur + (cur ? '\n' : '') + (evt.text || '')
              break
            }
            case 'tool_start': {
              const msg = ensureAssistantMsg()
              msg.toolCalls = msg.toolCalls || []
              msg.toolCalls.push({
                id: evt.id,
                name: evt.name,
                args: evt.args || {},
                status: 'running',
                result: null
              })
              break
            }
            case 'tool_end': {
              const msg = ensureAssistantMsg()
              msg.toolCalls = msg.toolCalls || []
              const idx = msg.toolCalls.findIndex(c => c.id === evt.id)
              if (idx >= 0) {
                msg.toolCalls[idx].status = 'done'
                msg.toolCalls[idx].result = evt.result || null
              } else {
                msg.toolCalls.push({
                  id: evt.id,
                  name: evt.name,
                  args: {},
                  status: 'done',
                  result: evt.result || null
                })
              }
              // AI保存笔记成功后，弹提示并提供跳转链接
              if (evt.name === 'create_note' && evt.result?.id) {
                setTimeout(() => {
                  loadRecentNotes()
                  loadAllNotes()
                }, 300)
                ElMessage.success({
                  message: '已保存到我的笔记，点击查看',
                  type: 'success',
                  duration: MESSAGE_DURATION.LONG,
                  onClick: () => {
                    router.push('/notes')
                  }
                })
              } else if (evt.name === 'create_note' && evt.result?.error) {
                ElMessage.error({
                  message: `保存失败：${evt.result.error}`,
                  duration: MESSAGE_DURATION.LONG
                })
              }
              break
            }
            case 'delta': {
              const msg = ensureAssistantMsg()
              msg.content = String(msg.content || '') + (evt.text || '')
              break
            }
            case 'done': {
              // 接收后端返回的 conversation_id（首次发送时后端自动创建并返回）
              if (evt.conversation_id != null) {
                currentConversationId.value = evt.conversation_id
              }
              break
            }
            case 'error': {
              const msg = ensureAssistantMsg()
              const errMsg = evt.message || 'AI 服务暂时不可用，请稍后重试'
              if (!String(msg.content || '').trim()) {
                msg.content = errMsg
              } else {
                msg.content = String(msg.content) + '\n\n> ⚠️ ' + errMsg
              }
              // 错误时也隐藏打字指示器
              if (!msg.hasDelta) {
                msg.hasDelta = true
                isAiThinking.value = false
              }
              break
            }
          }
          scheduleHomeChatScroll()
          scheduleDebouncedSaveChatHistory()
        }
      })

      if (assistantIdx < 0) {
        chatHistory.value.push({
          role: 'assistant',
          content: '抱歉，我暂时无法回答这个问题。',
          thinking: '',
          thinkingCollapsed: true,
          toolCalls: [],
          agents: [],
          currentAgent: null,
          timestamp: new Date()
        })
        isAiThinking.value = false
      } else {
        const c = String(chatHistory.value[assistantIdx].content || '').trim()
        if (!c) {
          // 检查是否有思考或工具调用：有则保留，无则给兜底
          const hasThinking = String(chatHistory.value[assistantIdx].thinking || '').trim()
          const hasTools = (chatHistory.value[assistantIdx].toolCalls || []).length > 0
          if (!hasThinking && !hasTools) {
            chatHistory.value[assistantIdx].content = '抱歉，我暂时无法回答这个问题。'
          } else {
            chatHistory.value[assistantIdx].content = '已完成上述操作。'
          }
        }
      }

    } catch (error) {
      console.error('AI 回复失败:', error)
      const aborted = error?.name === 'AbortError' || streamAbort.signal.aborted
      let fallback =
        '抱歉，服务暂时不可用，请稍后重试。'

      if (!aborted) {
        const d = error?.response?.data?.detail
        const msg = Array.isArray(d)
          ? d.map((x) => x.msg || JSON.stringify(x)).join('；')
          : d || error?.message
        const s = String(msg || '')
        if (s.includes('503') || /密钥|ENCRYPTION|crypto/i.test(s)) {
          fallback = '模型或密钥不可用，请到个人中心检查 LLM / API Key 配置'
        } else if (typeof msg === 'string' && msg.trim()) {
          fallback = msg.trim()
        }
        ElMessage.error({
          message: 'AI 服务暂时不可用，请稍后重试',
          duration: MESSAGE_DURATION.SHORT
        })
      } else if (homeChatStopWasUser) {
        if (assistantIdx >= 0 && String(chatHistory.value[assistantIdx].content || '').trim()) {
          ElMessage.info({
            message: '已停止生成',
            duration: MESSAGE_DURATION.SHORT
          })
        } else {
          ElMessage.info({
            message: '已停止',
            duration: MESSAGE_DURATION.SHORT
          })
        }
      } else if (assistantIdx >= 0 && String(chatHistory.value[assistantIdx].content || '').trim()) {
        ElMessage.warning({
          message: '回复已中断（可能为超时）',
          duration: MESSAGE_DURATION.SHORT
        })
      } else if (assistantIdx < 0) {
        ElMessage.info({
          message: '已取消或超时',
          duration: MESSAGE_DURATION.SHORT
        })
      }

      if (!aborted) {
        if (assistantIdx >= 0) {
          if (!String(chatHistory.value[assistantIdx].content || '').trim()) {
            chatHistory.value[assistantIdx].content = fallback
          }
        } else {
          chatHistory.value.push({
            role: 'assistant',
            content: fallback,
            thinking: '',
            toolCalls: [],
            agents: [],
            currentAgent: null,
            timestamp: new Date()
          })
        }
      } else if (homeChatStopWasUser) {
        if (assistantIdx >= 0) {
          if (!String(chatHistory.value[assistantIdx].content || '').trim()) {
            chatHistory.value[assistantIdx].content = '（已停止生成）'
          }
        } else {
          chatHistory.value.push({
            role: 'assistant',
            content: '（已停止生成）',
            thinking: '',
            thinkingCollapsed: true,
            toolCalls: [],
            agents: [],
            currentAgent: null,
            timestamp: new Date()
          })
        }
      } else {
        if (assistantIdx >= 0) {
          if (!String(chatHistory.value[assistantIdx].content || '').trim()) {
            chatHistory.value[assistantIdx].content = fallback
          }
        } else {
          chatHistory.value.push({
            role: 'assistant',
            content: fallback,
            thinking: '',
            thinkingCollapsed: true,
            toolCalls: [],
            agents: [],
            currentAgent: null,
            timestamp: new Date()
          })
        }
      }
    } finally {
      clearTimeout(timeoutId)
      clearTimeout(homeChatSaveDebounceTimer)
      homeChatSaveDebounceTimer = null
      isAiThinking.value = false
      isAiOutputInProgress.value = false
      homeChatAbortController = null
      homeChatStopWasUser = false
      saveChatHistory()
      await scrollToBottom()
      // 阶段二：刷新对话列表（让最新更新的对话排到最前）
      void loadConversationList()
    }
  })()
  
  // 立即返回，不等待任何操作完成
}

// 渲染消息内容（HTML / Markdown 与预览区一致）
function renderMessage(content) {
  return noteContentToSafeHtml(content)
}

// 格式化时间
function formatTime(timestamp) {
  const date = new Date(timestamp)
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  return `${hours}:${minutes}`
}

// 滚动到聊天底部
async function scrollToBottom() {
  await nextTick()
  if (chatMessagesRef.value) {
    chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
  }
  await nextTick()
  onChatScroll()
}

// 处理输入事件，检测 /note 命令
function handleInput(value) {
  
  // 检测是否包含 /note
  if (value.includes('/note')) {
    showNoteSelector.value = true
  } else {
    showNoteSelector.value = false
  }
}

// 关闭笔记选择器
function closeNoteSelector() {
  showNoteSelector.value = false
  // 移除输入框中的 /note
  if (aiMessage.value.endsWith('/note')) {
    aiMessage.value = aiMessage.value.slice(0, -5)
  }
}

// 统一解析 GET /note/:id 的返回（axios 已解一层 data，兼容若将来包一层 data）
function unwrapNoteResponse(res) {
  if (!res || typeof res !== 'object') return null
  if ('content' in res || 'title' in res || 'id' in res) return res
  if (res.data && typeof res.data === 'object') return res.data
  return res
}

// 选择笔记作为上下文
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

// ==================== 持久化缓存功能 ====================

// 保存当前笔记到 localStorage
function saveCurrentNoteToCache(note) {
  if (!note || !note.id) return
  
  try {
    const cacheData = {
      id: note.id,
      title: note.title,
      content: note.content,
      tags: note.tags,
      is_favorite: note.is_favorite,
      created_at: note.created_at,
      updated_at: note.updated_at,
      timestamp: Date.now()  // 记录缓存时间
    }
    localStorage.setItem(homeStorageKey('current_note'), JSON.stringify(cacheData))
  } catch (error) {
    console.error('保存笔记缓存失败:', error)
  }
}

// 从 localStorage 加载当前笔记
async function loadCurrentNoteFromCache() {
  try {
    const cached = localStorage.getItem(homeStorageKey('current_note'))
    if (!cached) return
    
    const cacheData = JSON.parse(cached)
    
    // 检查缓存是否过期（24小时）
    const now = Date.now()
    const cacheAge = now - cacheData.timestamp
    const maxAge = 24 * 60 * 60 * 1000  // 24小时
    
    if (cacheAge > maxAge) {
      // 缓存过期，清除
      localStorage.removeItem(homeStorageKey('current_note'))
      return
    }
    
    // 使用缓存的笔记
    currentNote.value = cacheData
  } catch (error) {
    console.error('加载笔记缓存失败:', error)
    localStorage.removeItem(homeStorageKey('current_note'))
  }
}

// 保存聊天历史到 localStorage（按用户隔离，带归属校验）
function saveChatHistory() {
  if (!homeUserScope()) return
  try {
    if (chatHistory.value.length > HOME_CHAT_MAX_MESSAGES) {
      chatHistory.value = chatHistory.value.slice(-HOME_CHAT_MAX_MESSAGES)
    }
    const payload = {
      v: 1,
      ownerId: userStore.user?.id ?? null,
      ownerEmail: userStore.user?.email ?? '',
      ownerUsername: userStore.user?.username ?? '',
      messages: chatHistory.value
    }
    localStorage.setItem(homeStorageKey('chat_history'), JSON.stringify(payload))
  } catch (error) {
    console.error('保存聊天历史失败:', error)
  }
}

function chatHistoryBelongsToCurrentUser(parsed) {
  const u = userStore.user
  if (!u) return false
  if (parsed.ownerId != null && u.id != null && Number(parsed.ownerId) !== Number(u.id)) {
    return false
  }
  if (parsed.ownerEmail && u.email && parsed.ownerEmail !== u.email) {
    return false
  }
  if (parsed.ownerUsername && u.username && parsed.ownerUsername !== u.username) {
    return false
  }
  return true
}

// 从 localStorage 加载聊天历史（仅恢复当前用户的记录）
function loadChatHistory() {
  if (!homeUserScope()) return
  try {
    const cached = localStorage.getItem(homeStorageKey('chat_history'))
    if (!cached) return

    const parsed = JSON.parse(cached)
    let history

    if (Array.isArray(parsed)) {
      history = parsed
    } else if (parsed?.v === 1 && Array.isArray(parsed.messages)) {
      if (!chatHistoryBelongsToCurrentUser(parsed)) {
        localStorage.removeItem(homeStorageKey('chat_history'))
        return
      }
      history = parsed.messages
    } else {
      localStorage.removeItem(homeStorageKey('chat_history'))
      return
    }

    chatHistory.value = history.map((msg) => ({
      ...msg,
      thinking: msg.thinking || '',
      thinkingCollapsed: msg.thinkingCollapsed !== undefined ? msg.thinkingCollapsed : true,
      toolCalls: Array.isArray(msg.toolCalls) ? msg.toolCalls : [],
      agents: Array.isArray(msg.agents) ? msg.agents : [],
      currentAgent: msg.currentAgent || null,
      timestamp: new Date(msg.timestamp)
    }))
    saveChatHistory()

    setTimeout(() => scrollToBottom(), 100)
  } catch (error) {
    console.error('加载聊天历史失败:', error)
    localStorage.removeItem(homeStorageKey('chat_history'))
  }
}

async function confirmClearChat() {
  try {
    await ElMessageBox.confirm('确定清空当前对话？清空后无法恢复。', '清空对话', {
      type: 'warning',
      confirmButtonText: '清空',
      cancelButtonText: '取消'
    })
  } catch {
    return
  }
  // 如果当前对话存在，从后端删除；本地状态也清空
  const cid = currentConversationId.value
  if (cid != null) {
    try {
      await aiApi.deleteConversation(cid)
    } catch (error) {
      console.error('删除对话失败:', error)
      ElMessage.error({ message: '删除对话失败', duration: MESSAGE_DURATION.SHORT })
      return
    }
  }
  chatHistory.value = []
  currentConversationId.value = null
  try {
    localStorage.removeItem(homeStorageKey('chat_history'))
  } catch {
    /* ignore */
  }
  ElMessage.success({ message: '已清空对话', duration: MESSAGE_DURATION.SHORT })
  await loadConversationList()
  await nextTick()
  onChatScroll()
}

// ==================== 对话历史管理（持久化）====================
/** 加载当前用户的对话列表 */
async function loadConversationList() {
  if (!userStore.isLoggedIn) {
    conversationList.value = []
    return
  }
  isLoadingConversations.value = true
  try {
    const list = await aiApi.listConversations()
    conversationList.value = Array.isArray(list) ? list : []
  } catch (error) {
    console.error('加载对话列表失败:', error)
    conversationList.value = []
  } finally {
    isLoadingConversations.value = false
  }
}

/** 切换到指定对话，加载其消息 */
async function switchConversation(conversationId) {
  if (conversationId == null) return
  try {
    const detail = await aiApi.getConversation(conversationId)
    if (!detail) return
    currentConversationId.value = detail.id
    chatHistory.value = (detail.messages || []).map((m) => ({
        role: m.role,
        content: m.content || '',
        thinking: '',
        thinkingCollapsed: true,
        toolCalls: [],
        agents: [],
        currentAgent: null,
        timestamp: m.created_at ? new Date(m.created_at) : new Date()
      }))
    showConversationDrawer.value = false
    ElMessage.success({
      message: `已切换到「${detail.title}」`,
      duration: MESSAGE_DURATION.SHORT
    })
    await nextTick()
    onChatScroll()
    await scrollToBottom()
  } catch (error) {
    console.error('切换对话失败:', error)
    ElMessage.error({ message: '加载对话失败', duration: MESSAGE_DURATION.SHORT })
  }
}

/** 新建空对话（前端只清空当前状态，等用户发首条消息时由后端创建并返回 conversation_id） */
async function createNewConversation() {
  chatHistory.value = []
  currentConversationId.value = null
  showConversationDrawer.value = false
  try {
    localStorage.removeItem(homeStorageKey('chat_history'))
  } catch {
    /* ignore */
  }
  await nextTick()
  onChatScroll()
  ElMessage.success({ message: '已开启新对话', duration: MESSAGE_DURATION.SHORT })
}

/** 删除指定对话 */
async function deleteConversationById(conversationId) {
  if (conversationId == null) return
  try {
    await ElMessageBox.confirm('确定删除此对话？所有消息将一并删除。', '删除对话', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    })
  } catch {
    return
  }
  try {
    await aiApi.deleteConversation(conversationId)
    ElMessage.success({ message: '已删除', duration: MESSAGE_DURATION.SHORT })
    // 如果删除的是当前对话，清空当前状态
    if (currentConversationId.value === conversationId) {
      chatHistory.value = []
      currentConversationId.value = null
    }
    await loadConversationList()
    // 删除后若没有当前对话，自动选中第一条
    if (currentConversationId.value == null && conversationList.value.length > 0) {
      await switchConversation(conversationList.value[0].id)
    }
  } catch (error) {
    console.error('删除对话失败:', error)
    ElMessage.error({ message: '删除失败', duration: MESSAGE_DURATION.SHORT })
  }
}

/** 重命名对话标题 */
async function renameConversationById(conversationId) {
  if (conversationId == null) return
  const conv = conversationList.value.find((c) => c.id === conversationId)
  if (!conv) return
  let newTitle = ''
  try {
    const { value } = await ElMessageBox.prompt('请输入新标题', '重命名对话', {
      confirmButtonText: '保存',
      cancelButtonText: '取消',
      inputValue: conv.title || '',
      inputPattern: /\S+/,
      inputErrorMessage: '标题不能为空'
    })
    newTitle = (value || '').trim()
  } catch {
    return
  }
  if (!newTitle) return
  try {
    await aiApi.renameConversation(conversationId, newTitle)
    ElMessage.success({ message: '已重命名', duration: MESSAGE_DURATION.SHORT })
    await loadConversationList()
  } catch (error) {
    console.error('重命名失败:', error)
    ElMessage.error({ message: '重命名失败', duration: MESSAGE_DURATION.SHORT })
  }
}

/** 切换抽屉显示 */
function toggleConversationDrawer() {
  showConversationDrawer.value = !showConversationDrawer.value
  if (showConversationDrawer.value) {
    void loadConversationList()
  }
}

/** 格式化对话列表的时间显示 */
function formatConversationTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  const now = new Date()
  const diff = now - d
  const oneDay = 24 * 60 * 60 * 1000
  if (diff < oneDay && d.getDate() === now.getDate()) {
    return `今天 ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
  }
  if (diff < 2 * oneDay) return '昨天'
  if (diff < 7 * oneDay) return `${Math.floor(diff / oneDay)}天前`
  return `${d.getMonth() + 1}月${d.getDate()}日`
}

// 获取笔记预览文本
function getNotePreview(content) {
  if (!content) return ''
  // 去掉HTML标签和Markdown标记
  const text = content
    .replace(/<[^>]*>/g, '')
    .replace(/#{1,6}\s/g, '')
    .replace(/\*\*(.+?)\*\*/g, '$1')
    .replace(/\*(.+?)\*/g, '$1')
    .replace(/`(.+?)`/g, '$1')
    .substring(0, 80)
  return text + (content.length > 80 ? '...' : '')
}
  return {
    HOME_CHAT_MAX_MESSAGES,
    recentNotes,
    currentNote,
    aiMessage,
    chatHistory,
    isAiThinking,
    isAiOutputInProgress,
    chatMessagesRef,
    uploadedNoteContent,
    uploadedNoteName,
    showNoteSelector,
    allNotes,
    filteredNotes,
    showScrollToLatestBtn,
    renderedContent,
    // 对话历史持久化
    currentConversationId,
    conversationList,
    showConversationDrawer,
    isLoadingConversations,
    loadConversationList,
    switchConversation,
    createNewConversation,
    deleteConversationById,
    renameConversationById,
    toggleConversationDrawer,
    formatConversationTime,
    // 笔记/AI 操作
    createNewNote,
    importNote,
    viewNote,
    editNote,
    addToMyNotes,
    goToHistory,
    sendQuickMessage,
    sendMindmapQuickPrompt,
    openMindmapPreviewFromMessage,
    onChatScroll,
    scrollChatToLatest,
    uploadNoteToAI,
    clearUploadedNote,
    stopAiChatOutput,
    sendMessage,
    renderMessage,
    formatTime,
    handleInput,
    closeNoteSelector,
    selectNoteForContext,
    confirmClearChat,
    extractMindmapDiagramSource,
    // 视图模式
    viewMode,
    setViewMode,
  }
}
