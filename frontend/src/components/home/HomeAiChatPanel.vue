<template>
  <el-aside width="560px" class="right-ai-panel">
    <div class="ai-header">
      <div class="ai-header-main">
        <h3>
          <IconAI :size="24" />AI 助手
          <el-button
            link
            size="small"
            class="ai-header-history-btn"
            title="历史对话"
            @click="toggleConversationDrawer"
          >
            <el-icon><Menu /></el-icon>
          </el-button>
        </h3>
        <p>
          智能问答与辅助 · 对话历史自动同步到云端
        </p>
        <!-- 视图切换 -->
        <div class="ai-view-toggle">
          <el-radio-group v-model="viewMode" size="small" @change="setViewMode">
            <el-radio-button value="all">全部</el-radio-button>
            <el-radio-button value="chat">仅聊天</el-radio-button>
            <el-radio-button value="note">仅笔记</el-radio-button>
          </el-radio-group>
        </div>
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

    <!-- 历史对话抽屉 -->
    <el-drawer
      v-model="showConversationDrawer"
      title="历史对话"
      direction="ltr"
      size="320px"
      :with-header="false"
      append-to-body
      class="conversation-drawer"
    >
      <div class="conversation-drawer-inner">
        <div class="conversation-drawer-header">
          <span class="conversation-drawer-title">历史对话</span>
          <el-button
            size="small"
            type="primary"
            plain
            @click="createNewConversation"
            title="新建对话"
          >
            + 新建
          </el-button>
        </div>
        <div
          v-loading="isLoadingConversations"
          class="conversation-drawer-list"
        >
          <div
            v-for="conv in conversationList"
            :key="conv.id"
            :class="[
              'conversation-item',
              { active: conv.id === currentConversationId }
            ]"
            @click="switchConversation(conv.id)"
          >
            <div class="conversation-item-main">
              <div class="conversation-item-title">{{ conv.title || '未命名对话' }}</div>
              <div class="conversation-item-time">
                {{ formatConversationTime(conv.updated_at || conv.created_at) }}
              </div>
            </div>
            <div class="conversation-item-actions" @click.stop>
              <el-button
                link
                size="small"
                title="重命名"
                @click="renameConversationById(conv.id)"
              >
                <el-icon><Edit /></el-icon>
              </el-button>
              <el-button
                link
                size="small"
                type="danger"
                title="删除"
                @click="deleteConversationById(conv.id)"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>
          <div v-if="!isLoadingConversations && conversationList.length === 0" class="conversation-empty">
            <p>暂无历史对话</p>
            <p class="conversation-empty-hint">发送第一条消息即可创建对话</p>
          </div>
        </div>
      </div>
    </el-drawer>

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
              <div
                v-if="message.role === 'assistant' && message.agents && message.agents.length"
                class="message-agents"
              >
                <span
                  v-for="agent in message.agents"
                  :key="agent.name"
                  :class="['message-agent-chip', agent.status]"
                  :title="agent.reason"
                >
                  {{ agent.emoji }} {{ agent.display_name }}
                  <span v-if="agent.status === 'running'" class="agent-status-dot"></span>
                </span>
              </div>

              <div
                v-if="message.role === 'assistant' && message.subAgents && message.subAgents.length"
                class="message-sub-agents"
              >
                <span class="sub-agents-label">→</span>
                <span
                  v-for="sub in message.subAgents"
                  :key="sub.name"
                  :class="['message-sub-agent-chip', sub.status]"
                  :title="`正在调用 ${sub.tool} 工具`"
                >
                  {{ sub.emoji }} {{ sub.display_name }}
                  <span v-if="sub.status === 'running'" class="agent-status-dot"></span>
                </span>
              </div>

              <div
                v-if="message.role === 'assistant' && message.thinking"
                class="message-thinking"
              >
                <div class="message-thinking-label">
                  💭 思考
                  <el-button
                    link
                    size="small"
                    class="thinking-toggle-btn"
                    @click="message.thinkingCollapsed = !message.thinkingCollapsed"
                  >
                    {{ message.thinkingCollapsed ? '展开' : '收起' }}
                  </el-button>
                </div>
                <div v-show="!message.thinkingCollapsed" class="message-thinking-text">
                  {{ message.thinking }}
                </div>
              </div>

              <div
                v-if="message.role === 'assistant' && message.toolCalls && message.toolCalls.length"
                class="message-tools"
              >
                <div
                  v-for="tool in message.toolCalls"
                  :key="tool.id"
                  class="message-tool-card"
                >
                  <div class="message-tool-header">
                    <span class="message-tool-name">🔧 {{ getToolLabel(tool.name) }}</span>
                    <span :class="['message-tool-status', tool.status]">
                      {{ tool.status === 'running' ? '运行中...' : '已完成' }}
                    </span>
                  </div>
                  <div v-if="tool.args && hasArgs(tool.args)" class="message-tool-args">
                    <span
                      v-for="(val, key) in tool.args"
                      :key="key"
                      class="message-tool-arg"
                    >
                      <span class="message-tool-arg-key">{{ key }}:</span>
                      <span class="message-tool-arg-val">{{ formatArgValue(val) }}</span>
                    </span>
                  </div>
                  <div v-if="tool.result && tool.result.error" class="message-tool-error">
                    ❌ {{ tool.result.error }}
                  </div>
                </div>
              </div>

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
import { ArrowDown, Menu, Edit, Delete } from '@element-plus/icons-vue'
import { IconAI, IconDocument, IconPlus, IconEdit } from '@/components/icons'
import { useHomeInject } from '@/composables/home/useHomeInject'

const TOOL_LABELS = {
  search_notes: '搜索笔记',
  get_note_content: '获取笔记内容',
  summarize_note: '总结笔记',
  generate_note: '生成笔记',
  translate_note: '翻译笔记',
  create_note: '创建笔记'
}

function getToolLabel(name) {
  return TOOL_LABELS[name] || name
}

function formatArgValue(val) {
  if (val == null) return ''
  if (typeof val === 'string') {
    return val.length > 30 ? val.slice(0, 30) + '...' : val
  }
  if (typeof val === 'number' || typeof val === 'boolean') {
    return String(val)
  }
  try {
    const s = JSON.stringify(val)
    return s.length > 30 ? s.slice(0, 30) + '...' : s
  } catch {
    return String(val)
  }
}

function hasArgs(args) {
  if (!args || typeof args !== 'object') return false
  return Object.keys(args).length > 0
}

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
  stopAiChatOutput,
  // 对话历史持久化
  currentConversationId,
  conversationList,
  showConversationDrawer,
  isLoadingConversations,
  switchConversation,
  createNewConversation,
  deleteConversationById,
  renameConversationById,
  toggleConversationDrawer,
  formatConversationTime,
  // 视图模式
  viewMode,
  setViewMode,
} = useHomeInject()
</script>
