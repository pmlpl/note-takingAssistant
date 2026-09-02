<template>
  <div class="ai-generate-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="page-title">
        <el-button link class="back-btn" @click="goBack">
          <el-icon size="16"><DArrowLeft /></el-icon>
          <span>返回</span>
        </el-button>
        <h2><IconMagic :size="36" color="var(--color-green)" /> AI 笔记生成</h2>
      </div>
      <div class="page-subtitle">
        <p>输入主题和关键词，AI 将为您自动生成专业笔记</p>
      </div>
    </div>

    <el-row :gutter="20">
      <!-- 左侧：输入区 -->
      <el-col :xs="24" :lg="10">
        <el-card class="input-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <IconNotebook :size="24" />
              <span>输入信息</span>
            </div>
          </template>

          <el-form :model="form" label-width="90px">
            <el-form-item label="笔记主题" required>
              <el-input
                v-model="form.topic"
                placeholder="例如：Python基础语法、机器学习入门"
                maxlength="50"
                show-word-limit
              />
            </el-form-item>

            <el-form-item label="补充关键词">
              <el-input
                v-model="form.keyword"
                type="textarea"
                :rows="3"
                placeholder="可选，多个关键词用逗号分隔&#10;例如：变量、函数、循环、类"
                maxlength="200"
                show-word-limit
              />
            </el-form-item>

            <el-form-item label="期望字数">
              <el-slider
                v-model="form.wordCount"
                :min="300"
                :max="1500"
                :step="100"
                :marks="{
                  300: '简洁',
                  600: '标准',
                  1000: '详细',
                  1500: '深入'
                }"
                show-input
              />
            </el-form-item>

            <el-form-item label="输出格式" style="margin-top: 32px;" class="format-selector-item">
              <el-radio-group v-model="form.outputFormat" size="large" class="format-radio-group">
                <el-radio-button value="md">
                  <IconDocument :size="16" />
                  Markdown
                </el-radio-button>
                <el-radio-button value="docx">
                  <IconDocument :size="16" />
                  Word文档
                </el-radio-button>
                <el-radio-button value="txt">
                  <IconDocument :size="16" />
                  纯文本
                </el-radio-button>
              </el-radio-group>
            </el-form-item>

            <!-- 参考笔记上传 -->
            <el-form-item label="参考笔记" style="margin-top: 32px;">
              <div class="reference-section">
                <el-upload
                  v-model:file-list="noteFileList"
                  action="#"
                  :auto-upload="false"
                  :on-change="handleNoteChange"
                  :on-remove="handleNoteRemove"
                  :limit="2"
                  accept=".txt,.md,.doc,.docx,.pdf"
                  drag
                >
                  <el-icon class="el-icon--upload"><IconUpload :size="40" /></el-icon>
                  <div class="el-upload__text">
                    拖拽文件到此处或 <em>点击上传</em>
                  </div>
                  <template #tip>
                    <div class="el-upload__tip">
                      支持 TXT、MD、DOC、PDF 格式，最多2个文件
                    </div>
                  </template>
                </el-upload>
              </div>
            </el-form-item>

            <!-- 图片上传区域 -->
            <el-form-item label="参考图片">
              <div class="upload-section">
                <el-upload
                  v-model:file-list="fileList"
                  action="#"
                  list-type="picture-card"
                  :auto-upload="false"
                  :on-change="handleImageChange"
                  :on-remove="handleImageRemove"
                  :limit="3"
                  accept="image/*"
                >
                  <el-icon><IconPlus :size="20" /></el-icon>
                  <template #tip>
                    <div class="el-upload__tip">
                      最多上传3张图片，供AI参考或插入
                    </div>
                  </template>
                </el-upload>
              </div>
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                :loading="loading"
                size="large"
                class="generate-btn"
                @click="generateNote"
              >
                <IconMagic :size="18" />
                {{ loading ? "AI生成中..." : "开始生成" }}
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 右侧：结果展示区 -->
      <el-col :xs="24" :lg="14">
        <el-card class="result-card" shadow="hover">
          <template #header>
            <div class="card-header result-header">
              <div class="header-left">
                <span>✨ 生成结果</span>
                <el-radio-group v-if="noteContent" v-model="displayMode" size="small" class="display-mode-switch">
                  <el-radio-button value="rich">富文本</el-radio-button>
                  <el-radio-button value="markdown">Markdown</el-radio-button>
                </el-radio-group>
              </div>
              <div class="result-actions">
                <el-button
                  v-if="noteContent"
                  type="success"
                  :loading="saving"
                  size="default"
                  @click="saveNote"
                >
                  💾 保存到笔记
                </el-button>
                <el-button
                  v-if="noteContent"
                  size="default"
                  @click="copyContent"
                >
                  📋 复制内容
                </el-button>
                <el-button
                  v-if="noteContent"
                  type="primary"
                  size="default"
                  @click="downloadNote"
                >
                  ⬇️ 下载{{ getFormatName(form.outputFormat) }}
                </el-button>
              </div>
            </div>
          </template>
                    
          <!-- 加载中状态 -->
          <div v-if="loading && !noteContent" class="loading-state">
            <el-icon class="is-loading" :size="40"><Loading /></el-icon>
            <p>AI 正在思考中...</p>
            <p class="hint">请稍候，内容将实时显示</p>
          </div>
                    
          <!-- 内容显示区域 -->
          <div v-else-if="noteContent" class="note-content-wrapper">
            <!-- 富文本模式（默认）：统一管线渲染（含 mermaid 图表） -->
            <MarkdownContent
              v-if="displayMode === 'rich'"
              :content="rawMarkdown"
              class="note-content prose"
            />
            <!-- Markdown 原始模式 -->
            <div v-else class="note-content markdown-raw">
              <pre>{{ rawMarkdown }}</pre>
            </div>
          </div>
                    
          <!-- 空状态 -->
          <div v-else class="empty-state">
            <IconMagic :size="80" color="var(--el-text-color-disabled)" />
            <h3>等待生成</h3>
            <p>在左侧输入主题和关键词，点击“开始生成”按钮</p>
            <p class="hint">💡 提示：上传参考笔记和图片可以让 AI 更好地理解您的需求</p>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onActivated, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useNoteStore, useUserStore } from '@/store'
