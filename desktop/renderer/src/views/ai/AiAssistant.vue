<template>
  <div class="ai-assistant-page">
    <div class="ai-header">
      <div class="ai-header-main">
        <h3><IconAI :size="24" />AI 助手</h3>
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
        <div class="chat-messages" ref="chatMessagesRef" @scroll.passive="onChatScroll">
          <div v-if="chatHistory.length === 0" class="welcome-message">
            <div class="welcome-icon">👋</div>
            <h4>您好！我是您的 AI 笔记助手</h4>
            <p>我可以帮您：</p>
            <ul>
              <li>💡 解答学习问题</li>
              <li>📝 优化笔记内容</li>
              <li>💪 提供学习建议</li>
              <li>📚 解释复杂概念</li>
            </ul>
            <div class="quick-actions">
              <el-button size="small" @click="sendMindmapQuickPrompt">思维导图</el-button>
              <el-button size="small" @click="sendQuickMessage('学习建议')">学习建议</el-button>
              <el-button size="small" @click="sendQuickMessage('概念解释')">概念解释</el-button>
            </div>
          </div>

          <div
            v-for="(msg, idx) in chatHistory"
            :key="msg.id || idx"
            class="message-item"
            :class="{ assistant: msg.role === 'assistant', user: msg.role === 'user' }"
          >
            <div class="message-avatar">
              <IconAI v-if="msg.role === 'assistant'" class="assistant-avatar" />
              <img
                v-else-if="userStore.user?.avatarUrl"
                :src="userStore.user.avatarUrl"
                class="user-avatar-img"
              />
              <span v-else class="user-avatar">{{ displayName.slice(0, 1) }}</span>
            </div>
            <div class="message-content">
              <div v-if="msg.contextNoteTitle" class="message-context-note">
                📎 {{ msg.contextNoteTitle }}
              </div>
              <div
                v-if="msg.role === 'user' || (msg.role === 'assistant' && msg.content)"
                class="message-text"
                v-html="renderMessage(msg.content)"
              />
              <div
                v-else-if="msg.role === 'assistant' && !msg.content && idx === chatHistory.length - 1 && isAiThinking"
                class="typing-indicator"
              >
                <span></span><span></span><span></span>
              </div>
              <div v-if="msg.role === 'assistant' && msg.content" class="message-mindmap-actions">
                <el-button
                  v-if="extractMindmapDiagramSource(msg.content)"
                  size="small"
                  @click="openMindmapPreviewFromMessage(msg.content)"
                >
                  <IconMindmap :size="14" />
                  查看思维导图
                </el-button>
              </div>
              <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
            </div>
          </div>
        </div>

        <el-button
          v-if="showScrollToLatestBtn"
          type="primary"
          round
          class="chat-scroll-float-btn"
          @click="scrollChatToLatest"
        >
          <ArrowDown :size="20" />
        </el-button>
      </div>

      <div class="input-section">
        <div v-if="uploadedNoteContent" class="uploaded-note-banner">
          <IconDocument :size="16" />
          <span class="note-name">{{ uploadedNoteName || '上传的笔记' }}</span>
          <el-button link size="small" @click="clearUploadedNote">移除</el-button>
        </div>

        <div class="quick-actions">
          <el-button size="small" icon="Upload" @click="uploadNoteToAI">导入文件</el-button>
          <el-button size="small" @click="sendMindmapQuickPrompt">思维导图</el-button>
          <el-button size="small" @click="sendQuickMessage('学习建议')">学习建议</el-button>
          <el-button size="small" @click="sendQuickMessage('概念解释')">概念解释</el-button>
        </div>

        <div class="input-wrapper">
          <div class="input-container">
            <el-input
              v-model="aiMessage"
              type="textarea"
              :placeholder="uploadedNoteContent ? '基于上传的笔记提问...' : '输入您的问题...（输入 /note 可选择笔记）'"
              :rows="2"
              class="ai-input"
              @keydown.enter.exact.prevent="sendMessage"
              @input="handleInput"
            />
            <div class="input-actions">
              <el-button
                v-if="isAiOutputInProgress"
                type="warning"
                @click="stopAiChatOutput"
                class="stop-ai-btn"
                size="small"
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

        <div v-if="showNoteSelector" class="note-selector-dropdown">
          <div class="selector-header">
            <span>选择笔记作为上下文</span>
            <el-button link size="small" @click="closeNoteSelector">✕</el-button>
          </div>
          <div class="note-list-container">
            <div
              v-for="note in filteredNotes"
              :key="note.id"
              class="note-option"
              @click="selectNoteForContext(note)"
            >
              <IconDocument :size="20" />
              <div class="note-info">
                <div class="note-title">{{ note.title || '未命名笔记' }}</div>
                <div class="note-preview">{{ getNotePreview(note.content) }}</div>
              </div>
            </div>
            <div v-if="filteredNotes.length === 0" class="empty-note-list">
              <p>暂无笔记</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ArrowDown } from '@element-plus/icons-vue'
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store'
import { noteApi } from '@/api/note'
import { aiApi } from '@/api/ai'
import { ElMessage, ElMessageBox } from 'element-plus'
import { IconAI, IconDocument, IconEdit, IconMindmap } from '@/components/icons'
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
  name: 'AiAssistant'
})

