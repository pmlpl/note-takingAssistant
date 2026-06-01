<template>
  <Layout>
    <div class="home-container">
      <el-container class="main-layout">
        <!-- 左侧：笔记管理 -->
        <el-aside width="240px" class="left-sidebar">
          <div class="sidebar-header">
            <h3><IconNotebook :size="32" color="#409eff" />笔记管理</h3>
          </div>
          <div class="sidebar-actions">
            <el-button type="primary" @click="createNewNote" class="action-btn">
              <IconPlus :size="18" />
              新建笔记
            </el-button>
            <el-button @click="importNote" class="action-btn">
              <IconUpload :size="18" />
              导入笔记
            </el-button>
          </div>
          <div class="notes-list">
            <div class="list-title">最近笔记</div>
            <!-- 显示所有最近笔记 -->
            <div v-for="note in recentNotes" :key="note.id" class="note-item" @click="viewNote(note)">
              <IconDocument :size="16" color="#909399" />
              <span class="note-title">{{ note.title }}</span>
            </div>
            <!-- 如果超过10个，显示省略号并跳转到历史笔记页面 -->
            <div v-if="recentNotes.length > 10" class="more-notes" @click="goToHistory">
              <span class="more-text">... 更多 ({{ recentNotes.length - 10 }})</span>
            </div>
            <div v-if="recentNotes.length === 0" class="empty-notes">
              <p>暂无笔记</p>
            </div>
          </div>
        </el-aside>

        <!-- 中间：笔记预览区 -->
        <el-main class="center-preview">
          <div v-if="currentNote" class="preview-content">
            <div class="preview-header">
              <h2>{{ currentNote.title }}</h2>
              <div class="preview-actions">
                <el-button 
                  v-if="!currentNote.is_favorite" 
                  size="small" 
                  type="success"
                  @click="addToMyNotes(currentNote)"
                >
                  加入我的笔记
                </el-button>
                <el-button size="small" @click="editNote(currentNote)">
                  <IconEdit :size="16" />
                  编辑
                </el-button>
              </div>
            </div>
            <div class="preview-body" v-html="renderedContent"></div>
          </div>
          <div v-else class="empty-preview">
            <IconDocument :size="80" color="#d9d9d9" />
            <h3>选择一个笔记开始预览</h3>
            <p>从左侧选择笔记，或创建新笔记</p>
          </div>
        </el-main>

        <!-- 右侧：AI 助手 -->
        <el-aside width="480px" class="right-ai-panel">
          <div class="ai-header">
            <div class="ai-header-main">
              <h3><IconAI :size="24"/>AI 助手</h3>
              <p>智能问答与辅助 · 本地最多保留 {{ HOME_CHAT_MAX_MESSAGES }} 条，超出自动丢弃最早消息</p>
            </div>
            <el-button
              v-if="chatHistory.length > 0"
              type="danger"
              link
              size="small"
              class="ai-header-clear"
              @click="confirmClearChat"
            >
              清空对话
            </el-button>
          </div>
          
          <div class="ai-chat-area">
            <div class="chat-messages-stack">
              <!-- 聊天记录区域 -->
              <div class="chat-messages" ref="chatMessagesRef" @scroll.passive="onChatScroll">
              <div v-if="chatHistory.length === 0" class="welcome-message">
                <div class="welcome-icon">👋</div>
                <h4>您好！我是您的 AI 笔记助手</h4>
                <p>我可以帮您：</p>
                <ul>
                  <li>💡 解答学习问题</li>
                  <li>📝 优化笔记内容</li>
                  <li>🎯 提供学习建议</li>
                  <li>📚 解释复杂概念</li>
                </ul>
              </div>
              
              <!-- 聊天消息列表 -->
              <div v-for="(message, index) in chatHistory" :key="index" 
                   :class="['message-item', message.role]">
                <div class="message-avatar">
                  <IconAI v-if="message.role === 'assistant'" :size="20" color="#409eff" />
                  <span v-else class="user-avatar">👤</span>
                </div>
                <div class="message-content">
                  <div class="message-text" v-html="renderMessage(message.content)"></div>
                  <div
                    v-if="message.role === 'assistant' && extractMindmapDiagramSource(message.content)"
                    class="message-mindmap-actions"
                  >
                    <el-button
                      type="primary"
                      size="small"
                      @click="openMindmapPreviewFromMessage(message.content)"
                    >
                      在思维导图页预览
                    </el-button>
                  </div>
                  <div
                    v-if="message.role === 'user' && message.contextNoteTitle"
                    class="message-context-note"
                  >
                    {{ message.contextNoteTitle }}
                  </div>
                  <div class="message-time">{{ formatTime(message.timestamp) }}</div>
                </div>
              </div>
              
              <!-- 加载中提示 -->
              <div v-if="isAiThinking" class="message-item assistant">
                <div class="message-avatar">
                  <IconAI :size="20" color="#409eff" />
                </div>
                <div class="message-content">
                  <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            </div>

              <el-button
                v-show="(chatHistory.length > 0 || isAiThinking) && showScrollToLatestBtn"
                class="chat-scroll-float-btn"
                circle
                type="primary"
                title="跳转最新消息"
                @click="scrollChatToLatest"
              >
                <el-icon :size="20" class="chat-scroll-float-btn__icon"><ArrowDown /></el-icon>
              </el-button>
            </div>

            <!-- 输入框区域 -->
            <div class="input-section">
              <!-- 笔记选择下拉框（显示在已上传笔记的位置） -->
              <div v-if="showNoteSelector" class="note-selector-dropdown">
                <div class="selector-header">
                  <span>选择笔记作为上下文 ({{ filteredNotes.length }}个笔记)</span>
                  <el-button size="small" link @click="closeNoteSelector">取消</el-button>
                </div>
                <div class="note-list-container">
                  <div 
                    v-for="note in filteredNotes" 
                    :key="note.id" 
                    class="note-option"
                    @click="selectNoteForContext(note)"
                  >
                    <IconDocument :size="16" color="#409eff" />
                    <div class="note-info">
                      <div class="note-title">{{ note.title }}</div>
                    </div>
                  </div>
                  <div v-if="filteredNotes.length === 0" class="empty-note-list">
                    <p>暂无笔记</p>
                  </div>
                </div>
              </div>
              
              <!-- 已上传笔记提示 -->
              <div v-else-if="uploadedNoteContent" class="uploaded-note-banner">
                <IconDocument :size="16" color="#409eff" />
                <span class="note-name">{{ uploadedNoteName }}</span>
                <el-button 
                  size="small" 
                  link 
                  type="danger"
                  @click="clearUploadedNote"
                >
                  清除
                </el-button>
              </div>
              
              <!-- 快捷操作按钮 -->
              <div class="quick-actions">
                <el-button
                  size="small"
                  :disabled="isAiOutputInProgress"
                  @click="sendMindmapQuickPrompt"
                >
                  思维导图
                </el-button>
                <el-button
                  size="small"
                  :disabled="isAiOutputInProgress"
                  @click="sendQuickMessage('给我一些学习建议')"
                >
                  学习建议
                </el-button>
                <el-button
                  size="small"
                  :disabled="isAiOutputInProgress"
                  @click="sendQuickMessage('解释一下这个概念')"
                >
                  概念解释
                </el-button>
              </div>

              <!-- 输入框 -->
              <div class="input-wrapper">
                <div class="input-container">
                  <el-input
                    v-model="aiMessage"
                    type="textarea"
                    :rows="3"
                    placeholder="输入您的问题...（输入 /note 可选择笔记）"
                    @keydown.enter.prevent="sendMessage"
                    @input="handleInput"
                    resize="none"
                    class="ai-input"
                  />
                  <!-- 上传笔记按钮 -->
                  <el-button 
                    class="upload-note-btn"
                    size="small"
                    circle
                    @click="uploadNoteToAI"
                    title="上传笔记"
                  >
                    <IconPlus :size="16" />
                  </el-button>
                </div>
                <el-button
                  v-if="isAiOutputInProgress"
                  type="danger"
                  plain
                  class="stop-ai-btn"
                  @click="stopAiChatOutput"
                >
                  停止
                </el-button>
                <el-button
                  type="primary"
                  @click="sendMessage"
                  :disabled="!aiMessage.trim() || isAiOutputInProgress"
                  :loading="isAiOutputInProgress"
                  class="send-btn"
                  circle
                >
                  <IconEdit :size="18" />
                </el-button>
              </div>
            </div>
          </div>
        </el-aside>
      </el-container>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted, onActivated, onBeforeUnmount, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store'