import { aiApi } from '@/api/ai'
import { noteApi } from '@/api/note'
import { IconMagic, IconPlus, IconUpload, IconDocument } from '@/components/icons'
import { ElMessage } from 'element-plus'
import {IconNotebook} from "@/components/icons/index.js";
import { Loading, DArrowLeft } from '@element-plus/icons-vue'
import MarkdownContent from '@/components/MarkdownContent.vue'
import { renderContentToSafeHtml } from '@/utils/htmlSanitize'

defineOptions({
  name: 'AiGenerate'
})

const router = useRouter()
const noteStore = useNoteStore()
const userStore = useUserStore()
const generateBoundUserId = ref(null)

const form = ref({
  topic: '',
  keyword: '',
  wordCount: 600,  // 默认600字
  outputFormat: 'md'  // 默认输出格式：Markdown
})

const loading = ref(false)
const saving = ref(false)
const rawMarkdown = ref('')
// 保存/复制/下载用的安全 HTML（统一管线：HTML 只消毒，Markdown 渲染后消毒）
const noteContent = computed(() => rawMarkdown.value ? renderContentToSafeHtml(rawMarkdown.value) : '')
const displayMode = ref('rich')

const STREAM_MS = Number(import.meta.env.VITE_AI_REQUEST_TIMEOUT_MS) || 600_000
let generateAbortController = null
let generateRunId = 0

// 图片上传相关（预览由 el-upload picture-card 展示，提交时再读为 Data URL）
const fileList = ref([])

