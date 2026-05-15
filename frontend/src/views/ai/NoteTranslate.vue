<template>
  <Layout>
    <div class="note-translate-page">
      <header class="page-header">
        <el-button link class="back-btn" @click="goBack">
          <el-icon size="16"><DArrowLeft /></el-icon>
          <span>返回</span>
        </el-button>
        <h2 class="page-heading">
          <IconTranslate :size="36" color="#409eff" />
          翻译笔记
        </h2>
        <p class="page-subtitle">
          左侧载入原文、右侧查看译文；中间选择语言并翻译。单次最多 {{ maxChars }} 字符，译文带「笔记助手」水印。
        </p>
      </header>

      <div class="translate-workspace">
        <el-row :gutter="20" class="translate-row">
          <!-- 原文 -->
          <el-col :xs="24" :lg="10">
            <section class="translate-panel">
              <div class="panel-head">
                <span class="panel-label panel-label--source">原文</span>
                <span class="panel-hint">富文本 / Markdown 预览</span>
              </div>
              <div class="panel-body">
                <div class="source-toolbar">
                  <el-upload
                    class="toolbar-upload"
                    action="#"
                    :auto-upload="false"
                    :show-file-list="false"
                    accept=".md,.txt,.docx"
                    :on-change="handleFileUpload"
                  >
                    <el-button plain>
                      <IconUpload :size="16" /> 上传文件
                    </el-button>
                  </el-upload>
                  <el-select
                    v-model="form.noteId"
                    clearable
                    filterable
                    placeholder="从我的笔记选择"
                    class="toolbar-select"
                    @change="onNotePick"
                  >
                    <el-option
                      v-for="n in notes"
                      :key="n.id"
                      :label="n.title"
                      :value="n.id"
                    />
                  </el-select>
                </div>
                <p class="toolbar-tip">支持 .md / .txt 直接填入；.docx 导入为笔记后填入</p>

                <div class="doc-preview">
                  <div v-if="!effectiveSource" class="doc-preview-empty">
                    <IconTranslate :size="40" color="#dcdfe6" />
                    <p>上传、选择笔记或在下方编辑原文</p>
                  </div>
                  <div
                    v-else
                    class="preview-body source-preview-body"
                    v-html="sourcePreviewHtml"
                  />
                </div>

                <el-collapse v-model="sourceEditOpen" class="source-edit-collapse">
                  <el-collapse-item title="编辑原文（发送给翻译接口）" name="1">
                    <el-input
                      v-model="form.sourceText"
                      type="textarea"
                      :rows="6"
                      placeholder="粘贴 Markdown、HTML 或纯文本"
                      maxlength="50000"
                      show-word-limit
                    />
                  </el-collapse-item>
                </el-collapse>
                <p v-if="truncationHint" class="hint">{{ truncationHint }}</p>
              </div>
            </section>
          </el-col>

          <!-- 翻译枢纽 -->
          <el-col :xs="24" :lg="4" class="hub-col">
            <div class="translate-hub">
              <div class="hub-line hub-line--left" aria-hidden="true" />
              <div class="hub-card">
                <div class="hub-icon-wrap">
                  <IconTranslate :size="28" color="#409eff" />
                </div>
                <p class="hub-title">翻译为</p>
                <el-select v-model="form.targetLang" class="hub-select" size="large">
                  <el-option
                    v-for="opt in langOptions"
                    :key="opt.value"
                    :label="opt.label"
                    :value="opt.value"
                  />
                </el-select>
                <el-button
                  type="primary"
                  size="large"
                  class="hub-btn"
                  :loading="loading"
                  :disabled="!canTranslate"
                  @click="runTranslate"
                >
                  {{ loading ? '翻译中…' : '开始翻译' }}
                </el-button>
                <p v-if="!canTranslate" class="hub-tip">请先载入原文</p>
              </div>
              <div class="hub-line hub-line--right" aria-hidden="true" />
            </div>
          </el-col>

          <!-- 译文 -->
          <el-col :xs="24" :lg="10">
            <section class="translate-panel translate-panel--result">
              <div class="panel-head">
                <span class="panel-label panel-label--target">译文</span>
                <el-button
                  v-if="translatedRaw"
                  size="small"
                  plain
                  type="primary"
                  @click="copyTranslation"
                >
                  复制全文
                </el-button>
              </div>
              <div class="panel-body panel-body--result">
                <div v-if="!translatedRaw" class="doc-preview doc-preview--empty">
                  <IconTranslate :size="40" color="#dcdfe6" />
                  <p>翻译结果将显示在这里</p>
                </div>
                <div v-else class="doc-preview doc-preview--filled">
                  <div class="result-wrap">
                    <div class="watermark-layer" aria-hidden="true">
                      <span v-for="i in 8" :key="i" class="watermark-tile">笔记助手</span>
                    </div>
                    <div
                      class="preview-body translated-body"
                      v-html="translatedPreviewHtml"
                    />
                  </div>
                </div>
              </div>
            </section>
          </el-col>
        </el-row>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted, onActivated } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store'
