<template>
  <Layout>
    <div class="mindmap-page">
      <div class="page-header">
        <h2>
          <IconMindmap :size="32" color="#4facfe" />
          思维导图（Mermaid）
        </h2>
        <p class="subtitle">
          支持 Mermaid 语法，创建和分享思维导图。
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
                <div class="preview-title-wrap">
                  <span class="preview-title">预览</span>
                  <span class="preview-hint">滚轮缩放，左键拖拽平移</span>
                </div>
                <div class="preview-actions">
                  <el-button size="small" plain @click="resetPreviewView">
                    复位视图
                  </el-button>
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
              </div>
            </template>
            <el-alert
              v-if="parseError"
              type="error"
              :closable="false"
              :title="parseError"
              class="error-alert"
            />
            <div
              ref="previewViewport"
              class="preview-viewport"
              :class="{ 'preview-viewport--panning': isPanning }"
              @wheel.prevent="onPreviewWheel"
              @mousedown="onPanStart"
            >
              <div ref="previewLayer" class="preview-layer" />
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </Layout>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
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

const SCALE_MIN = 0.25
const SCALE_MAX = 4
const WHEEL_FACTOR = 1.08

/** 初始适配时内容中心的垂直位置（视口高度比例）。0.5 为几何居中，略小则整体偏上，贴近卡片中部阅读区 */
const FIT_ANCHOR_Y_RATIO = 0.44

const source = ref('')
const previewViewport = ref(null)
const previewLayer = ref(null)
const parseError = ref('')
const savingPreviewPng = ref(false)

/** 当前「相机」矩形（SVG 用户坐标系），宽高比始终与视口 client 一致；缩小窗口 =放大内容 */
const viewBoxState = ref({ x: 0, y: 0, width: 100, height: 100 })
/** 最近一次「适配视口」时的 viewBox.width，用于滚轮缩放上下限（等价于原 SCALE_MIN/MAX） */
let fitViewBoxWidth = 100
const isPanning = ref(false)

let panStartClientX = 0
let panStartClientY = 0
let panStartViewBox = { x: 0, y: 0, width: 100, height: 100 }

let mermaidReady = false
let mermaidApi = null

function getViewportContentBox() {
  const vp = previewViewport.value
  if (!vp) return { Vw: 400, Vh: 300, padL: 0, padT: 0 }
  const cs = window.getComputedStyle(vp)
  const padL = Number.parseFloat(cs.paddingLeft) || 0
  const padR = Number.parseFloat(cs.paddingRight) || 0
  const padT = Number.parseFloat(cs.paddingTop) || 0
  const padB = Number.parseFloat(cs.paddingBottom) || 0
  const Vw = Math.max(vp.clientWidth - padL - padR, 80)
  const Vh = Math.max(vp.clientHeight - padT - padB, 80)
  return { Vw, Vh, padL, padT }
}

/** 将 viewBoxState 写入当前预览 SVG（用 viewBox 映射代替 CSS scale，放大仍清晰） */
function syncSvgViewBox() {
  const svg = previewLayer.value?.querySelector('svg')
  if (!svg) return
  const vb = viewBoxState.value
  svg.setAttribute('viewBox', `${vb.x} ${vb.y} ${vb.width} ${vb.height}`)
  svg.setAttribute('preserveAspectRatio', 'none')
  svg.setAttribute('width', '100%')
  svg.setAttribute('height', '100%')
  svg.style.display = 'block'
  svg.style.maxWidth = 'none'
  svg.style.maxHeight = 'none'
}

/** 按视口「contain」铺满；水平居中，垂直按 FIT_ANCHOR_Y_RATIO 对齐（受 SCALE_MIN / SCALE_MAX 约束） */
function fitPreviewToViewport() {
  const vp = previewViewport.value
  const svg = previewLayer.value?.querySelector('svg')
  if (!vp || !svg) return

  let bb
  try {
    bb = svg.getBBox()
  } catch {
    return
  }
  const w = Math.max(bb.width, 1)
  const h = Math.max(bb.height, 1)
  const cx = bb.x + w / 2
  const cy = bb.y + h / 2

  const { Vw, Vh } = getViewportContentBox()
  const Ra = Vw / Vh
  const t = Math.max(h, w / Ra)
  const vbW = Ra * t
  const vbH = t
  const midY = cy + (0.5 - FIT_ANCHOR_Y_RATIO) * vbH

  viewBoxState.value = {
    x: cx - vbW / 2,
    y: midY - vbH / 2,
    width: vbW,
    height: vbH
  }
  fitViewBoxWidth = vbW
  syncSvgViewBox()
}

