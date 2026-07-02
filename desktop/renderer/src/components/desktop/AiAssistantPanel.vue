<template>
  <div class="ai-assistant-panel">
    <!-- 面板头部 -->
    <div class="panel-header">
      <div class="panel-title">
        <IconAI :size="20" :color="ICON_COLOR" />
        <span>AI 助手</span>
      </div>
      <button class="close-btn" @click="$emit('close')" title="关闭">
        <svg width="14" height="14" viewBox="0 0 14 14">
          <line x1="2" y1="2" x2="12" y2="12" stroke="currentColor" stroke-width="1.5"/>
          <line x1="12" y1="2" x2="2" y2="12" stroke="currentColor" stroke-width="1.5"/>
        </svg>
      </button>
    </div>

    <!-- 快捷操作 -->
    <div class="quick-actions">
      <button class="quick-btn" @click="quickAction('summarize')">
        <IconTrend :size="16" :color="ICON_COLOR" />
        <span>生成摘要</span>
      </button>
      <button class="quick-btn" @click="quickAction('translate')">
        <IconTranslate :size="16" :color="ICON_COLOR" />
        <span>翻译</span>
      </button>
      <button class="quick-btn" @click="quickAction('generate')">
        <IconMagic :size="16" :color="ICON_COLOR" />
        <span>AI 生成</span>
      </button>
    </div>

    <!-- 对话区域 -->
    <div class="chat-area" ref="chatMessagesRef">
      <div v-if="chatHistory.length === 0" class="empty-chat">
        <IconAI :size="48" :color="ICON_COLOR" />
        <p>有什么可以帮助你的？</p>
        <p class="hint">输入问题或使用快捷操作</p>
      </div>

      <div
        v-for="(msg, idx) in chatHistory"
        :key="idx"
        class="message-item"
        :class="msg.role === 'user' ? 'message-user' : 'message-ai'"
      >
        <div class="message-bubble" v-html="renderMessage(msg.content)"></div>
        <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
      </div>

      <div v-if="isAiThinking" class="message-item message-ai">
        <div class="message-bubble thinking">
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="input-area">
      <div v-if="uploadedNoteName" class="uploaded-note">
        <IconDocument :size="14" :color="ICON_COLOR" />
        <span class="uploaded-name">{{ uploadedNoteName }}</span>
        <button class="clear-btn" @click="clearUploadedNote" title="清除">
          <svg width="12" height="12" viewBox="0 0 12 12">
            <line x1="2" y1="2" x2="10" y2="10" stroke="currentColor" stroke-width="1.5"/>
            <line x1="10" y1="2" x2="2" y2="10" stroke="currentColor" stroke-width="1.5"/>
          </svg>
        </button>
      </div>
      <div class="input-row">
        <el-input
          v-model="aiMessage"
          type="textarea"
          :rows="2"
          placeholder="输入消息，Enter 发送..."
          resize="none"
          @keydown.enter.exact.prevent="sendMessage"
        />
        <el-button type="primary" :loading="isAiThinking" @click="sendMessage">
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { aiApi } from '@/api/ai'
import { noteApi } from '@/api/note'
import { renderMarkdownToSafeHtml } from '@/utils/htmlSanitize'
import {
  IconAI,
  IconTrend,
  IconTranslate,
  IconMagic,
  IconDocument
} from '@/components/icons'
import { useNotification } from '@/composables/useNotification'

const ICON_COLOR = 'var(--color-pencil)'

defineEmits(['close'])

const props = defineProps({
  noteContext: {
    type: Object,
    default: null
  }
})

const { notifyAIComplete } = useNotification()

const aiMessage = ref('')
const chatHistory = ref([])
const isAiThinking = ref(false)
const chatMessagesRef = ref(null)
const uploadedNoteName = ref('')
const uploadedNoteContent = ref(null)

// 渲染消息内容
function renderMessage(content) {
  return renderMarkdownToSafeHtml(content)
}

// 格式化时间
function formatTime(timestamp) {
  const date = new Date(timestamp)
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  return `${hours}:${minutes}`
}

// 滚动到底部
async function scrollToBottom() {
  await nextTick()
  if (chatMessagesRef.value) {
    chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
  }
}

