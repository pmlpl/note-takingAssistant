<template>
  <div class="note-edit-desktop">
    <!-- 左栏：笔记列表 -->
    <aside class="left-panel" :class="{ 'left-panel-collapsed': !showLeftPanel }">
      <div class="panel-header">
        <div class="panel-title">
          <IconDocument :size="18" :color="ICON_COLOR" />
          <span v-if="showLeftPanel">笔记列表</span>
        </div>
        <button v-if="showLeftPanel" class="collapse-btn" @click="toggleLeftPanel" title="折叠">
          <svg width="14" height="14" viewBox="0 0 14 14">
            <polyline points="9,2 4,7 9,12" fill="none" stroke="currentColor" stroke-width="1.5"/>
          </svg>
        </button>
        <button v-else class="expand-btn" @click="toggleLeftPanel" title="展开">
          <svg width="14" height="14" viewBox="0 0 14 14">
            <polyline points="5,2 10,7 5,12" fill="none" stroke="currentColor" stroke-width="1.5"/>
          </svg>
        </button>
      </div>

      <div v-if="showLeftPanel" class="notes-list">
        <div class="search-bar">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索笔记..."
            size="small"
            clearable
          >
            <template #prefix>
              <IconSearch :size="14" />
            </template>
          </el-input>
        </div>

        <div class="notes-scroll" v-loading="loadingNotes">
          <div
            v-for="note in filteredNotes"
            :key="note.id"
            class="note-item"
            :class="{ 'note-item-active': isCurrentNote(note.id) }"
            @click="selectNote(note)"
          >
            <div class="note-item-title">{{ note.title || '未命名笔记' }}</div>
            <div class="note-item-meta">
              <span class="note-item-time">{{ formatNoteTime(note.updated_at || note.created_at) }}</span>
            </div>
          </div>

          <div v-if="!loadingNotes && filteredNotes.length === 0" class="empty-list">
            <p>暂无笔记</p>
            <el-button size="small" @click="createNewNote">
              <IconPlus :size="14" />
              新建笔记
            </el-button>
          </div>
        </div>

        <div class="new-note-btn">
          <el-button type="primary" size="small" @click="createNewNote" style="width: 100%">
            <IconPlus :size="14" />
            新建笔记
          </el-button>
        </div>
      </div>
    </aside>

    <!-- 中栏：笔记预览/编辑器 -->
    <main class="middle-panel">
      <div class="edit-header">
        <el-button size="small" @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <h2 class="edit-title">
          <template v-if="viewMode === 'preview'">预览笔记</template>
          <template v-else>{{ isEdit ? '编辑笔记' : '新建笔记' }}</template>
        </h2>
        <div class="header-actions">
          <template v-if="viewMode === 'preview'">
            <el-button type="primary" size="small" @click="enterEditMode">
              <IconEdit :size="14" :color="'#fff'" />
              编辑
            </el-button>
            <el-button size="small" @click="toggleAiPanel" :type="showAiPanel ? 'success' : ''">
              <IconAI :size="16" :color="ICON_COLOR" />
              AI助手
            </el-button>
          </template>
          <template v-else>
            <el-radio-group v-model="editorMode" size="small">
              <el-radio-button value="rich">富文本</el-radio-button>
              <el-radio-button value="markdown">Markdown</el-radio-button>
            </el-radio-group>
            <el-button type="primary" size="small" @click="saveNote" :loading="saving">
              保存
            </el-button>
            <el-button size="small" @click="toggleAiPanel" :type="showAiPanel ? 'success' : ''">
              <IconAI :size="16" :color="ICON_COLOR" />
              AI助手
            </el-button>
          </template>
        </div>
      </div>

      <!-- 预览模式 -->
      <div v-if="viewMode === 'preview'" class="preview-content" v-loading="loadingNote">
        <div v-if="form.title || form.content" class="preview-inner">
          <div class="preview-page-header">
            <h1 class="preview-page-title">{{ form.title || '未命名笔记' }}</h1>
            <div class="preview-page-meta">
              <span class="preview-page-time">
                更新于 {{ formatFullTime(currentNote?.updated_at || currentNote?.created_at) }}
              </span>
              <div v-if="previewTags.length > 0" class="preview-page-tags">
                <span v-for="tag in previewTags" :key="tag" class="preview-page-tag">{{ tag }}</span>
              </div>
            </div>
          </div>
          <div class="preview-page-body" v-html="renderedPreviewContent"></div>
        </div>
        <div v-else class="preview-empty">
          <IconDocument :size="64" :color="ICON_COLOR" />
          <p>笔记内容为空</p>
        </div>
      </div>

      <!-- 编辑模式 -->
      <div v-else class="edit-content">
        <el-form :model="form" label-position="top">
          <el-form-item label="标题" prop="title" :rules="[{ required: true, message: '请输入标题' }]">
            <el-input v-model="form.title" placeholder="请输入笔记标题" size="large" />
          </el-form-item>
          <el-form-item label="标签">
            <el-input v-model="form.tags" placeholder="多个标签用逗号分隔" />
          </el-form-item>
          <el-form-item label="内容">
            <RichText v-if="editorMode === 'rich'" v-model="form.content" />
            <div v-else class="markdown-editor">
              <el-input
                v-model="form.content"
                type="textarea"
                :rows="20"
                placeholder="支持 Markdown 或 HTML 语法..."
                class="markdown-input"
              />
              <div class="markdown-preview" v-html="renderedContent"></div>
            </div>
          </el-form-item>
        </el-form>
      </div>
    </main>

    <!-- 右栏：AI助手面板 -->
    <aside class="right-panel" :class="{ 'right-panel-hidden': !showAiPanel }">
      <AiAssistantPanel
        ref="aiPanelRef"
        :note-context="currentNoteContext"
        @close="toggleAiPanel"
      />
    </aside>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { noteApi } from '@/api/note'