import Layout from '@/components/Layout.vue'
import {IconPlus, IconUpload, IconDocument, IconEdit, IconAI, IconNotebook} from '@/components/icons'
import { noteApi } from '@/api/note'
import { aiApi } from '@/api/ai'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
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

defineOptions({
  name: 'Home'
})

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
  () => [userStore.user?.id, userStore.user?.username, userStore.authSessionEpoch],
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

  loadChatHistory()
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
      // 构建消息历史
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

      await aiApi.chatStream({
        message: messageForApi,
        history: messages,
        signal: streamAbort.signal,
        onChunk: (acc) => {
          if (assistantIdx < 0) {
            chatHistory.value.push({
              role: 'assistant',
              content: acc,
              timestamp: new Date()
            })
            assistantIdx = chatHistory.value.length - 1
            isAiThinking.value = false
          } else {
            chatHistory.value[assistantIdx].content = acc
          }
          scheduleHomeChatScroll()
          scheduleDebouncedSaveChatHistory()
        }
      })

      if (assistantIdx < 0) {
        chatHistory.value.push({
          role: 'assistant',
          content: '抱歉，我暂时无法回答这个问题。',
          timestamp: new Date()
        })
        isAiThinking.value = false
      } else {
        const c = String(chatHistory.value[assistantIdx].content || '').trim()
        if (!c) {
          chatHistory.value[assistantIdx].content =
            '抱歉，我暂时无法回答这个问题。'
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
  chatHistory.value = []
  try {
    localStorage.removeItem(homeStorageKey('chat_history'))
  } catch {
    /* ignore */
  }
  ElMessage.success({ message: '已清空对话', duration: MESSAGE_DURATION.SHORT })
  await nextTick()
  onChatScroll()
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
</script>

<style scoped>
/* ═══ Home — Hand-Drawn Theme ═══ */

.home-container {
  height: calc(100vh - 60px);
  overflow: hidden;
}

.main-layout {
  height: 100%;
  background: var(--color-paper);
  background-image: radial-gradient(var(--color-muted) 1px, transparent 1px);
  background-size: 24px 24px;
}

/* ── Left Sidebar ── */
.left-sidebar {
  background: #ffffff;
  border-right: 3px dashed var(--color-pencil);
  display: flex;
  flex-direction: column;
  padding: 20px;
}

.sidebar-header h3 {
  font-family: var(--font-heading);
  font-size: 18px;
  color: var(--color-pencil);
  margin: 0 0 20px;
  font-weight: 700;
}

.sidebar-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}

.action-btn {
  width: 100%;
  justify-content: center;
  margin-left: 0 !important;
}

.notes-list {
  flex: 1;
  overflow-y: auto;
}

.list-title {
  font-family: var(--font-body);
  font-size: 14px;
  color: #999;
  margin-bottom: 12px;
  font-weight: 600;
}

.note-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px;
  border-radius: var(--radius-wobbly-sm);
  cursor: pointer;
  transition: all 0.15s ease;
  margin-bottom: 4px;
}