import Layout from '@/components/Layout.vue'
import { IconTranslate, IconUpload } from '@/components/icons'
import { DArrowLeft } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { noteApi } from '@/api/note'
import { aiApi } from '@/api/ai'
import {
  isLikelyHtmlContent,
  sanitizeHtml,
  renderMarkdownToSafeHtml
} from '@/utils/htmlSanitize'

defineOptions({ name: 'NoteTranslate' })

const router = useRouter()
const userStore = useUserStore()
const translateBoundUserId = ref(null)
const maxChars = 8000
const notes = ref([])
const loading = ref(false)
const translatedRaw = ref('')
const translatedFormat = ref('markdown')
const sourceEditOpen = ref([])

const langOptions = [
  { value: 'zh', label: '简体中文' },
  { value: 'en', label: 'English' },
  { value: 'ja', label: 'Japanese（日语）' },
  { value: 'ko', label: 'Korean（韩语）' },
  { value: 'fr', label: 'French（法语）' },
  { value: 'es', label: 'Spanish（西班牙语）' }
]

const form = ref({
  noteId: null,
  sourceText: '',
  targetLang: 'en'
})

const effectiveSource = computed(() => {
  return (form.value.sourceText || '').trim()
})

const truncationHint = computed(() => {
  const len = form.value.sourceText.length
  if (len > maxChars) {
    return `原文 ${len} 字符，将仅翻译前 ${maxChars} 字符。`
  }
  return ''
})

const canTranslate = computed(() => effectiveSource.value.length > 0)

const sourcePreviewHtml = computed(() => {
  const t = form.value.sourceText || ''
  if (!t.trim()) return ''
  if (isLikelyHtmlContent(t)) return sanitizeHtml(t)
  return renderMarkdownToSafeHtml(t)
})

const translatedPreviewHtml = computed(() => {
  if (!translatedRaw.value) return ''
  const asHtml =
    translatedFormat.value === 'html' || isLikelyHtmlContent(translatedRaw.value)
  if (asHtml) return sanitizeHtml(translatedRaw.value)
  return renderMarkdownToSafeHtml(translatedRaw.value)
})

onMounted(() => {
  void refreshTranslateSession()
})

onActivated(() => {
  void refreshTranslateSession()
})

async function refreshTranslateSession() {
  const uid = userStore.user?.id
  if (uid == null || uid === undefined) return
  const uidNum = Number(uid)
  if (translateBoundUserId.value !== uidNum) {
    translateBoundUserId.value = uidNum
    form.value = {
      noteId: null,
      sourceText: '',
      targetLang: 'en'
    }
    translatedRaw.value = ''
    translatedFormat.value = 'markdown'
    sourceEditOpen.value = []
    loading.value = false
  }
  await loadNotes()
}

async function loadNotes() {
  try {
    notes.value = await noteApi.getNotes()
  } catch (e) {
    console.error(e)
    ElMessage.error('加载笔记列表失败')
  }
}

function goBack() {
  router.back()
}

async function applyImportedNote(created) {
  form.value.sourceText = created.content || ''
  form.value.noteId = created.id ?? null
  await loadNotes()
  ElMessage.success('导入成功，已填入原文')
}

async function handleFileUpload(uploadFile) {
  const raw = uploadFile?.raw
  if (!raw) return
  const name = (raw.name || '').toLowerCase()
  if (name.endsWith('.md') || name.endsWith('.txt')) {
    const reader = new FileReader()
    reader.onload = () => {
      form.value.sourceText = String(reader.result || '')
      form.value.noteId = null
      ElMessage.success('已载入文件')
    }
    reader.onerror = () => ElMessage.error('读取文件失败')
    reader.readAsText(raw, 'UTF-8')
    return
  }
  if (name.endsWith('.docx')) {
    try {
      const created = await noteApi.importNote(raw)
      await applyImportedNote(created)
    } catch (e) {
      if (e?.response?.status === 409) {
        const detail =
          e?.response?.data?.detail ||
          '已存在同名笔记，覆盖将替换数据库中的该笔记内容。'
        try {
          await ElMessageBox.confirm(detail, '导入冲突', {
            type: 'warning',
            confirmButtonText: '覆盖导入',
            cancelButtonText: '取消'
          })
        } catch {
          return
        }
        try {
          const created = await noteApi.importNote(raw, { overwrite: true })
          await applyImportedNote(created)
        } catch (e2) {
          console.error(e2)
          const d2 = e2?.response?.data?.detail
          ElMessage.error(
            typeof d2 === 'string' ? d2 : e2?.message || '覆盖导入失败'
          )
        }
      } else {
        console.error(e)
        const d = e?.response?.data?.detail
        ElMessage.error(typeof d === 'string' ? d : e?.message || '导入失败')
      }
    }
    return
  }
  ElMessage.warning('仅支持 .md、.txt、.docx 文件')
}