const HOME_CHAT_MAX_MESSAGES = 40
const HOME_CHAT_STREAM_MS = Number(import.meta.env.VITE_AI_REQUEST_TIMEOUT_MS) || 600_000

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

let homeChatAbortController = null
let homeChatStopWasUser = false

const router = useRouter()
const userStore = useUserStore()

const homeBoundUserId = ref(null)
const boundAuthEpoch = ref(-1)

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

const aiMessage = ref('')
const chatHistory = ref([])
const isAiThinking = ref(false)
const isAiOutputInProgress = ref(false)
const chatMessagesRef = ref(null)
const uploadedNoteContent = ref(null)
const uploadedNoteName = ref('')
const showNoteSelector = ref(false)
const allNotes = ref([])
const showScrollToLatestBtn = ref(false)

const displayName = computed(() => {
  const u = userStore.user
  if (!u) return '用户'
  return u.nickname || u.username || (u.email ? u.email.split('@')[0] : '用户')
})

const filteredNotes = computed(() => {
  return allNotes.value
})

function noteContentToSafeHtml(content) {
  if (!content) return ''
  return isLikelyHtmlContent(content)
    ? sanitizeHtml(content)
    : renderMarkdownToSafeHtml(content)
}

onMounted(async () => {
  await ensureHomeSessionForCurrentUser()
})

onBeforeUnmount(() => {
  homeChatStopWasUser = false
})

watch(
  () => [userStore.user?.id, userStore.user?.email, userStore.authSessionEpoch],
  () => {
    void ensureHomeSessionForCurrentUser()
  }
)

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
    console.error('加载笔记列表失败:', error)
  }
}