.note-item:hover {
  background: var(--color-yellow);
  transform: rotate(-0.5deg);
}

.note-title {
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-pencil);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.more-notes {
  padding: 10px;
  text-align: center;
  cursor: pointer;
  border-radius: var(--radius-wobbly-sm);
  margin-top: 4px;
}

.more-notes:hover {
  background: var(--color-muted);
}

.more-text {
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-blue);
  font-weight: 600;
}

.empty-notes {
  text-align: center;
  padding: 40px 20px;
  color: #999;
}

.empty-notes p {
  margin: 0;
  font-size: 14px;
}

/* ── Center Preview ── */
.center-preview {
  background: #ffffff;
  padding: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.preview-content {
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 30px 30px 20px;
  border-bottom: 3px dashed var(--color-pencil);
  background: #fff;
  flex-shrink: 0;
  position: sticky;
  top: 0;
  z-index: 10;
}

.preview-header h2 {
  font-family: var(--font-heading);
  font-size: 24px;
  color: var(--color-pencil);
  margin: 0;
  font-weight: 700;
}

.preview-body {
  flex: 1;
  overflow-y: auto;
  overflow-x: auto;
  padding: 0 30px 30px;
  line-height: 1.8;
  color: var(--color-pencil);
  font-size: 15px;
  min-height: 0;
}

.preview-body :deep(h1),
.preview-body :deep(h2),
.preview-body :deep(h3) {
  font-family: var(--font-heading);
  margin-top: 24px;
  margin-bottom: 12px;
  color: var(--color-pencil);
}

.preview-body :deep(p)    { margin: 12px 0; }
.preview-body :deep(img)  { max-width: 100%; height: auto; }
.preview-body :deep(table) { display: table; border-collapse: collapse; max-width: 100%; margin: 12px 0; }
.preview-body :deep(td),
.preview-body :deep(th)   { border: 2px solid var(--color-pencil); padding: 8px 12px; vertical-align: top; }
.preview-body :deep(th)   { background: var(--color-muted); font-weight: 700; }

.empty-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
  padding: 30px;
}

