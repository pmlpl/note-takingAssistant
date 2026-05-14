<template>
  <Layout>
    <div class="mindmap-page">
      <div class="page-header">
        <h2>
          <IconMindmap :size="32" color="#4facfe" />
          思维导图（Mermaid）
        </h2>
        <p class="subtitle">
          在左侧粘贴或编写 Mermaid 源码，点击「渲染预览」在右侧查看流程图。可从 AI 助手回复中复制 fenced 代码块（以
          mermaid 为语言标记）中的内容。
        </p>
      </div>

      <el-row :gutter="20" class="split-row">
        <el-col :xs="24" :lg="10">
          <el-card shadow="hover" class="panel-card">
            <template #header>
              <span>源代码</span>
            </template>
            <el-input
              v-model="source"
              type="textarea"
              :autosize="{ minRows: 18, maxRows: 32 }"
              placeholder="在此粘贴 Mermaid，例如：&#10;flowchart TD&#10;    A[开始] --> B[结束]"
              class="source-input"
              spellcheck="false"
            />
            <div class="toolbar">
              <el-button type="primary" @click="renderPreview">渲染预览</el-button>
              <el-button @click="clearAll">清空</el-button>
              <el-button @click="pasteFromClipboard">从剪贴板粘贴</el-button>
            </div>
          </el-card>
        </el-col>

        <el-col :xs="24" :lg="14">
          <el-card shadow="hover" class="panel-card preview-card">
            <template #header>
              <span>预览</span>
            </template>
            <el-alert
              v-if="parseError"
              type="error"
              :closable="false"
              :title="parseError"
              class="error-alert"
            />
            <div ref="previewHost" class="preview-host" />
          </el-card>
        </el-col>
      </el-row>
    </div>
  </Layout>
</template>

<script setup>
import { ref, watch, onMounted, nextTick } from 'vue'
import mermaid from 'mermaid'
import { ElMessage } from 'element-plus'
import Layout from '@/components/Layout.vue'
import { IconMindmap } from '@/components/icons'

const STORAGE_KEY = 'mindmap_mermaid_source'

const DEFAULT_SAMPLE = `flowchart TD
    A[开始] --> B{判断}
    B -->|是| C[结果1]
    B -->|否| D[结果2]`

const source = ref('')
const previewHost = ref(null)
const parseError = ref('')
let mermaidReady = false

function initMermaid() {
  if (mermaidReady) return
  mermaid.initialize({
    startOnLoad: false,
    securityLevel: 'strict',
    theme: 'neutral'
  })
  mermaidReady = true
}

function showPlaceholder() {
  const el = previewHost.value
  if (!el) return
  el.innerHTML = '<p class="preview-placeholder">在左侧输入 Mermaid 后点击「渲染预览」</p>'
}

async function renderPreview() {
  parseError.value = ''
  const el = previewHost.value
  if (!el) return

  initMermaid()
  el.innerHTML = ''

  const text = source.value.trim()
  if (!text) {
    showPlaceholder()
    return
  }

  try {
    await mermaid.parse(text)
  } catch (e) {
    parseError.value = e?.message || String(e)
    showPlaceholder()
    return
  }

  try {
    const id = `mmd-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`
    const { svg, bindFunctions } = await mermaid.render(id, text)
    el.innerHTML = svg
    bindFunctions?.(el)
  } catch (e) {
    parseError.value = e?.message || String(e)
    showPlaceholder()
  }
}

function clearAll() {
  source.value = ''
  parseError.value = ''
  localStorage.removeItem(STORAGE_KEY)
  showPlaceholder()
}

async function pasteFromClipboard() {
  try {
    const text = await navigator.clipboard.readText()
    source.value = text
    ElMessage.success('已从剪贴板粘贴')
    await nextTick()
    await renderPreview()
  } catch {
    ElMessage.warning('无法读取剪贴板，请手动粘贴（浏览器需 localhost 或 HTTPS）')
  }
}

let saveTimer = null
watch(source, () => {
  clearTimeout(saveTimer)
  saveTimer = setTimeout(() => {
    localStorage.setItem(STORAGE_KEY, source.value)
  }, 500)
})

onMounted(() => {
  initMermaid()
  const saved = localStorage.getItem(STORAGE_KEY)
  source.value = saved != null && saved !== '' ? saved : DEFAULT_SAMPLE
  nextTick(() => {
    renderPreview()
  })
})
</script>

<style scoped>
.mindmap-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 16px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0 0 8px;
  font-size: 1.35rem;
}

.subtitle {
  margin: 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
}

.subtitle code {
  padding: 0 4px;
  background: #f4f4f5;
  border-radius: 4px;
  font-size: 13px;
}

.split-row {
  align-items: stretch;
}

.panel-card {
  height: 100%;
  min-height: 420px;
}

.source-input :deep(textarea) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 13px;
}

.toolbar {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.preview-card :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  min-height: 360px;
}

.error-alert {
  margin-bottom: 12px;
  flex-shrink: 0;
}

.preview-host {
  flex: 1;
  overflow: auto;
  min-height: 280px;
  padding: 8px;
  background: #fafafa;
  border-radius: 8px;
}

.preview-host :deep(svg) {
  max-width: 100%;
  height: auto;
}

.preview-placeholder {
  margin: 0;
  color: #909399;
  font-size: 14px;
}
</style>