import { useNoteStore } from '@/store'
import RichText from '@/components/RichText.vue'
import AiAssistantPanel from '@/components/desktop/AiAssistantPanel.vue'
import {
  IconDocument,
  IconSearch,
  IconPlus,
  IconAI,
  IconEdit
} from '@/components/icons'
import { sanitizeHtml, renderMarkdownToSafeHtml, isLikelyHtmlContent } from '@/utils/htmlSanitize'

defineOptions({
  name: 'NoteEditDesktop'
})

const ICON_COLOR = 'var(--color-pencil)'

const route = useRoute()
const router = useRouter()
const noteStore = useNoteStore()

// 面板状态
const showLeftPanel = ref(true)
const showAiPanel = ref(false)

// 笔记列表
const notes = ref([])
const loadingNotes = ref(false)
const searchKeyword = ref('')

// 当前编辑的笔记
const isEdit = ref(false)
const saving = ref(false)
const loadingNote = ref(false)
const editorMode = ref('rich')
const currentNoteId = ref(null)
const currentNote = ref(null)
const viewMode = ref('edit') // 'preview' | 'edit'

const form = ref({
  title: '',
  tags: '',
  content: ''
})

const aiPanelRef = ref(null)

// 当前笔记上下文（用于AI助手）
const currentNoteContext = computed(() => {
  return {
    title: form.value.title,
    content: form.value.content
  }
})

// 过滤笔记
const filteredNotes = computed(() => {
  if (!searchKeyword.value) return notes.value
  const keyword = searchKeyword.value.toLowerCase()
  return notes.value.filter(n =>
    (n.title || '').toLowerCase().includes(keyword)
  )
})

// 渲染Markdown内容
const renderedContent = computed(() => {
  if (!form.value.content) return ''
  const isHtml = /<[a-z][\s\S]*>/i.test(form.value.content)
  if (isHtml) return sanitizeHtml(form.value.content)
  return renderMarkdownToSafeHtml(form.value.content)
})

// 预览模式的标签
const previewTags = computed(() => {
  const tags = form.value.tags
  if (!tags) return []
  if (Array.isArray(tags)) return tags
  if (typeof tags === 'string') return tags.split(',').map(t => t.trim()).filter(Boolean)
  return []
})

// 预览模式的内容渲染
const renderedPreviewContent = computed(() => {
  if (!form.value.content) return ''
  return isLikelyHtmlContent(form.value.content)
    ? sanitizeHtml(form.value.content)
    : renderMarkdownToSafeHtml(form.value.content)
})

// 加载笔记列表
async function loadNotes() {
  loadingNotes.value = true
  try {
    const res = await noteApi.searchNotes({ page: 1, pageSize: 100 })
    // 响应拦截器已返回 response.data，无需再取 .data
    notes.value = res.items || res.notes || res.data?.items || res.data?.notes || res.data || []
  } catch (err) {
    console.error('加载笔记列表失败:', err)
    ElMessage.error('加载笔记列表失败')
  } finally {
    loadingNotes.value = false
  }
}