// 参考笔记上传相关（列表由 el-upload 展示，提交时再读取正文）
const noteFileList = ref([])

function resetGeneratePageForNewUser() {
  form.value = {
    topic: '',
    keyword: '',
    wordCount: 600,
    outputFormat: 'md'
  }
  loading.value = false
  saving.value = false
  rawMarkdown.value = ''
  displayMode.value = 'rich'
  fileList.value = []
  noteFileList.value = []
}

function ensureGenerateSession() {
  const uid = userStore.user?.id
  if (uid == null || uid === undefined) return
  const uidNum = Number(uid)
  if (generateBoundUserId.value !== uidNum) {
    generateBoundUserId.value = uidNum
    resetGeneratePageForNewUser()
  }
}

onMounted(() => {
  ensureGenerateSession()
})

onActivated(() => {
  ensureGenerateSession()
})

onBeforeUnmount(() => {
  generateAbortController?.abort()
})

function goBack() {
  router.back()
}

function handleNoteChange(file, files) {
  if (files.length > 2) {
    ElMessage.warning('最多只能上传2个参考笔记')
    noteFileList.value = files.slice(0, 2)
  }
}

function handleNoteRemove(file, files) {
  noteFileList.value = files
}

function readFileAsText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = () => reject(reader.error)
    reader.readAsText(file)
  })
}

async function noteFileListToReferenceNotes(files) {
  const slice = files.slice(0, 2).filter((f) => f.raw)
  const out = []
  for (const f of slice) {
    const content = await readFileAsText(f.raw)
    out.push({ name: f.name, content })
  }
  return out
}

function handleImageChange(file, files) {
  if (files.length > 3) {
    ElMessage.warning('最多只能上传3张图片')
    fileList.value = files.slice(0, 3)
  }
}

function handleImageRemove(file, files) {
  fileList.value = files
}

function fileListToDataUrls(files) {
  const slice = files.slice(0, 3).filter((f) => f.raw)
  return Promise.all(
    slice.map(
      (f) =>
        new Promise((resolve, reject) => {
          const reader = new FileReader()
          reader.onload = () => resolve(reader.result)
          reader.onerror = () => reject(reader.error)
          reader.readAsDataURL(f.raw)
        })
    )
  )
}

async function generateNote() {
  if (!form.value.topic.trim()) {
    ElMessage.warning('请输入笔记主题')
    return
  }

  const runId = ++generateRunId
  loading.value = true
  rawMarkdown.value = ''

  generateAbortController?.abort()
  generateAbortController = new AbortController()
  const streamSignal = generateAbortController.signal
  const timeoutId = setTimeout(() => generateAbortController?.abort(), STREAM_MS)

  try {
    const images = await fileListToDataUrls(fileList.value)
    const referenceNotePayload = await noteFileListToReferenceNotes(noteFileList.value)
    const requestData = {
      topic: form.value.topic,
      keywords: form.value.keyword,
      wordCount: form.value.wordCount,
      images,
      referenceNotes: referenceNotePayload.map((note) => ({
        filename: note.name,
        content: note.content,
      })),
    }

    await aiApi.generateNoteStream({
      ...requestData,
      signal: streamSignal,
      onChunk: (acc) => {
        if (runId !== generateRunId) return
        rawMarkdown.value = acc
      }
    })

    if (runId !== generateRunId) return
    ElMessage.success('笔记生成成功！')
  } catch (error) {
    if (runId !== generateRunId) return
    console.error('生成笔记失败:', error)
    if (error?.name === 'AbortError' || streamSignal.aborted) {
      if (rawMarkdown.value) {
        ElMessage.warning('生成已中断（可能为超时或离开页面）')
      } else {
        ElMessage.info('已取消或超时')
      }
    } else {
      const d = error?.response?.data?.detail
      const msg = Array.isArray(d)
        ? d.map((x) => x.msg || JSON.stringify(x)).join('；')
        : d || error?.message || '生成失败'
      const s = String(msg)
      if (s.includes('503') || /密钥|ENCRYPTION|crypto/i.test(s)) {
        ElMessage.error('模型或密钥不可用，请到个人中心检查 LLM / API Key 配置')
      } else {
        ElMessage.error(typeof msg === 'string' ? msg : '生成失败，请重试')
      }
      rawMarkdown.value = ''
    }
  } finally {
    clearTimeout(timeoutId)
    if (runId === generateRunId) {
      loading.value = false
    }
  }
}