// 发送消息
async function sendMessage() {
  if (!aiMessage.value.trim() || isAiThinking.value) return

  const userMessage = aiMessage.value.trim()
  aiMessage.value = ''

  // 添加用户消息
  chatHistory.value.push({
    role: 'user',
    content: userMessage,
    timestamp: new Date()
  })

  await scrollToBottom()
  isAiThinking.value = true

  try {
    // 构建历史消息
    const history = chatHistory.value.slice(0, -1).slice(-10).map(msg => ({
      role: msg.role,
      content: msg.content
    }))

    // 如果有笔记上下文，附加到消息中
    let messageForApi = userMessage
    if (uploadedNoteContent.value) {
      messageForApi = `笔记上下文: ${uploadedNoteName.value}\n内容: ${uploadedNoteContent.value}\n\n问题: ${userMessage}`
    } else if (props.noteContext?.content) {
      messageForApi = `当前笔记: ${props.noteContext.title || '未命名'}\n内容: ${props.noteContext.content}\n\n问题: ${userMessage}`
    }

    const result = await aiApi.chat({
      message: messageForApi,
      history
    })

    const reply = result.data?.reply || '抱歉，我暂时无法回答这个问题。'
    chatHistory.value.push({
      role: 'assistant',
      content: reply,
      timestamp: new Date()
    })

    // 发送系统通知
    await notifyAIComplete('AI对话')
  } catch (error) {
    console.error('AI 回复失败:', error)
    ElMessage.error('AI 服务暂时不可用，请稍后重试')
    chatHistory.value.push({
      role: 'assistant',
      content: '抱歉，服务暂时不可用，请稍后重试。',
      timestamp: new Date()
    })
  } finally {
    isAiThinking.value = false
    await scrollToBottom()
  }
}

// 快捷操作
function quickAction(type) {
  const messages = {
    summarize: '请帮我总结这篇笔记的主要内容',
    translate: '请帮我把这篇笔记翻译成英文',
    generate: '请基于当前内容帮我扩展生成相关内容'
  }
  aiMessage.value = messages[type] || ''
  sendMessage()
}

// 清除上传的笔记
function clearUploadedNote() {
  uploadedNoteName.value = ''
  uploadedNoteContent.value = null
}

// 暴露方法给父组件
defineExpose({
  setNoteContext(note) {
    if (note) {
      uploadedNoteName.value = note.title || '未命名笔记'
      uploadedNoteContent.value = note.content || ''
    }
  },
  clearChat() {
    chatHistory.value = []
  }
})
</script>

<style scoped>
.ai-assistant-panel {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-card-bg);
  border-left: 1px solid var(--color-muted);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-muted);
  background: var(--color-card-bg);
  flex-shrink: 0;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-heading);
  font-size: 18px;
  font-weight: 700;
  color: var(--color-pencil);
}

.close-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-secondary);
  transition: all 0.15s ease;
}

.close-btn:hover {
  background: var(--color-sidebar-hover);
  color: var(--color-accent);
}

.quick-actions {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-muted);
  flex-shrink: 0;
}

.quick-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 4px;
  border: 1px solid var(--color-muted);
  background: var(--color-content-bg);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: var(--font-body);
  font-size: 12px;
  color: var(--color-pencil);
}

.quick-btn:hover {
  background: var(--color-yellow);
  transform: translateY(-2px);
}

.chat-area {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.empty-chat {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 8px;
  color: var(--color-text-muted);
  font-family: var(--font-body);
}

.empty-chat .hint {
  font-size: 13px;
  opacity: 0.7;
}

.message-item {
  display: flex;
  flex-direction: column;
  max-width: 85%;
}

.message-user {
  align-self: flex-end;
  align-items: flex-end;
}

.message-ai {
  align-self: flex-start;
  align-items: flex-start;
}

.message-bubble {
  padding: 10px 14px;
  border-radius: 12px;
  font-family: var(--font-body);
  font-size: 14px;
  line-height: 1.6;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.message-user .message-bubble {
  background: var(--color-blue);
  color: #ffffff;
  border-radius: 12px 12px 4px 12px;
}

.message-ai .message-bubble {
  background: var(--color-content-bg);
  color: var(--color-pencil);
  border: 1px solid var(--color-muted);
  border-radius: 12px 12px 12px 4px;
}

.message-bubble.thinking {
  display: flex;
  gap: 4px;
  align-items: center;
}

.dot {
  width: 6px;
  height: 6px;
  background: var(--color-text-muted);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out;
}

.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.6; }
  40% { transform: scale(1); opacity: 1; }
}

.message-time {
  font-size: 11px;
  color: var(--color-text-muted);
  margin-top: 4px;
}

.input-area {
  border-top: 1px solid var(--color-muted);
  padding: 12px 16px;
  background: var(--color-card-bg);
  flex-shrink: 0;
}

.uploaded-note {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: var(--color-yellow);
  border-radius: 6px;
  margin-bottom: 8px;
  font-size: 12px;
  color: var(--color-pencil);
}

.uploaded-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

.clear-btn {
  border: none;
  background: transparent;
  cursor: pointer;
  color: var(--color-text-secondary);
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.clear-btn:hover {
  color: var(--color-accent);
}

.input-row {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}

.input-row .el-input {
  flex: 1;
  min-width: 0;
}

/* 深色模式通过 CSS 变量自动适配，无需额外覆盖 */

</style>