// 加载单个笔记
async function loadNote(id) {
  loadingNote.value = true
  try {
    const res = await noteApi.getNote(id)
    const note = res.note || res.data?.note || res.data || res
    if (note) {
      currentNote.value = note
      form.value.title = note.title || ''
      // tags 可能是数组或字符串，统一处理为逗号分隔字符串
      const tags = note.tags
      if (Array.isArray(tags)) {
        form.value.tags = tags.join(', ')
      } else if (typeof tags === 'string') {
        form.value.tags = tags
      } else {
        form.value.tags = ''
      }
      form.value.content = note.content || ''
      currentNoteId.value = id
      isEdit.value = true
      // 根据路由参数决定进入预览还是编辑模式
      const urlMode = route.query.mode
      viewMode.value = urlMode === 'edit' ? 'edit' : 'preview'
    }
  } catch (err) {
    console.error('加载笔记失败:', err)
    ElMessage.error('加载笔记失败')
  } finally {
    loadingNote.value = false
  }
}

// 进入编辑模式
function enterEditMode() {
  viewMode.value = 'edit'
}

// 保存笔记
async function saveNote() {
  if (!form.value.title.trim()) {
    ElMessage.warning('请输入笔记标题')
    return
  }
  saving.value = true
  try {
    const noteData = {
      title: form.value.title,
      content: form.value.content,
      tags: form.value.tags.split(',').map(t => t.trim()).filter(Boolean)
    }
    if (isEdit.value && currentNoteId.value) {
      await noteApi.updateNote(currentNoteId.value, noteData)
      ElMessage.success('笔记已更新')
    } else {
      const res = await noteApi.createNote(noteData)
      const newId = res.data?.id || res.data?.note?.id
      if (newId) {
        currentNoteId.value = newId
        isEdit.value = true
      }
      ElMessage.success('笔记已创建')
    }
    await loadNotes()
  } catch (err) {
    console.error('保存笔记失败:', err)
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

// 创建新笔记
function createNewNote() {
  form.value = { title: '', tags: '', content: '' }
  currentNoteId.value = null
  currentNote.value = null
  isEdit.value = false
  // 新建笔记直接进入编辑模式
  viewMode.value = 'edit'
  // 检查是否有拖拽导入的内容
  const dragContent = sessionStorage.getItem('dragImportContent')
  const dragFileName = sessionStorage.getItem('dragImportFileName')
  if (dragContent) {
    form.value.content = dragContent
    if (dragFileName) {
      form.value.title = dragFileName.replace(/\.[^.]+$/, '')
    }
    sessionStorage.removeItem('dragImportContent')
    sessionStorage.removeItem('dragImportFileName')
  }
  if (route.path !== '/notes/edit') {
    router.push('/notes/edit')
  }
}

// 选择笔记
async function selectNote(note) {
  // 直接加载笔记内容
  await loadNote(note.id)
  // 更新URL，保持路由同步，保留当前模式
  if (route.params.id !== String(note.id)) {
    const modeParam = viewMode.value === 'edit' ? '?mode=edit' : ''
    router.replace(`/notes/edit/${note.id}${modeParam}`)
  }
}

// 判断是否为当前笔记
function isCurrentNote(noteId) {
  return String(currentNoteId.value) === String(noteId)
}

// 格式化笔记时间
function formatNoteTime(time) {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now - date
  if (diff < 60 * 1000) return '刚刚'
  if (diff < 60 * 60 * 1000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 24 * 60 * 60 * 1000) return `${Math.floor(diff / 3600000)}小时前`
  const month = (date.getMonth() + 1).toString().padStart(2, '0')
  const day = date.getDate().toString().padStart(2, '0')
  return `${month}-${day}`
}

function formatFullTime(time) {
  if (!time) return ''
  const date = new Date(time)
  const year = date.getFullYear()
  const month = (date.getMonth() + 1).toString().padStart(2, '0')
  const day = date.getDate().toString().padStart(2, '0')
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}`
}

// 切换面板
function toggleLeftPanel() {
  showLeftPanel.value = !showLeftPanel.value
}

function toggleAiPanel() {
  showAiPanel.value = !showAiPanel.value
  if (showAiPanel.value && aiPanelRef.value) {
    aiPanelRef.value.setNoteContext(currentNoteContext.value)
  }
}

// 返回
function goBack() {
  router.push('/notes')
}

// 监听路由参数变化
watch(() => route.params.id, async (newId) => {
  if (newId && newId !== 'new') {
    await loadNote(newId)
  } else if (!newId) {
    createNewNote()
  }
}, { immediate: false })

onMounted(async () => {
  await loadNotes()
  const id = route.params.id
  if (id && id !== 'new') {
    await loadNote(id)
  } else {
    createNewNote()
  }
})
</script>

<style scoped>
.note-edit-desktop {
  display: flex;
  width: 100%;
  height: 100%;
  background: var(--color-content-bg);
  overflow: hidden;
}

/* 左栏 */
.left-panel {
  width: 280px;
  background: var(--color-card-bg);
  border-right: 1px solid var(--color-muted);
  display: flex;
  flex-direction: column;
  transition: width 0.25s ease;
  flex-shrink: 0;
}

.left-panel-collapsed {
  width: 48px;
}

.left-panel-collapsed .panel-header {
  justify-content: center;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border-bottom: 1px solid var(--color-muted);
  min-height: 48px;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-heading);
  font-size: 16px;
  font-weight: 700;
  color: var(--color-pencil);
}

.collapse-btn,
.expand-btn {
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

.collapse-btn:hover,
.expand-btn:hover {
  background: rgba(0, 0, 0, 0.08);
  color: var(--color-pencil);
}

.notes-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.search-bar {
  padding: 12px;
}

.notes-scroll {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 0 12px;
}

.note-item {
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
  margin-bottom: 4px;
  border: 1px solid transparent;
}

.note-item:hover {
  background: var(--color-muted);
}

.note-item-active {
  background: var(--color-yellow);
  border-color: var(--color-pencil);
  transform: rotate(-0.5deg);
}

.note-item-title {
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 600;
  color: var(--color-pencil);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 4px;
}

.note-item-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.note-item-time {
  font-size: 12px;
  color: #888;
}

.empty-list {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  gap: 12px;
  color: #888;
}

.new-note-btn {
  padding: 12px;
  border-top: 1px solid var(--color-muted);
}

/* 中栏 */
.middle-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--color-content-bg);
}

.edit-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  border-bottom: 1px solid var(--color-muted);
  background: var(--color-content-bg);
  gap: 12px;
  flex-shrink: 0;
}

.edit-title {
  font-family: var(--font-heading);
  font-size: 18px;
  color: var(--color-pencil);
  margin: 0;
  flex: 1;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-shrink: 0;
}

/* 富文本/Markdown切换按钮 - 高优先级确保显示 */
:deep(.header-actions .el-radio-button__inner) {
  background: var(--color-card-bg) !important;
  color: var(--color-pencil) !important;
  border-color: var(--color-muted) !important;
}

:deep(.header-actions .el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: var(--color-blue) !important;
  color: #fff !important;
  border-color: var(--color-blue) !important;
}

/* 保存按钮样式 */
:deep(.header-actions .el-button--primary) {
  background: var(--color-blue) !important;
  border-color: var(--color-blue) !important;
  color: #fff !important;
}

.edit-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 20px;
}

/* 预览模式 */
.preview-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  background: var(--color-content-bg);
  min-height: 0;
}

.preview-inner {
  max-width: 900px;
  width: 100%;
  padding: 32px 40px;
  display: flex;
  flex-direction: column;
}

.preview-page-header {
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 3px dashed var(--color-muted);
}

.preview-page-title {
  font-family: var(--font-heading);
  font-size: 32px;
  color: var(--color-heading);
  margin: 0 0 12px 0;
  font-weight: 700;
  line-height: 1.3;
  word-break: break-word;
}

.preview-page-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.preview-page-time {
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-text-muted);
}

.preview-page-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.preview-page-tag {
  padding: 3px 10px;
  background: var(--color-yellow);
  border: 2px solid var(--color-pencil);
  border-radius: 12px;
  font-size: 12px;
  font-family: var(--font-body);
  color: var(--color-pencil);
  font-weight: 600;
}

.preview-page-body {
  flex: 1;
  line-height: 1.9;
  color: var(--color-text-primary);
  font-size: 15px;
  font-family: var(--font-body);
  word-wrap: break-word;
}

.preview-page-body :deep(h1),
.preview-page-body :deep(h2),
.preview-page-body :deep(h3),
.preview-page-body :deep(h4),
.preview-page-body :deep(h5),
.preview-page-body :deep(h6) {
  font-family: var(--font-heading);
  margin-top: 32px;
  margin-bottom: 16px;
  color: var(--color-heading);
  line-height: 1.3;
  font-weight: 700;
}

.preview-page-body :deep(h1) { font-size: 26px; }
.preview-page-body :deep(h2) { font-size: 22px; }
.preview-page-body :deep(h3) { font-size: 19px; }
.preview-page-body :deep(h4) { font-size: 17px; }

.preview-page-body :deep(p) { margin: 14px 0; }

.preview-page-body :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  border: 2.5px solid var(--color-pencil);
  box-shadow: var(--shadow-hard-sm);
}

.preview-page-body :deep(table) {
  display: table;
  border-collapse: collapse;
  max-width: 100%;
  margin: 16px 0;
  width: 100%;
}

.preview-page-body :deep(td),
.preview-page-body :deep(th) {
  border: 2px solid var(--color-pencil);
  padding: 10px 14px;
  vertical-align: top;
  font-family: var(--font-body);
  font-size: 14px;
}

.preview-page-body :deep(th) {
  background: var(--color-muted);
  font-weight: 700;
  color: var(--color-heading);
}

.preview-page-body :deep(ul),
.preview-page-body :deep(ol) {
  padding-left: 28px;
  margin: 14px 0;
}

.preview-page-body :deep(li) {
  margin: 6px 0;
}

.preview-page-body :deep(blockquote) {
  border-left: 4px solid var(--color-pencil);
  padding-left: 20px;
  margin: 16px 0;
  color: var(--color-text-secondary);
  font-style: italic;
  background: var(--color-muted);
  padding-top: 12px;
  padding-bottom: 12px;
  padding-right: 16px;
  border-radius: 0 10px 10px 0;
}

.preview-page-body :deep(code) {
  background: var(--color-muted);
  padding: 2px 8px;
  border-radius: 6px;
  font-family: var(--font-mono, monospace);
  font-size: 14px;
  color: var(--color-pencil);
}

.preview-page-body :deep(pre) {
  background: var(--color-card-bg);
  padding: 16px 20px;
  border-radius: var(--radius-wobbly-sm);
  overflow-x: auto;
  margin: 16px 0;
  border: 2.5px solid var(--color-pencil);
  box-shadow: var(--shadow-hard-sm);
}

.preview-page-body :deep(pre code) {
  background: none;
  padding: 0;
  font-size: 14px;
}

.preview-page-body :deep(a) {
  color: var(--color-blue);
  text-decoration: underline;
}

.preview-page-body :deep(hr) {
  border: none;
  border-top: 3px dashed var(--color-muted);
  margin: 28px 0;
}

.preview-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 16px;
  color: var(--color-text-muted);
  font-family: var(--font-body);
  font-size: 16px;
}

.preview-empty p {
  margin: 0;
}

.edit-content :deep(.el-form-item) {
  margin-bottom: 16px;
}

.edit-content :deep(.el-form-item__label) {
  font-family: var(--font-heading);
  font-weight: 700;
  color: var(--color-pencil);
}

.markdown-editor {
  display: flex;
  gap: 12px;
  border: 2px solid var(--color-pencil);
  border-radius: var(--radius-wobbly-sm);
  overflow: hidden;
  background: var(--color-card-bg);
}

.markdown-input {
  flex: 1;
  border: none;
}

.markdown-input :deep(.el-textarea__inner) {
  border: none;
  border-radius: 0;
  resize: none;
}

.markdown-preview {
  flex: 1;
  padding: 12px;
  overflow-y: auto;
  overflow-x: hidden;
  border-left: 1px solid var(--color-muted);
  background: var(--color-content-bg);
}

/* 右栏 */
.right-panel {
  width: 360px;
  background: var(--color-card-bg);
  border-left: 1px solid var(--color-muted);
  display: flex;
  flex-direction: column;
  transition: width 0.25s ease, margin 0.25s ease;
  flex-shrink: 0;
}

.right-panel-hidden {
  width: 0;
  margin-right: -360px;
  border-left: none;
  overflow: hidden;
}

/* 响应系统主题 */
@media (prefers-color-scheme: dark) {
  .collapse-btn:hover,
  .expand-btn:hover {
    background: rgba(255, 255, 255, 0.1);
  }

  .note-item-time,
  .empty-list {
    color: #888;
  }
}
</style>