async function saveNote() {
  if (!noteContent.value) return

  saving.value = true
  try {
    // 获取文件类型标签
    const formatMap = {
      'md': 'Markdown',
      'docx': 'Word',
      'txt': '文本'
    }
    const formatTag = formatMap[form.value.outputFormat] || '文件'
    
    // 构建标签：关键词 + 文件类型 + AI生成
    let tags = `${formatTag},AI生成`
    if (form.value.keyword && form.value.keyword.trim()) {
      tags = `${form.value.keyword.trim()},${formatTag},AI生成`
    }
    
    const note = await noteApi.createNote({
      title: form.value.topic,
      content: noteContent.value,
      tags: tags,
      is_favorite: true  // AI生成的笔记直接加入"我的笔记"
    })
    noteStore.addNote(note)
    ElMessage.success('保存成功！')
    setTimeout(() => {
      router.push('/notes')
    }, 1000)
  } catch (error) {
    console.error('保存笔记失败:', error)
    ElMessage.error('保存失败，请重试')
  } finally {
    saving.value = false
  }
}

function copyContent() {
  // 根据显示模式复制内容
  let textToCopy = ''
  
  if (displayMode.value === 'markdown') {
    // Markdown 模式：复制原始 Markdown
    textToCopy = rawMarkdown.value
  } else {
    // 富文本模式：复制纯文本（去掉HTML标签）
    textToCopy = noteContent.value.replace(/<[^>]*>/g, '')
  }
  
  navigator.clipboard.writeText(textToCopy).then(() => {
    ElMessage.success('已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

// 获取格式名称
function getFormatName(format) {
  const formatMap = {
    'md': 'Markdown',
    'docx': 'Word',
    'txt': '文本'
  }
  return formatMap[format] || '文件'
}

// 下载笔记
function downloadNote() {
  if (!noteContent.value) return
  
  const format = form.value.outputFormat
  let content = noteContent.value
  let filename = `${form.value.topic || '未命名笔记'}`
  let mimeType = 'text/plain'
  
  // 根据格式处理内容
  if (format === 'md') {
    content =
      (rawMarkdown.value && rawMarkdown.value.trim()) ||
      noteContent.value.replace(/<[^>]*>/g, '')
    filename += '.md'
    mimeType = 'text/markdown'
  } else if (format === 'txt') {
    content =
      (rawMarkdown.value && rawMarkdown.value.trim()) ||
      noteContent.value.replace(/<[^>]*>/g, '')
    filename += '.txt'
    mimeType = 'text/plain'
  } else if (format === 'docx') {
    // Word 文档 - 创建简单的 HTML 格式的 doc
    content = convertToDocx(content)
    filename += '.doc'
    mimeType = 'application/msword'
  }
  
  // 创建 Blob 并下载
  const blob = new Blob([content], { type: mimeType })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
  
  ElMessage.success(`已下载 ${filename}`)
}

// 转换为 Word 格式（简单 HTML）
function convertToDocx(htmlContent) {
  // 创建一个简单的 HTML 文档，Word 可以打开
  return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body { font-family: 'Microsoft YaHei', Arial, sans-serif; line-height: 1.6; }
    h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
    h2 { color: #34495e; margin-top: 20px; }
    h3 { color: #7f8c8d; }
    code { background-color: #f4f4f4; padding: 2px 6px; border-radius: 3px; }
    pre { background-color: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }
    blockquote { border-left: 4px solid #3498db; padding-left: 15px; color: #7f8c8d; }
  </style>
</head>
<body>
${htmlContent}
</body>
</html>
  `.trim()
}
</script>

<style scoped>
.ai-generate-page {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

/* 页面头部 */
.page-header {
  display: flex;
  margin-bottom: 30px;
  position: relative;
  flex-direction: column;
  align-items: center;
}
.page-title{
}
.page-subtitle{
  text-align: center;
}
.back-btn {
  position: absolute;
  left: 0;
  top: 0;
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.back-btn:hover {
  color: var(--el-link-color);
}

.page-header h2 {
  font-size: 28px;
  color: var(--el-text-color-primary);
  margin: 0 0 10px 0;
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  padding-left: 60px;
}

.page-header p {
  font-size: 15px;
  color: var(--el-text-color-secondary);
  margin: 0;
  padding-left: 60px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  color: var(--el-text-color-primary);

}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.display-mode-switch {
  margin-left: 10px;
}

.result-actions {
  display: flex;
  gap: 10px;
}

.input-card,
.result-card,
.empty-card {
  min-height: 100%;
}

/* 参考笔记上传区域（仅 el-upload 列表，无重复展示） */
.reference-section {
  width: 100%;
}

/* 图片上传区域 */
.upload-section {
  width: 100%;
}

.generate-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
}

/* 输出格式选择器样式 */
.format-selector-item :deep(.el-form-item__label) {
  margin-right: 20px; /* 增加标签和按钮之间的距离 */
}

.format-radio-group {
  display: flex;
  gap: 0; /* 按钮之间无间距 */
}

.note-content-wrapper {
  max-height: 800px;
  overflow-y: auto;
  padding: 10px;
}

.note-content {
  line-height: 1.8;
  color: var(--el-text-color-primary);
}

.note-content :deep(h1),
.note-content :deep(h2),
.note-content :deep(h3) {
  margin-top: 20px;
  margin-bottom: 10px;
  color: var(--el-text-color-primary);
}

.note-content :deep(p) {
  margin: 10px 0;
}

.note-content :deep(ul),
.note-content :deep(ol) {
  padding-left: 20px;
  margin: 10px 0;
}

.note-content :deep(li) {
  margin: 5px 0;
}

.note-content :deep(code) {
  background: var(--el-fill-color-light);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 0.9em;
}

.note-content :deep(pre) {
  background: var(--el-fill-color-light);
  padding: 15px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 15px 0;
}

.note-content :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  margin: 15px 0;
}

/* 原始 Markdown 显示样式 */
.note-content.markdown-raw {
  background: var(--el-fill-color-light);
  padding: 20px;
  border-radius: 8px;
  overflow-x: auto;
}

.note-content.markdown-raw pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: var(--font-mono);
  font-size: 14px;
  line-height: 1.6;
  color: var(--el-text-color-primary);
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
  color: var(--el-text-color-secondary);
  margin: 100px 0;
}

.empty-state h3 {
  font-size: 20px;
  color: var(--el-text-color-regular);
  margin: 20px 0 10px 0;
}

.empty-state p {
  font-size: 14px;
  margin: 8px 0;
}

.empty-state .hint {
  color: var(--color-blue);
  font-style: italic;
}

/* 加载状态 */
.loading-state {
  text-align: center;
  padding: 80px 20px;
  color: var(--el-text-color-secondary);
}

.loading-state p {
  margin: 15px 0;
  font-size: 16px;
}

.loading-state .hint {
  font-size: 14px;
  color: var(--color-blue);
}

/* 响应式 */
@media (max-width: 768px) {
  .ai-generate-page {
    padding: 15px;
  }

  .page-header h2,
  .page-header p {
    padding-left: 0;
  }

  .back-btn {
    position: static;
    margin-bottom: 10px;
  }
}
</style>