.empty-preview h3 {
  font-family: var(--font-heading);
  font-size: 20px;
  color: var(--color-pencil);
  margin: 20px 0 10px;
}

.empty-preview p {
  font-family: var(--font-body);
  font-size: 14px;
  margin: 0;
}

/* ── Right AI Panel ── */
.right-ai-panel {
  background: #ffffff;
  border-left: 3px dashed var(--color-pencil);
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.ai-header {
  padding: 20px;
  border-bottom: 2px dashed var(--color-muted);
  flex-shrink: 0;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.ai-header-main { flex: 1; min-width: 0; }
.ai-header-clear { flex-shrink: 0; margin-top: 2px; }

.ai-header h3 {
  font-family: var(--font-heading);
  font-size: 18px;
  color: var(--color-pencil);
  margin: 0 0 4px;
  font-weight: 700;
}

.ai-header p {
  font-family: var(--font-body);
  font-size: 12px;
  color: #999;
  margin: 0;
}

.ai-chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

.chat-messages-stack {
  flex: 1;
  min-height: 0;
  position: relative;
  display: flex;
  flex-direction: column;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  overflow-x: auto;
  padding: 20px;
  min-height: 0;
}

.chat-scroll-float-btn {
  position: absolute;
  left: 50%;
  top: 95%;
  transform: translate(-50%, -50%);
  z-index: 6;
  width: 44px;
  height: 44px;
  padding: 0;
}

/* ── Welcome message inside chat ── */
.welcome-message {
  text-align: center;
  padding: 40px 20px;
  color: var(--color-pencil);
}

.welcome-icon {
  font-size: 48px;
  margin-bottom: 15px;
}

.welcome-message h4 {
  font-family: var(--font-heading);
  font-size: 18px;
  color: var(--color-pencil);
  margin: 0 0 15px;
  font-weight: 700;
}

.welcome-message p {
  font-size: 14px;
  color: #888;
  margin: 0 0 10px;
  font-family: var(--font-body);
}

.welcome-message ul {
  list-style: none;
  padding: 0;
  margin: 15px 0 0;
  text-align: left;
  max-width: 300px;
  margin-left: auto;
  margin-right: auto;
}

.welcome-message li {
  padding: 8px 12px;
  margin: 5px 0;
  background: var(--color-muted);
  border: 2px solid var(--color-pencil);
  border-radius: var(--radius-wobbly-sm);
  font-size: 14px;
  color: var(--color-pencil);
  font-family: var(--font-body);
}

/* ── Chat Messages ── */
.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  animation: messageSlideIn 0.3s ease;
}

@keyframes messageSlideIn {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}

.message-item.user { flex-direction: row-reverse; }

.message-avatar {
  width: 38px;
  height: 38px;
  border-radius: var(--radius-wobbly);
  border: 2px solid var(--color-pencil);
  background: var(--color-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.user-avatar { font-size: 20px; }

.message-content {
  max-width: 70%;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.message-item.user .message-content { align-items: flex-end; }

.message-text {
  padding: 12px 16px;
  border-radius: var(--radius-wobbly-sm);
  font-size: 14px;
  line-height: 1.6;
  word-wrap: break-word;
  border: 2px solid var(--color-pencil);
  font-family: var(--font-body);
}

.message-item.assistant .message-text {
  background: #ffffff;
  color: var(--color-pencil);
}

.message-item.user .message-text {
  background: var(--color-pencil);
  color: white;
}

.message-item.user .message-context-note {
  font-size: 12px;
  color: #999;
  line-height: 1.4;
  max-width: 100%;
  text-align: right;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.message-mindmap-actions { margin-top: 4px; }
.message-item.assistant .message-mindmap-actions { align-self: flex-start; }

.message-text :deep(p) { margin: 8px 0; }
.message-text :deep(p:first-child) { margin-top: 0; }
.message-text :deep(p:last-child)  { margin-bottom: 0; }
.message-text :deep(code) {
  background: var(--color-muted);
  padding: 2px 6px;
  border-radius: 6px;
  font-family: var(--font-mono);
  font-size: 13px;
}
.message-item.user .message-text :deep(code) { background: rgba(255,255,255,0.2); }
.message-text :deep(pre) {
  background: rgba(0,0,0,0.05);
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
  border: 2px solid var(--color-muted);
}
.message-item.user .message-text :deep(pre) { background: rgba(255,255,255,0.1); border-color: rgba(255,255,255,0.3); }
.message-text :deep(img)   { max-width: 100%; height: auto; }
.message-text :deep(table) { border-collapse: collapse; max-width: 100%; margin: 8px 0; }
.message-text :deep(td),
.message-text :deep(th)    { border: 1px solid var(--color-pencil); padding: 6px 10px; }
.message-item.user .message-text :deep(td),
.message-item.user .message-text :deep(th) { border-color: rgba(255,255,255,0.35); }

.message-time {
  font-size: 12px;
  color: #999;
  padding: 0 4px;
}

/* ── Typing indicator ── */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: #fff;
  border: 2px solid var(--color-pencil);
  border-radius: var(--radius-wobbly-sm);
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-pencil);
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-10px); opacity: 1; }
}

/* ── Input Area ── */
.input-section {
  padding: 15px 20px;
  border-top: 2px dashed var(--color-pencil);
  background: #fff;
  flex-shrink: 0;
}

.uploaded-note-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  margin-bottom: 12px;
  background: var(--color-yellow);
  border: 2px solid var(--color-pencil);
  border-radius: var(--radius-wobbly-sm);
  color: var(--color-pencil);
  font-size: 13px;
  font-family: var(--font-body);
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateY(-10px); }
  to   { opacity: 1; transform: translateY(0); }
}

