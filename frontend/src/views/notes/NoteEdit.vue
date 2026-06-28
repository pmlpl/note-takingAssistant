<template>
    <div class="note-edit-container">
      <div class="edit-header">
        <el-button @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <h2>{{ isEdit ? '编辑笔记' : '新建笔记' }}</h2>
        <div class="header-actions">
          <el-radio-group v-model="editorMode" size="small">
            <el-radio-button value="rich">富文本</el-radio-button>
            <el-radio-button value="markdown">Markdown</el-radio-button>
          </el-radio-group>
          <el-button type="primary" @click="saveNote" :loading="saving">
            <IconUpload :size="18" />
            保存
          </el-button>
        </div>
      </div>
      <el-card>
        <el-form :model="form" label-width="80px">
          <el-form-item label="标题" prop="title" :rules="[{ required: true, message: '请输入标题' }]">
            <el-input v-model="form.title" placeholder="请输入笔记标题" />
          </el-form-item>
          <el-form-item label="标签">
            <el-input v-model="form.tags" placeholder="多个标签用逗号分隔" />
          </el-form-item>
          <el-form-item label="内容">
            <!-- 富文本编辑器模式 -->
            <RichText v-if="editorMode === 'rich'" v-model="form.content" />
            <!-- Markdown/HTML 编辑器模式 -->
            <div v-else class="markdown-editor">
              <el-input
                v-model="form.content"
                type="textarea"
                :rows="20"
                placeholder="支持 Markdown 或 HTML 语法..."
                class="markdown-input"
              />
              <!-- 渲染预览（支持 HTML 和 Markdown） -->
              <div class="markdown-preview" v-html="renderedContent"></div>
            </div>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onActivated, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useNoteStore, useUserStore } from '@/store'
import { noteApi } from '@/api/note'
import RichText from '@/components/RichText.vue'
import { IconUpload } from '@/components/icons'
import { sanitizeHtml, renderMarkdownToSafeHtml } from '@/utils/htmlSanitize'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'

defineOptions({
  name: 'NoteEdit'
})
const route = useRoute()
const router = useRouter()
const noteStore = useNoteStore()
const userStore = useUserStore()
const editBoundUserId = ref(null)

const isEdit = ref(false)
const saving = ref(false)
const editorMode = ref('rich') // 默认使用 rich 编辑器

const form = ref({
  title: '',
  tags: '',
  content: ''
})

// 渲染内容预览（支持 HTML 和 Markdown）
const renderedContent = computed(() => {
  if (!form.value.content) return ''
  
  // 检测是否是 HTML 格式（包含 HTML 标签）
  const isHtml = /<[a-z][\s\S]*>/i.test(form.value.content)
  
  if (isHtml) {
    return sanitizeHtml(form.value.content)
  }
  return renderMarkdownToSafeHtml(form.value.content)
})
// 监听路由参数变化，当ID改变时重新加载笔记
watch(() => route.params.id, async (newId, oldId) => {
  if (newId && newId !== oldId) {
    // ID发生变化，重新加载笔记
    isEdit.value = true
    await loadNote(newId)
  } else if (!newId) {
    // 新建笔记模式
    isEdit.value = false
    form.value = {
      title: '',
      tags: '',
      content: ''
    }
  }
}, { immediate: false })

async function hydrateNoteEditForRoute() {
  const noteId = route.params.id
  if (noteId) {
    isEdit.value = true
    await loadNote(noteId)
  } else {
    isEdit.value = false
    form.value = {
      title: '',
      tags: '',
      content: ''
    }
  }
}

onMounted(async () => {
  const uid = userStore.user?.id
  if (uid != null && uid !== undefined) {
    editBoundUserId.value = Number(uid)
  }
  await hydrateNoteEditForRoute()
})

onActivated(async () => {
  const uid = userStore.user?.id
  if (uid == null || uid === undefined) return
  const uidNum = Number(uid)
  if (editBoundUserId.value !== uidNum) {
    editBoundUserId.value = uidNum
    await hydrateNoteEditForRoute()
  }
})