function scheduleFitPreviewToViewport() {
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      fitPreviewToViewport()
    })
  })
}

/** 复位视图：重新适配视口并居中 */
function resetPreviewView() {
  fitPreviewToViewport()
}

let previewResizeObserver = null
function setupPreviewResizeObserver() {
  if (previewResizeObserver || typeof ResizeObserver === 'undefined') return
  const el = previewViewport.value
  if (!el) return
  let timer = null
  previewResizeObserver = new ResizeObserver(() => {
    clearTimeout(timer)
    timer = setTimeout(() => {
      if (previewLayer.value?.querySelector('svg')) {
        fitPreviewToViewport()
      }
    }, 120)
  })
  previewResizeObserver.observe(el)
}

function detachPanListeners() {
  window.removeEventListener('mousemove', onPanMove)
  window.removeEventListener('mouseup', onPanEnd)
  isPanning.value = false
}

function onPanMove(e) {
  if (!isPanning.value) return
  const vp = previewViewport.value
  if (!vp) return
  const { Vw, Vh } = getViewportContentBox()
  const dx = e.clientX - panStartClientX
  const dy = e.clientY - panStartClientY
  const vb0 = panStartViewBox
  viewBoxState.value = {
    x: vb0.x - (dx * vb0.width) / Vw,
    y: vb0.y - (dy * vb0.height) / Vh,
    width: vb0.width,
    height: vb0.height
  }
  syncSvgViewBox()
}

function onPanEnd() {
  detachPanListeners()
}

function onPanStart(e) {
  if (e.button !== 0) return
  const vp = previewViewport.value
  if (!vp || !vp.contains(e.target)) return
  isPanning.value = true
  panStartClientX = e.clientX
  panStartClientY = e.clientY
  panStartViewBox = { ...viewBoxState.value }
  window.addEventListener('mousemove', onPanMove)
  window.addEventListener('mouseup', onPanEnd)
}

function onPreviewWheel(e) {
  const vp = previewViewport.value
  if (!vp) return
  const rect = vp.getBoundingClientRect()
  const { Vw, Vh, padL, padT } = getViewportContentBox()
  const mx = e.clientX - rect.left - padL
  const my = e.clientY - rect.top - padT
  const vb = viewBoxState.value
  const factor = e.deltaY < 0 ? WHEEL_FACTOR : 1 / WHEEL_FACTOR
  let newW = vb.width / factor
  const wMin = fitViewBoxWidth / SCALE_MAX
  const wMax = fitViewBoxWidth / SCALE_MIN
  if (newW < wMin) newW = wMin
  if (newW > wMax) newW = wMax
  const newH = (newW * Vh) / Vw
  if (Math.abs(newW - vb.width) < 1e-9) return

  const worldX = vb.x + (mx * vb.width) / Vw
  const worldY = vb.y + (my * vb.height) / Vh
  viewBoxState.value = {
    x: worldX - (mx * newW) / Vw,
    y: worldY - (my * newH) / Vh,
    width: newW,
    height: newH
  }
  syncSvgViewBox()
}

async function getMermaid() {
  if (!mermaidApi) {
    const mod = await import('mermaid')
    mermaidApi = mod.default
  }
  return mermaidApi
}

/**
 * 对预览视口 DOM 栅格化导出（mindmap 等文字在 SVG foreignObject 内，浏览器把 SVG 当图片解码时会丢字，必须截真实 DOM）。
 */
async function exportPreviewViewportToPng(filename) {
  const vp = previewViewport.value
  if (!vp) throw new Error('预览区域未就绪')
  const { toBlob } = await import('html-to-image')
  const pr = Math.min(4, Math.max(2, (window.devicePixelRatio || 1) * 2))
  const blob = await toBlob(vp, {
    pixelRatio: pr,
    cacheBust: true,
    backgroundColor: '#fafafa',
    type: 'image/png'
  })
  if (!blob) throw new Error('生成 PNG 失败')
  const url = URL.createObjectURL(blob)
  try {
    const a = document.createElement('a')
    a.download = filename
    a.href = url
    a.rel = 'noopener'
    a.click()
    setTimeout(() => URL.revokeObjectURL(url), 2000)
  } catch (e) {
    URL.revokeObjectURL(url)
    throw e
  }
}