function clearHomeUiState() {
  allNotes.value = []
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

function sendQuickMessage(message) {
  aiMessage.value = message
  sendMessage()
}

function sendMindmapQuickPrompt() {
  sendQuickMessage(AI_MINDMAP_QUICK_PROMPT)
}

function openMindmapPreviewFromMessage(markdown) {
  const raw = extractMindmapDiagramSource(markdown)
  const src = prepareMermaidSourceForRender(raw)
  if (!raw) {
    ElMessage.warning({
      message: '未识别到可渲染的 Mermaid 图表',
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
    ElMessage.error({ message: '无法暂存导图数据', duration: MESSAGE_DURATION.SHORT })
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
      let content = ''

      if (file.name.endsWith('.docx')) {
        const arrayBuffer = await file.arrayBuffer()
        const mammoth = (await import('mammoth')).default
        const result = await mammoth.convertToHtml({ arrayBuffer })
        content = result.value.replace(/<[^>]*>/g, '')
      } else if (file.name.endsWith('.md')) {
        content = await file.text()
      } else if (file.name.endsWith('.txt')) {
        content = await file.text()
      } else {
        ElMessage.error({ message: '不支持的文件格式', duration: MESSAGE_DURATION.SHORT })
        return
      }

      if (!content.trim()) {
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

function clearUploadedNote() {
  uploadedNoteContent.value = null
  uploadedNoteName.value = ''
  ElMessage.success({ message: '已清除上传的笔记', duration: MESSAGE_DURATION.SHORT })
}

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

  chatHistory.value.push({
    role: 'user',
    content: userMessage,
    timestamp: new Date(),
    contextNoteTitle: hasNoteContext ? (uploadedNoteName.value || '笔记') : undefined
  })

  chatHistory.value.push({
    role: 'assistant',
    content: '',
    timestamp: new Date()
  })
  saveChatHistory()

  scrollToBottom()

  isAiThinking.value = true
  isAiOutputInProgress.value = true

  ;(async () => {
    const streamAbort = new AbortController()
    homeChatAbortController = streamAbort
    const timeoutId = setTimeout(() => streamAbort.abort(), HOME_CHAT_STREAM_MS)
    let assistantIdx = chatHistory.value.length - 1

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

      await aiApi.chatStream({
        message: messageForApi,
        history: messages,
        signal: streamAbort.signal,
        onChunk: (acc) => {
          chatHistory.value[assistantIdx].content = acc
          isAiThinking.value = false
          scheduleHomeChatScroll()
          scheduleDebouncedSaveChatHistory()
        }
      })

      const c = String(chatHistory.value[assistantIdx].content || '').trim()
      if (!c) {
        chatHistory.value[assistantIdx].content = '抱歉，我暂时无法回答这个问题。'
      }

    } catch (error) {
      console.error('AI 回复失败:', error)
      const aborted = error?.name === 'AbortError' || streamAbort.signal.aborted
      let fallback = '抱歉，服务暂时不可用，请稍后重试。'

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
        if (String(chatHistory.value[assistantIdx].content || '').trim()) {
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
      } else if (String(chatHistory.value[assistantIdx].content || '').trim()) {
        ElMessage.warning({
          message: '回复已中断（可能为超时）',
          duration: MESSAGE_DURATION.SHORT
        })
      } else {
        ElMessage.info({
          message: '已取消或超时',
          duration: MESSAGE_DURATION.SHORT
        })
      }

      if (!aborted) {
        if (!String(chatHistory.value[assistantIdx].content || '').trim()) {
          chatHistory.value[assistantIdx].content = fallback
        }
      } else if (homeChatStopWasUser) {
        if (!String(chatHistory.value[assistantIdx].content || '').trim()) {
          chatHistory.value[assistantIdx].content = '（已停止生成）'
        }
      } else {
        if (!String(chatHistory.value[assistantIdx].content || '').trim()) {
          chatHistory.value[assistantIdx].content = fallback
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
}

function renderMessage(content) {
  return noteContentToSafeHtml(content)
}

function formatTime(timestamp) {
  const date = new Date(timestamp)
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  return `${hours}:${minutes}`
}

async function scrollToBottom() {
  await nextTick()
  if (chatMessagesRef.value) {
    chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
  }
  await nextTick()
  onChatScroll()
}

function handleInput(value) {
  if (value.includes('/note')) {
    showNoteSelector.value = true
  } else {
    showNoteSelector.value = false
  }
}

function closeNoteSelector() {
  showNoteSelector.value = false
  if (aiMessage.value.endsWith('/note')) {
    aiMessage.value = aiMessage.value.slice(0, -5)
  }
}

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

function unwrapNoteResponse(res) {
  if (!res || typeof res !== 'object') return null
  if ('content' in res || 'title' in res || 'id' in res) return res
  if (res.data && typeof res.data === 'object') return res.data
  return res
}

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

function getNotePreview(content) {
  if (!content) return ''
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
.ai-assistant-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--color-content-bg);
  overflow: hidden;
}

.ai-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 2px dashed var(--color-muted);
  background: var(--color-card-bg);
  flex-shrink: 0;
}

.ai-header-main {
  flex: 1;
}

.ai-header h3 {
  font-family: var(--font-heading);
  font-size: 20px;
  color: var(--color-heading);
  margin: 0 0 4px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.ai-header p {
  font-family: var(--font-body);
  font-size: 12px;
  color: var(--color-text-muted);
  margin: 0;
}

.ai-header-clear {
  flex-shrink: 0;
}

.ai-chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.chat-messages-stack {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.chat-messages {
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 20px;
  background: var(--color-content-bg);
}

.welcome-message {
  text-align: center;
  padding: 60px 20px;
  color: var(--color-text-secondary);
}

.welcome-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.welcome-message h4 {
  font-family: var(--font-heading);
  font-size: 18px;
  color: var(--color-heading);
  margin: 0 0 12px 0;
}

.welcome-message p {
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0 0 16px 0;
}

.welcome-message ul {
  text-align: left;
  max-width: 300px;
  margin: 0 auto 20px;
  padding-left: 20px;
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-text-secondary);
}

.welcome-message .quick-actions {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.message-item.assistant {
  flex-direction: row;
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
}

.assistant-avatar {
  color: var(--color-primary);
}

.user-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--color-primary);
  color: white;
  font-family: var(--font-heading);
  font-size: 14px;
  font-weight: 600;
}

.message-content {
  max-width: 70%;
}

.message-item.user .message-content {
  text-align: right;
}

.message-context-note {
  font-size: 12px;
  color: var(--color-text-muted);
  line-height: 1.4;
  margin-bottom: 4px;
}

.message-item.user .message-context-note {
  text-align: right;
}

.message-text {
  padding: 12px 16px;
  background: var(--color-card-bg);
  border: 2px solid var(--color-pencil);
  border-radius: var(--radius-wobbly-sm);
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-text-primary);
  line-height: 1.6;
  word-break: break-word;
}

.message-item.user .message-text {
  background: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

.message-mindmap-actions {
  margin-top: 8px;
}

.message-item.user .message-mindmap-actions {
  text-align: right;
}

.message-time {
  font-size: 12px;
  color: var(--color-text-muted);
  padding: 4px 4px 0;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: var(--color-card-bg);
  border: 2px solid var(--color-pencil);
  border-radius: var(--radius-wobbly-sm);
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: var(--color-pencil);
  border-radius: 50%;
  animation: typingBounce 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes typingBounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.chat-scroll-float-btn {
  position: absolute;
  bottom: 16px;
  right: 16px;
  z-index: 10;
}

.input-section {
  padding: 15px 20px;
  border-top: 2px dashed var(--color-muted);
  background: var(--color-card-bg);
  flex-shrink: 0;
}

.uploaded-note-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--color-primary);
  color: white;
  border-radius: 8px;
  margin-bottom: 12px;
  font-size: 13px;
}

.note-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.input-section .quick-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 12px;
}

.input-container {
  flex: 1;
  position: relative;
  display: flex;
  align-items: stretch;
}

.ai-input {
  flex: 1;
  border-radius: var(--radius-wobbly-md);
}

.input-actions {
  position: absolute;
  right: 8px;
  bottom: 8px;
  display: flex;
  gap: 8px;
  align-items: center;
}

.stop-ai-btn {
  flex-shrink: 0;
}

.send-btn {
  flex-shrink: 0;
}

.note-selector-dropdown {
  background: var(--color-card-bg);
  border: 2px solid var(--color-pencil);
  border-radius: var(--radius-wobbly-md);
  box-shadow: var(--shadow-hard);
  max-height: 300px;
  overflow-y: auto;
  margin-bottom: 12px;
  animation: slideUp 0.2s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 2px dashed var(--color-muted);
  font-family: var(--font-heading);
  font-size: 14px;
  color: var(--color-heading);
}

.note-list-container {
  padding: 8px;
}

.note-option {
  display: flex;
  gap: 12px;
  padding: 10px 12px;
  cursor: pointer;
  border-radius: 8px;
  transition: background 0.15s ease;
}

.note-option:hover {
  background: var(--color-muted);
}

.note-option .note-info {
  flex: 1;
  min-width: 0;
}

.note-option .note-title {
  font-family: var(--font-heading);
  font-size: 14px;
  font-weight: 600;
  color: var(--color-heading);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 4px;
}

.note-option .note-preview {
  font-family: var(--font-body);
  font-size: 12px;
  color: var(--color-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-note-list {
  padding: 20px;
  text-align: center;
  color: var(--color-text-muted);
}

@media (prefers-color-scheme: dark) {
  .user-avatar {
    background: var(--color-primary);
  }
}
</style>