.uploaded-note-banner .note-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 600;
}

.uploaded-note-banner .el-button { color: var(--color-pencil); padding: 0; font-size: 12px; }
.uploaded-note-banner .el-button:hover { color: var(--color-accent); }

.quick-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.quick-actions .el-button {
  flex: 1;
  min-width: 0;
}

.input-wrapper {
  position: relative;
  display: flex;
  gap: 10px;
  align-items: flex-end;
}

.input-container { position: relative; flex: 1; }

.upload-note-btn {
  position: absolute;
  bottom: 8px;
  left: 8px;
  width: 28px;
  height: 28px;
  padding: 0;
  z-index: 10;
}

.ai-input { flex: 1; }

.ai-input :deep(.el-textarea__inner) {
  padding: 12px 15px 12px 45px;
  font-size: 14px;
  line-height: 1.6;
  resize: none;
  font-family: var(--font-body);
}

.send-btn { width: 44px; height: 44px; flex-shrink: 0; }
.stop-ai-btn { flex-shrink: 0; height: 44px; padding: 0 14px; font-size: 13px; }
.send-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* ── Note Selector Dropdown ── */
.note-selector-dropdown {
  background: white;
  border: 2px solid var(--color-pencil);
  border-radius: var(--radius-wobbly-md);
  box-shadow: var(--shadow-hard);
  max-height: 300px;
  overflow-y: auto;
  animation: slideDown 0.2s ease;
  margin-bottom: 12px;
}

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-10px); }
  to   { opacity: 1; transform: translateY(0); }
}

.selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 2px dashed var(--color-muted);
  background: var(--color-muted);
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 600;
  color: var(--color-pencil);
}

.note-list-container { max-height: 250px; overflow-y: auto; }

.note-option {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
  cursor: pointer;
  transition: all 0.15s;
  border-bottom: 1px solid var(--color-muted);
}

.note-option:hover { background: var(--color-yellow); }
.note-option:last-child { border-bottom: none; }

.note-info { flex: 1; min-width: 0; }

.note-info .note-title {
  font-family: var(--font-heading);
  font-size: 14px;
  font-weight: 600;
  color: var(--color-pencil);
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.note-preview {
  font-size: 12px;
  color: #999;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.empty-note-list { padding: 40px 20px; text-align: center; color: #999; }
.empty-note-list p { margin: 0; font-size: 14px; }
</style>