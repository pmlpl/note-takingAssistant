<template>
  <el-aside width="480px" class="right-ai-panel">
    <div class="ai-header">
      <div class="ai-header-main">
        <h3><IconAI :size="24" />AI 助手</h3>
        <p>
          智能问答与辅助 · 本地最多保留 {{ HOME_CHAT_MAX_MESSAGES }} 条，超出自动丢弃最早消息
        </p>
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
              <li>🎯 提供学习建议</li>
              <li>📚 解释复杂概念</li>
            </ul>
          </div>

          <div
            v-for="(message, index) in chatHistory"
            :key="index"
            :class="['message-item', message.role]"
          >
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

      <div class="input-section">
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

        <div v-else-if="uploadedNoteContent" class="uploaded-note-banner">
          <IconDocument :size="16" color="#409eff" />
          <span class="note-name">{{ uploadedNoteName }}</span>
          <el-button size="small" link type="danger" @click="clearUploadedNote"> 清除 </el-button>
        </div>

        <div class="quick-actions">
          <el-button size="small" :disabled="isAiOutputInProgress" @click="sendMindmapQuickPrompt">
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
</template>

<script setup>
import { ArrowDown } from '@element-plus/icons-vue'
import { IconAI, IconDocument, IconPlus, IconEdit } from '@/components/icons'
import { useHomeInject } from '@/composables/home/useHomeInject'

const {
  HOME_CHAT_MAX_MESSAGES,
  chatHistory,
  isAiThinking,
  isAiOutputInProgress,
  chatMessagesRef,
  aiMessage,
  uploadedNoteContent,
  uploadedNoteName,
  showNoteSelector,
  filteredNotes,
  showScrollToLatestBtn,
  confirmClearChat,
  onChatScroll,
  scrollChatToLatest,
  renderMessage,
  formatTime,
  extractMindmapDiagramSource,
  openMindmapPreviewFromMessage,
  sendMindmapQuickPrompt,
  sendQuickMessage,
  closeNoteSelector,
  selectNoteForContext,
  clearUploadedNote,
  uploadNoteToAI,
  handleInput,
  sendMessage,
  stopAiChatOutput
} = useHomeInject()
</script>