/** 将预览区导出为 PNG：优先 DOM 截图（含 foreignObject 文字），失败再回退 SVG→Canvas */
async function savePreviewAsPng() {
  const vp = previewViewport.value
  const layer = previewLayer.value
  const svg = layer?.querySelector('svg')
  if (!svg || !vp) {
    ElMessage.warning('请先点击「渲染预览」生成图形后再保存')
    return
  }
  savingPreviewPng.value = true
  const filename = `思维导图_${Date.now()}.png`
  try {
    await exportPreviewViewportToPng(filename)
    ElMessage.success('已保存为 PNG')
  } catch (e1) {
    try {
      await exportSvgToPng(svg, filename, {
        viewBox: { ...viewBoxState.value },
        pixelScale: Math.min(4, Math.max(2, (window.devicePixelRatio || 1) * 2))
      })
      ElMessage.success('已保存为 PNG（备用导出）')
    } catch (e2) {
      const m1 = e1 instanceof Error ? e1.message : String(e1)
      const m2 = e2 instanceof Error ? e2.message : String(e2)
      ElMessage.error(`导出失败：${m1}；备用：${m2}`)
    }
  } finally {
    savingPreviewPng.value = false
  }
}

/**
 * 将 Mermaid 等依赖 class 与内部 style 的 SVG 在导出前内联为属性，避免 canvg / 位图解码丢字。
 * @param {SVGSVGElement} svgOriginal
 * @param {SVGSVGElement} svgClone
 */
