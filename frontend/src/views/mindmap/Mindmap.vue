<template>
  <Layout>
    <div class="mindmap-page">
      <div class="page-header">
        <h2>
          <IconMindmap :size="32" color="#4facfe" />
          思维导图（Mermaid）
        </h2>
        <p class="subtitle">
          在左侧粘贴或编写 Mermaid 源码，点击「渲染预览」在右侧查看。从首页 AI
          助手某条回复下点击「在思维导图页预览」时，会通过内存与本地存储传入源码并自动渲染；若预览失败，请检查回复中是否包含
          <code>flowchart</code> / <code>mindmap</code> 等 Mermaid 语法。
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
              <div class="preview-card-header">
                <span>预览</span>
                <el-button
                  type="primary"
                  plain
                  size="small"
                  :loading="savingPreviewPng"
                  @click="savePreviewAsPng"
                >
                  保存为 PNG
                </el-button>
              </div>
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
import { ElMessage } from 'element-plus'
import Layout from '@/components/Layout.vue'
import { IconMindmap } from '@/components/icons'
import {
  MINDMAP_LOCAL_STORAGE_KEY,
  MINDMAP_PENDING_SESSION_KEY,
  takeMindmapNavBridgeSource,
  prepareMermaidSourceForRender
} from '@/utils/common'

const DEFAULT_SAMPLE = `flowchart TD
    A[开始] --> B{判断}
    B -->|是| C[结果1]
    B -->|否| D[结果2]`

const source = ref('')
const previewHost = ref(null)
const parseError = ref('')
const savingPreviewPng = ref(false)
let mermaidReady = false
let mermaidApi = null

async function getMermaid() {
  if (!mermaidApi) {
    const mod = await import('mermaid')
    mermaidApi = mod.default
  }
  return mermaidApi
}

/** 将预览区内的 Mermaid SVG 导出为 PNG（白底、2× 像素密度） */
async function savePreviewAsPng() {
  const host = previewHost.value
  const svg = host?.querySelector('svg')
  if (!svg) {
    ElMessage.warning('请先点击「渲染预览」生成图形后再保存')
    return
  }
  savingPreviewPng.value = true
  try {
    await exportSvgToPngWithCanvg(svg, `思维导图_${Date.now()}.png`)
    ElMessage.success('已保存为 PNG')
  } catch (e) {
    ElMessage.error(e?.message || '导出图片失败，请重试')
  } finally {
    savingPreviewPng.value = false
  }
}

/**
 * 使用 canvg 将 SVG 矢量绘制到 Canvas，避免 Image+Blob 解码时因外链/字体等导致画布污染（toBlob 报 Tainted）。
 * @param {SVGSVGElement} svgEl
 * @param {string} filename
 */
async function exportSvgToPngWithCanvg(svgEl, filename) {
  const { Canvg } = await import('canvg')
  const bbox = svgEl.getBBox()
  if (!bbox.width || !bbox.height) {
    throw new Error('图形尺寸为空，无法导出')
  }
  const pad = 24
  const vbW = bbox.width + pad * 2
  const vbH = bbox.height + pad * 2
  const vx = bbox.x - pad
  const vy = bbox.y - pad
  const scale = 2
  const outW = Math.ceil(vbW * scale)
  const outH = Math.ceil(vbH * scale)

  const clone = /** @type {SVGSVGElement} */ (svgEl.cloneNode(true))
  clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
  if (!clone.getAttribute('xmlns:xlink')) {
    clone.setAttribute('xmlns:xlink', 'http://www.w3.org/1999/xlink')
  }
  clone.setAttribute('viewBox', `${vx} ${vy} ${vbW} ${vbH}`)
  clone.setAttribute('width', String(outW))
  clone.setAttribute('height', String(outH))
  clone.removeAttribute('style')

  const xml = new XMLSerializer().serializeToString(clone)
  const canvas = document.createElement('canvas')
  canvas.width = outW
  canvas.height = outH
  const ctx = canvas.getContext('2d')
  if (!ctx) {
    throw new Error('浏览器不支持 Canvas')
  }
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, outW, outH)

  const canvg = Canvg.fromString(ctx, xml, {
    ignoreMouse: true,
    ignoreAnimation: true
  })
  await canvg.render()

  await new Promise((resolve, reject) => {
    try {
      canvas.toBlob(
        (blob) => {
          if (!blob) {
            reject(new Error('生成 PNG 失败'))
            return
          }
          const a = document.createElement('a')
          a.download = filename
          const pngUrl = URL.createObjectURL(blob)
          a.href = pngUrl
          a.rel = 'noopener'
          a.click()
          setTimeout(() => URL.revokeObjectURL(pngUrl), 2000)
          resolve()
        },
        'image/png',
        1
      )
    } catch (e) {
      reject(e)
    }
  })
}

async function initMermaid() {
  if (mermaidReady) return
  const mermaid = await getMermaid()
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

  await initMermaid()
  const mermaid = await getMermaid()
  el.innerHTML = ''

  const raw = source.value.trim()
  let text = prepareMermaidSourceForRender(raw)
  if (text !== raw) {
    source.value = text
    await nextTick()
    text = source.value.trim()
  }

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
  localStorage.removeItem(MINDMAP_LOCAL_STORAGE_KEY)
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
    localStorage.setItem(MINDMAP_LOCAL_STORAGE_KEY, source.value)
  }, 500)
})

async function loadInitialMindmapSource() {
  await initMermaid()

  let pending = takeMindmapNavBridgeSource().trim()
  if (!pending) {
    try {
      pending = (sessionStorage.getItem(MINDMAP_PENDING_SESSION_KEY) || '').trim()
      if (pending) sessionStorage.removeItem(MINDMAP_PENDING_SESSION_KEY)
    } catch {
      pending = ''
    }
  } else {
    try {
      sessionStorage.removeItem(MINDMAP_PENDING_SESSION_KEY)
    } catch {
      /* ignore */
    }
  }

  if (pending) {
    source.value = pending
    try {
      localStorage.setItem(MINDMAP_LOCAL_STORAGE_KEY, source.value)
    } catch {
      /* ignore */
    }
    await nextTick()
    await renderPreview()
    return
  }

  const saved = localStorage.getItem(MINDMAP_LOCAL_STORAGE_KEY)
  source.value = saved != null && saved !== '' ? saved : DEFAULT_SAMPLE
  await nextTick()
  await renderPreview()
}

onMounted(() => {
  loadInitialMindmapSource()
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

.preview-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
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