async function loadNote(id) {
  try {
    const note = await noteApi.getNote(id)
    
    // 直接使用后端返回的原始内容，不做任何转换
    // 富文本编辑器会自己处理 HTML/Markdown 格式
    let content = note.content || ''
    // 检测是否是 Markdown 格式（不包含 HTML 标签）
    const isHtml = /<[a-z][\s\S]*>/i.test(content)
    // 如果不是 HTML 格式，则认为是 Markdown，转换为 HTML
    if (!isHtml && content.trim()) {
      content = renderMarkdownToSafeHtml(content)
    } else if (isHtml && content.trim()) {
      content = sanitizeHtml(content)
    }

    form.value = {
      title: note.title || '',
      tags: note.tags || '',
      content: content
    }
  }catch (error) {
    ElMessage.error('加载笔记失败')
  }
}

async function saveNote() {
  if (!form.value.title.trim()) return
  
  saving.value = true
  try {
    if (isEdit.value) {
      await noteApi.updateNote(route.params.id, form.value)
      noteStore.updateNote(route.params.id, form.value)
    } else {
      const note = await noteApi.createNote({
        ...form.value,
        is_favorite: true,
      })
      noteStore.addNote(note)
    }
    router.push('/notes')
  } catch (error) {
    console.error('保存笔记失败:', error)
  } finally {
    saving.value = false
  }
}

function goBack() {
  router.push('/notes')
}
</script>

<style scoped>
.note-edit-container {
  box-sizing: border-box;
  width: 100%;
  max-width: 1200px;
  margin: 20px auto;
  padding: 20px 24px;
}

.note-edit-container :deep(.el-form-item__content) {
  flex: 1;
  min-width: 0;
  max-width: 100%;
}

.note-edit-container :deep(.el-card__body) {
  overflow-x: hidden;
}

.edit-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
}

.edit-header h2 {
  flex: 1;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

/* Markdown 编辑器样式 */
.markdown-editor {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  min-height: 400px;
}

.markdown-input {
  height: 600px;
}

.markdown-input :deep(textarea) {
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.6;
  resize: none;
  height: 100%;
}

.markdown-preview {
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 16px;
  background-color: #fafafa;
  overflow-y: auto;
  max-height: 600px;
  line-height: 1.6;
}

.markdown-preview :deep(h1),
.markdown-preview :deep(h2),
.markdown-preview :deep(h3),
.markdown-preview :deep(h4),
.markdown-preview :deep(h5),
.markdown-preview :deep(h6) {
  margin: 12px 0 8px;
  font-weight: 600;
}

.markdown-preview :deep(h1) { font-size: 1.8em; }
.markdown-preview :deep(h2) { font-size: 1.5em; }
.markdown-preview :deep(h3) { font-size: 1.3em; }

.markdown-preview :deep(p) {
  margin: 8px 0;
}

.markdown-preview :deep(code) {
  background-color: #f0f0f0;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
}

.markdown-preview :deep(pre) {
  background-color: #f0f0f0;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
  margin: 12px 0;
}

.markdown-preview :deep(pre code) {
  background-color: transparent;
  padding: 0;
}

.markdown-preview :deep(blockquote) {
  border-left: 4px solid #409eff;
  padding-left: 16px;
  margin: 12px 0;
  color: #606266;
  font-style: italic;
}

.markdown-preview :deep(ul),
.markdown-preview :deep(ol) {
  margin: 12px 0;
  padding-left: 24px;
}

.markdown-preview :deep(li) {
  margin: 6px 0;
}

.markdown-preview :deep(a) {
  color: #409eff;
  text-decoration: none;
}

.markdown-preview :deep(a:hover) {
  text-decoration: underline;
}

.markdown-preview :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
}

.markdown-preview :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
}

.markdown-preview :deep(th),
.markdown-preview :deep(td) {
  border: 1px solid #e4e7ed;
  padding: 8px 12px;
  text-align: left;
}

.markdown-preview :deep(th) {
  background-color: #f5f7fa;
  font-weight: 600;
}
</style>