async function onNotePick(noteId) {
  if (!noteId) return
  try {
    const note = await noteApi.getNote(noteId)
    form.value.sourceText = note.content || ''
    ElMessage.success('已载入笔记')
  } catch (e) {
    console.error(e)
    ElMessage.error('获取笔记失败')
  }
}

async function runTranslate() {
  if (!canTranslate.value) {
    ElMessage.warning('请先输入或选择原文')
    return
  }
  loading.value = true
  translatedRaw.value = ''
  translatedFormat.value = 'markdown'
  try {
    const content = form.value.sourceText.slice(0, maxChars)
    const res = await aiApi.translateNote({
      content,
      targetLang: form.value.targetLang
    })
    const payload = res?.data
    translatedRaw.value = (payload && payload.content) || ''
    translatedFormat.value =
      payload?.contentFormat === 'html' ? 'html' : 'markdown'
    if (payload?.truncated) {
      ElMessage.warning('原文过长，已按上限截断后翻译')
    }
    ElMessage.success('翻译完成')
  } catch (e) {
    const d = e?.response?.data?.detail
    const msg = Array.isArray(d)
      ? d.map((x) => x.msg || JSON.stringify(x)).join('；')
      : d || e?.message || '翻译失败'
    const s = String(msg)
    if (s.includes('503') || /密钥|ENCRYPTION|crypto/i.test(s)) {
      ElMessage.error('模型或密钥不可用，请到个人中心检查 LLM / API Key 配置')
    } else {
      ElMessage.error(typeof msg === 'string' ? msg : '翻译失败，请重试')
    }
  } finally {
    loading.value = false
  }
}

async function copyTranslation() {
  try {
    await navigator.clipboard.writeText(translatedRaw.value)
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败，请手动选择文本复制')
  }
}
</script>

<style scoped>
.note-translate-page {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

/* ---------- 页头（与 AI 总结页一致） ---------- */
.page-header {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 28px;
}

.back-btn {
  position: absolute;
  left: 0;
  top: 0;
  font-size: 14px;
  color: #606266;
}

.back-btn:hover {
  color: #409eff;
}

.page-heading {
  margin: 0 0 10px;
  padding-left: 60px;
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 10px;
}

.page-subtitle {
  margin: 0;
  padding-left: 60px;
  font-size: 15px;
  color: #909399;
  text-align: center;
  max-width: 640px;
  line-height: 1.6;
}

/* ---------- 工作区 ---------- */
.translate-workspace {
  background: #f5f7fa;
  border-radius: 16px;
  padding: 20px;
  border: 1px solid #ebeef5;
}

.translate-row {
  align-items: stretch;
}

/* ---------- 左右面板（统一卡片） ---------- */
.translate-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 520px;
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e4e7ed;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid #ebeef5;
  background: #fafbfc;
  flex-shrink: 0;
}

.panel-label {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  padding-left: 10px;
  border-left: 3px solid #dcdfe6;
}

.panel-label--source {
  border-left-color: #909399;
}

.panel-label--target {
  border-left-color: #409eff;
}

.panel-hint {
  font-size: 12px;
  color: #909399;
}

.panel-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px 20px 20px;
  min-height: 0;
}

.panel-body--result {
  padding-top: 12px;
  flex: 1;
  min-height: 0;
}

.doc-preview--empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  min-height: min(62vh, 640px);
  color: #909399;
  font-size: 14px;
}

.doc-preview--empty p {
  margin: 0;
  color: #909399;
  text-align: center;
}

/* ---------- 原文工具栏 ---------- */
.source-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.toolbar-upload {
  flex-shrink: 0;
}

.toolbar-select {
  flex: 1;
  min-width: 160px;
}

.toolbar-tip {
  margin: 8px 0 12px;
  font-size: 12px;
  color: #a8abb2;
  line-height: 1.5;
}

/* ---------- 预览区（左右共用） ---------- */
.doc-preview {
  flex: 1;
  min-height: 280px;
  max-height: min(62vh, 640px);
  border: 1px solid #e4e7ed;
  border-radius: 10px;
  background: #fff;
  overflow: auto;
}

.doc-preview-empty {
  height: 100%;
  min-height: 240px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #909399;
  font-size: 14px;
  padding: 24px;
}