function inlineSvgExportStyles(svgOriginal, svgClone) {
  const origTexts = svgOriginal.querySelectorAll('text, tspan')
  const cloneTexts = svgClone.querySelectorAll('text, tspan')
  const n = Math.min(origTexts.length, cloneTexts.length)
  for (let i = 0; i < n; i++) {
    const st = window.getComputedStyle(origTexts[i])
    const el = cloneTexts[i]
    let fill = st.fill
    if (!fill || fill === 'none' || /^rgba\(0,\s*0,\s*0,\s*0\)$/.test(fill)) {
      fill = st.color
    }
    if (fill && fill !== 'none' && !/^rgba\(0,\s*0,\s*0,\s*0\)$/.test(fill)) {
      el.setAttribute('fill', fill)
    }
    const ff = st.fontFamily?.split(',')[0]?.replace(/["']/g, '').trim()
    if (ff) el.setAttribute('font-family', ff)
    if (st.fontSize) el.setAttribute('font-size', st.fontSize)
    const fw = String(st.fontWeight)
    if (fw && fw !== '400' && fw !== 'normal') el.setAttribute('font-weight', fw)
    if (st.opacity && st.opacity !== '1') el.setAttribute('opacity', st.opacity)
  }

  const origFos = svgOriginal.querySelectorAll('foreignObject')
  const cloneFos = svgClone.querySelectorAll('foreignObject')
  const nf = Math.min(origFos.length, cloneFos.length)
  for (let i = 0; i < nf; i++) {
    inlineForeignObjectStyles(origFos[i], cloneFos[i])
  }
}

/**
 * @param {SVGForeignObjectElement} origFo
 * @param {SVGForeignObjectElement} cloneFo
 */
function inlineForeignObjectStyles(origFo, cloneFo) {
  function walk(o, c) {
    if (o.nodeType !== Node.ELEMENT_NODE || c.nodeType !== Node.ELEMENT_NODE) return
    const oEl = /** @type {Element} */ (o)
    const cEl = /** @type {Element} */ (c)
    const tag = oEl.tagName.toLowerCase()
    if (
      ['div', 'span', 'p', 'label', 'td', 'th', 'a', 'code', 'pre'].includes(tag) ||
      oEl.childElementCount === 0
    ) {
      const st = window.getComputedStyle(oEl)
      const extra = [
        `color:${st.color}`,
        `font-size:${st.fontSize}`,
        `font-weight:${st.fontWeight}`,
        `font-style:${st.fontStyle}`,
        `font-family:${st.fontFamily}`,
        `text-align:${st.textAlign}`,
        `line-height:${st.lineHeight}`
      ].join(';')
      const prev = cEl.getAttribute('style') || ''
      cEl.setAttribute('style', prev ? `${prev};${extra}` : extra)
    }
    const oc = oEl.children
    const cc = cEl.children
    for (let j = 0; j < Math.min(oc.length, cc.length); j++) {
      walk(oc[j], cc[j])
    }
  }
  if (origFo.firstElementChild && cloneFo.firstElementChild) {
    walk(origFo.firstElementChild, cloneFo.firstElementChild)
  }
}

/**
 * @param {SVGSVGElement} svgEl
 * @param {{ x: number; y: number; width: number; height: number }} vb
 * @param {number} outW
 * @param {number} outH
 */
function buildExportClone(svgEl, vb, outW, outH) {
  const clone = /** @type {SVGSVGElement} */ (svgEl.cloneNode(true))
  clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
  if (!clone.getAttribute('xmlns:xlink')) {
    clone.setAttribute('xmlns:xlink', 'http://www.w3.org/1999/xlink')
  }
  clone.setAttribute('viewBox', `${vb.x} ${vb.y} ${vb.width} ${vb.height}`)
  clone.setAttribute('preserveAspectRatio', 'none')
  clone.setAttribute('width', String(outW))
  clone.setAttribute('height', String(outH))
  clone.removeAttribute('style')
  return clone
}

function downloadCanvasPng(canvas, filename) {
  return new Promise((resolve, reject) => {
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

/**
 * 备用：SVG 克隆 + canvg（对 foreignObject 仍可能不完整；主路径为 DOM 截图）。
 * @param {SVGSVGElement} svgEl
 * @param {string} filename
 * @param {{ viewBox: { x: number; y: number; width: number; height: number }; pixelScale?: number }} opts
 */
async function exportSvgToPng(svgEl, filename, opts) {
  const vb = opts?.viewBox
  if (!vb?.width || !vb?.height) {
    throw new Error('视窗尺寸无效，无法导出')
  }
  const vp = previewViewport.value
  const { Vw: cssW, Vh: cssH } = vp ? getViewportContentBox() : { Vw: 400, Vh: 300 }
  const pixelScale = opts?.pixelScale ?? 2
  const outW = Math.ceil(cssW * pixelScale)
  const outH = Math.ceil(cssH * pixelScale)

  const clone = buildExportClone(svgEl, vb, outW, outH)
  inlineSvgExportStyles(svgEl, clone)
  await rasterizeSvgCloneWithCanvg(clone, outW, outH, filename)
}

/**
 * @param {SVGSVGElement} clone
 */
async function rasterizeSvgCloneWithCanvg(clone, outW, outH, filename) {
  const { Canvg } = await import('canvg')
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
  await downloadCanvasPng(canvas, filename)
}

async function initMermaid() {
  if (mermaidReady) return
  const mermaid = await getMermaid()
  mermaid.initialize({
    startOnLoad: false,
    securityLevel: 'strict',
    theme: 'neutral',
    flowchart: {
      htmlLabels: false,
      useMaxWidth: true
    },
    themeVariables: {
      fontSize: '16px'
    }
  })
  mermaidReady = true
}

function showPlaceholder() {
  detachPanListeners()
  const layer = previewLayer.value
  if (!layer) return
  layer.innerHTML =
    '<p class="preview-placeholder">在左侧输入 Mermaid 后点击「渲染预览」</p>'
}

async function renderPreview() {
  parseError.value = ''
  detachPanListeners()

  const layer = previewLayer.value
  if (!layer) return

  await initMermaid()
  const mermaid = await getMermaid()
  layer.innerHTML = ''

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
    layer.innerHTML = svg
    bindFunctions?.(layer)
    await nextTick()
    scheduleFitPreviewToViewport()
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

onMounted(async () => {
  await nextTick()
  setupPreviewResizeObserver()
  await loadInitialMindmapSource()
})

onUnmounted(() => {
  detachPanListeners()
  if (previewResizeObserver) {
    previewResizeObserver.disconnect()
    previewResizeObserver = null
  }
})
</script>

<style scoped>
.mindmap-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 16px;
}

.page-header {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 28px;
}

.page-header h2 {
  flex-direction: column;
  gap: 10px;
  margin: 0 0 8px;
  font-size: 28px;
}

.subtitle {
  margin: 0 auto;
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
  text-align: center;
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
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.preview-title-wrap {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.preview-title {
  font-weight: 600;
  color: #303133;
}

.preview-hint {
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
}

.preview-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  flex-shrink: 0;
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

.preview-viewport {
  flex: 1;
  min-height: 280px;
  overflow: hidden;
  position: relative;
  padding: 8px;
  background: #fafafa;
  border-radius: 8px;
  cursor: grab;
}

.preview-viewport--panning {
  cursor: grabbing;
  user-select: none;
}

.preview-layer {
  width: 100%;
  height: 100%;
  min-height: 0;
  display: block;
}

.preview-layer :deep(svg) {
  width: 100%;
  height: 100%;
  max-width: none;
  max-height: none;
  display: block;
  shape-rendering: geometricPrecision;
  text-rendering: geometricPrecision;
}

.preview-placeholder {
  margin: 0;
  color: #909399;
  font-size: 14px;
}
</style>