.doc-preview-empty p {
  margin: 0;
}

.doc-preview--filled {
  position: relative;
  border: none;
  background: transparent;
  overflow: visible;
  max-height: none;
}

.doc-preview--filled .result-wrap {
  border: 1px solid #e4e7ed;
  border-radius: 10px;
  background: #fff;
  max-height: min(62vh, 640px);
  overflow: auto;
}

.source-preview-body {
  padding: 16px 20px 24px;
  line-height: 1.8;
  color: #303133;
  font-size: 15px;
}

.source-edit-collapse {
  margin-top: 12px;
  flex-shrink: 0;
}

.source-edit-collapse :deep(.el-collapse-item__header) {
  font-size: 13px;
  color: #606266;
}

.hint {
  margin: 8px 0 0;
  font-size: 12px;
  color: #e6a23c;
}

/* ---------- 中间枢纽 ---------- */
.hub-col {
  display: flex;
  align-items: center;
  justify-content: center;
}

.translate-hub {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 320px;
  padding: 16px 0;
}

.hub-line {
  display: none;
}

.hub-card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 200px;
  padding: 24px 18px;
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e4e7ed;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  text-align: center;
}

.hub-icon-wrap {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: #ecf5ff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hub-title {
  margin: 0;
  font-size: 13px;
  color: #909399;
  letter-spacing: 0.05em;
}

.hub-select {
  width: 100%;
}

.hub-btn {
  width: 100%;
  height: 44px;
  font-size: 15px;
  font-weight: 500;
}

.hub-tip {
  margin: 0;
  font-size: 12px;
  color: #c0c4cc;
  line-height: 1.4;
}

/* 大屏：左右连接线 */
@media (min-width: 992px) {
  .translate-hub {
    min-height: 100%;
  }

  .hub-line {
    display: block;
    position: absolute;
    top: 50%;
    height: 2px;
    width: calc(50% - 108px);
    margin-top: -1px;
    background: linear-gradient(90deg, #dcdfe6, #c6e2ff);
    pointer-events: none;
  }

  .hub-line--left {
    left: 0;
    background: linear-gradient(90deg, transparent, #c6e2ff);
  }

  .hub-line--right {
    right: 0;
    background: linear-gradient(270deg, transparent, #c6e2ff);
  }
}

@media (max-width: 991px) {
  .translate-panel {
    min-height: auto;
  }

  .hub-col {
    padding: 8px 0 16px;
  }

  .translate-hub {
    min-height: auto;
  }

  .hub-card {
    max-width: 320px;
  }

  .page-heading,
  .page-subtitle {
    padding-left: 0;
    text-align: center;
  }

  .back-btn {
    position: static;
    align-self: flex-start;
    margin-bottom: 8px;
  }
}

/* ---------- 富文本 / 水印 ---------- */
.source-preview-body :deep(img),
.translated-body :deep(img) {
  max-width: 100%;
  height: auto;
}

.source-preview-body :deep(table),
.translated-body :deep(table) {
  border-collapse: collapse;
  max-width: 100%;
}

.source-preview-body :deep(td),
.source-preview-body :deep(th),
.translated-body :deep(td),
.translated-body :deep(th) {
  border: 1px solid #e4e7ed;
  padding: 6px 10px;
}

.result-wrap {
  position: relative;
  min-height: 200px;
}

.watermark-layer {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  align-content: flex-start;
  justify-content: space-around;
  gap: 40px 28px;
  padding: 20px;
  opacity: 0.1;
  font-size: 20px;
  font-weight: 700;
  color: #409eff;
  transform: rotate(-18deg);
  user-select: none;
}

.watermark-tile {
  white-space: nowrap;
}

.preview-body {
  position: relative;
  z-index: 2;
  line-height: 1.8;
  color: #303133;
  font-size: 15px;
}

.translated-body {
  padding: 16px 20px 24px;
}

.preview-body :deep(h1),
.preview-body :deep(h2),
.preview-body :deep(h3) {
  margin-top: 24px;
  margin-bottom: 12px;
  color: #303133;
}

.preview-body :deep(p) {
  margin: 12px 0;
}

.preview-body :deep(pre) {
  overflow-x: auto;
}

.doc-preview::-webkit-scrollbar,
.result-wrap::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.doc-preview::-webkit-scrollbar-thumb,
.result-wrap::-webkit-scrollbar-thumb {
  background: rgba(144, 147, 153, 0.35);
  border-radius: 4px;
}

.doc-preview:hover::-webkit-scrollbar-thumb,
.result-wrap:hover::-webkit-scrollbar-thumb {
  background: rgba(144, 147, 153, 0.6);
}
</style>
