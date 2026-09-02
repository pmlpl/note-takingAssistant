import DOMPurify from 'isomorphic-dompurify'
import { marked } from 'marked'

/** 与后端 `looks_like_html_note` 一致：含常见 HTML 标签则按 HTML 处理，否则按 Markdown。 */
const LIKELY_HTML_RE =
  /<\s*\/?\s*(?:p|div|span|table|tr|td|th|img|br|h[1-6]|ul|ol|li|section|article|blockquote|tbody|thead|tfoot|caption|colgroup|col|figure|figcaption|html|body)\b/i

/**
 * 行首 Markdown 结构信号（ATX 标题、代码围栏、引用、列表、分隔线、表格行）。
 * 用于优先识别 Markdown：代码围栏/列表里出现 `<p>` 等标签时不应误判为 HTML。
 */
const MARKDOWN_STRUCTURE_RE = new RegExp(
  [
    '^\\s*#{1,6}\\s+', // ATX 标题：# 标题
    '^\\s*(?:```|~~~)', // 代码围栏：```lang / ~~~lang
    '^\\s*>\\s', // 引用：> text
    '^\\s*(?:[-*+])\\s', // 无序列表：- item
    '^\\s*\\d+[.)]\\s', // 有序列表：1. item
    '^\\s*(?:-{3,}|\\*{3,}|_{3,})\\s*$', // 分隔线：--- / *** / ___
    '^\\s*\\|.*\\|' // GFM 表格行：| a | b |
  ].join('|'),
  'm'
)

const TEXT_ALIGN_VALUES = new Set(['left', 'right', 'center', 'justify', 'start', 'end'])
const VERTICAL_ALIGN_VALUES = new Set(['top', 'middle', 'bottom', 'baseline'])
const ALIGN_ATTR_VALUES = new Set(['left', 'right', 'center', 'justify', 'middle', 'char'])

/** 禁止出现在 style 属性值中的片段（防 XSS / 数据外带） */
const FORBIDDEN_IN_STYLE_VALUE = /url\s*\(|expression\s*\(|javascript:|@import|behavior\s*:|<\/script|&#/i

let alignmentHooksInstalled = false

/**
 * @param {string} val
 * @returns {boolean}
 */
function isSafeStyleToken(val) {
  if (!val || val.length > 200) return false
  return !FORBIDDEN_IN_STYLE_VALUE.test(val)
}

/**
 * Word 常用长度：14.0pt、0.5cm、12px（可选前导负号，用于缩进）
 * @param {string} val
 * @returns {string|null}
 */
function matchCssLength(val) {
  const v = val.replace(/\s+/g, ' ').trim()
  if (!isSafeStyleToken(v)) return null
  if (/^-?[\d.]+\s*(pt|px|em|rem|%|in|cm|mm|ex|ch)$/i.test(v)) return v
  return null
}

/**
 * @param {string} val
 * @returns {string|null}
 */
function matchFontSize(val) {
  const v = val.replace(/\s+/g, ' ').trim()
  if (!isSafeStyleToken(v)) return null
  if (/^[\d.]+\s*(pt|px|em|rem|%)$/i.test(v)) return v
  return null
}

/**
 * @param {string} val
 * @returns {string|null}
 */
function matchLineHeight(val) {
  const v = val.replace(/\s+/g, ' ').trim()
  if (!isSafeStyleToken(v)) return null
  const low = v.toLowerCase()
  if (low === 'normal') return 'normal'
  if (/^\d+(\.\d+)?$/.test(low)) return low
  if (/^\d+(\.\d+)?%$/.test(low)) return low
  return matchCssLength(v)
}

/**
 * @param {string} val
 * @returns {string|null}
 */
function matchFontWeight(val) {
  const v = val.replace(/\s+/g, ' ').trim().toLowerCase()
  if (!isSafeStyleToken(v)) return null
  if (/^(normal|bold|bolder|lighter|\d{3})$/.test(v)) return v
  return null
}

/**
 * 字体族：禁止括号与反斜线，避免 expression / url
 * @param {string} val
 * @returns {string|null}
 */
function matchFontFamily(val) {
  const v = val.trim()
  if (!v || v.length > 220 || !isSafeStyleToken(v)) return null
  if (/[()\\<>{}]/.test(v)) return null
  if (/^[\w\s\u4e00-\u9fff,'".-]+$/u.test(v)) return v.replace(/\s+/g, ' ').trim()
  return null
}

/**
 * 颜色：hex / rgb(a) / 常见英文色名
 * @param {string} val
 * @returns {string|null}
 */
function matchColor(val) {
  const v = val.replace(/\s+/g, ' ').trim()
  if (!v || v.length > 60 || !isSafeStyleToken(v)) return null
  if (/^#([0-9a-f]{3}|[0-9a-f]{6}|[0-9a-f]{8})$/i.test(v)) return v
  if (/^rgba?\(\s*[\d.]+\s*,\s*[\d.]+\s*,\s*[\d.]+\s*(,\s*[\d.]+\s*)?\)$/i.test(v)) return v
  if (/^[a-z]{3,20}$/i.test(v)) return v.toLowerCase()
  return null
}

/**
 * 从 Word / 富文本导出的 style 中保留**安全**的排版声明（对齐、字号、缩进等），
 * 避免 DOMPurify 去掉整块 style 后预览与 Word 不一致。
 * @param {string} styleStr
 * @returns {string}
 */
export function sanitizeInlineAlignmentStyle(styleStr) {
  if (!styleStr || typeof styleStr !== 'string') return ''
  const kept = []
  for (const rawDecl of styleStr.split(';')) {
    const decl = rawDecl.trim()
    if (!decl) continue
    const colon = decl.indexOf(':')
    if (colon === -1) continue
    const prop = decl.slice(0, colon).trim().toLowerCase()
    let val = decl.slice(colon + 1).trim()
    val = val.replace(/\s*!important\s*$/i, '').trim()
    const valLower = val.toLowerCase()

    if (prop.startsWith('mso-')) {
      continue
    }

    if (prop === 'text-align') {
      const norm = valLower.replace(/['"]/g, '')
      if (TEXT_ALIGN_VALUES.has(norm)) {
        kept.push(`text-align: ${norm}`)
      }
      continue
    }
    if (prop === 'vertical-align') {
      const norm = valLower.replace(/['"]/g, '')
      if (VERTICAL_ALIGN_VALUES.has(norm)) {
        kept.push(`vertical-align: ${norm}`)
      }
      continue
    }
    if (prop === 'font-size') {
      const fs = matchFontSize(val)
      if (fs) kept.push(`font-size: ${fs}`)
      continue
    }
    if (prop === 'line-height') {
      const lh = matchLineHeight(val)
      if (lh) kept.push(`line-height: ${lh}`)
      continue
    }
    if (prop === 'font-weight') {
      const fw = matchFontWeight(val)
      if (fw) kept.push(`font-weight: ${fw}`)
      continue
    }
    if (prop === 'font-family') {
      const ff = matchFontFamily(val)
      if (ff) kept.push(`font-family: ${ff}`)
      continue
    }
    if (prop === 'color') {
      const c = matchColor(val)
      if (c) kept.push(`color: ${c}`)
      continue
    }
    if (
      prop === 'margin-top' ||
      prop === 'margin-bottom' ||
      prop === 'margin-left' ||
      prop === 'margin-right'
    ) {
      if (valLower === 'auto') {
        kept.push(`${prop}: auto`)
        continue
      }
      const len = matchCssLength(val)
      if (len) kept.push(`${prop}: ${len}`)
      continue
    }
    if (prop === 'padding-left' || prop === 'padding-right' || prop === 'padding-top' || prop === 'padding-bottom') {
      const len = matchCssLength(val)
      if (len) kept.push(`${prop}: ${len}`)
      continue
    }
    if (prop === 'text-indent') {
      const len = matchCssLength(val)
      if (len) kept.push(`text-indent: ${len}`)
      continue
    }
    if (prop === 'letter-spacing' || prop === 'word-spacing') {
      if (valLower === 'normal') {
        kept.push(`${prop}: normal`)
        continue
      }
      const len = matchCssLength(val)
      if (len) kept.push(`${prop}: ${len}`)
      continue
    }
    // Word 常用块级居中：margin: 0 auto / 0px auto
    if (prop === 'margin') {
      if (/^0(?:px)?\s+auto$/i.test(val.replace(/\s+/g, ' ').trim())) {
        kept.push('margin: 0 auto')
      }
      continue
    }
  }
  return kept.join('; ')
}

function ensureAlignmentSanitizeHooks() {
  if (alignmentHooksInstalled) return
  alignmentHooksInstalled = true

  DOMPurify.addHook('uponSanitizeAttribute', (node, data) => {
    if (data.attrName === 'style') {
      const safe = sanitizeInlineAlignmentStyle(String(data.attrValue ?? ''))
      if (safe) {
        data.attrValue = safe
      } else {
        data.keepAttr = false
      }
      return
    }
    if (data.attrName === 'align') {
      const v = String(data.attrValue ?? '').trim().toLowerCase()
      if (ALIGN_ATTR_VALUES.has(v)) {
        data.attrValue = v
        data.keepAttr = true
      } else {
        data.keepAttr = false
      }
      return
    }
    if (data.attrName === 'valign') {
      const v = String(data.attrValue ?? '').trim().toLowerCase()
      if (VERTICAL_ALIGN_VALUES.has(v)) {
        data.attrValue = v
        data.keepAttr = true
      } else {
        data.keepAttr = false
      }
    }
  })
}

ensureAlignmentSanitizeHooks()

/**
 * 判断内容应作为 HTML 还是 Markdown 渲染（与后端 `looks_like_html_note` 口径一致）。
 * 边界修正：
 * - 行首有 Markdown 结构信号（标题/围栏/引用/列表等）时优先按 Markdown，避免
 *   代码块或正文里出现的 `<p>` 等标签导致整段误判为 HTML；
 * - `<!DOCTYPE` / `<!--` 开头按 HTML；
 * - 纯文本比较表达式（如 `1 < 2`）不含已知标签，按 Markdown。
 * @param {unknown} text
 * @returns {boolean}
 */
export function isLikelyHtmlContent(text) {
  const s = String(text ?? '').trim()
  if (!s.includes('<')) return false
  if (MARKDOWN_STRUCTURE_RE.test(s)) return false
  if (/^<!/.test(s)) return true
  return LIKELY_HTML_RE.test(s)
}

/**
 * 统一内容渲染入口：HTML 内容仅消毒保留原结构；Markdown / 纯文本经 marked 渲染后消毒。
 * 笔记预览、AI 聊天/生成/总结/翻译结果都应走此函数，避免各页面判断与渲染不一致。
 * @param {unknown} content
 * @returns {string}
 */
export function renderContentToSafeHtml(content) {
  if (content == null || content === '') return ''
  return isLikelyHtmlContent(content)
    ? sanitizeHtml(content)
    : renderMarkdownToSafeHtml(content)
}

/**
 * 对任意 HTML 片段做白名单消毒（用于 v-html、富文本 AI 输出等）。
 * @param {unknown} dirty
 * @returns {string}
 */
export function sanitizeHtml(dirty) {
  return DOMPurify.sanitize(String(dirty ?? ''), {
    USE_PROFILES: { html: true }
  })
}

/**
 * Markdown → HTML → 消毒，供 v-html 安全展示。
 * @param {unknown} markdown
 * @returns {string}
 */
export function renderMarkdownToSafeHtml(markdown) {
  const raw = marked.parse(String(markdown ?? ''), { async: false })
  const html = typeof raw === 'string' ? raw : String(raw)
  return sanitizeHtml(html)
}

/**
 * 动态加载 mermaid（与 Mindmap 页一致按需分包，避免进首包）；加载失败返回 null。
 * @returns {Promise<object|null>}
 */
async function loadMermaidApi() {
  try {
    const mod = await import('mermaid')
    return mod.default ?? mod
  } catch {
    return null
  }
}

let mermaidSeq = 0

/** 保留源码 <pre> 并标记降级状态（mermaid 解析失败 / 加载失败时调用） */
function markMermaidFallback(pre) {
  pre.dataset.mermaidState = 'fallback'
  pre.classList.add('mermaid-fallback')
  pre.setAttribute('title', '图表解析失败，已显示源码')
}

/**
 * 将容器内 ```mermaid / ```mindmap 代码块渲染为图表（在 Markdown 渲染后对 DOM 做水合）：
 * - 成功：以 `<div class="mermaid-rendered">` 替换原 `<pre>`，保留可交互的 bindFunctions；
 * - 失败（语法错误、mermaid 动态加载失败）：保留源码 `<pre>` 并标记 `mermaid-fallback` 降级展示。
 * v-html 每次重渲染后调用一次即可；调用方（MarkdownContent）已对流式输出做防抖。
 * @param {Element|null} container
 * @returns {Promise<void>}
 */
export async function hydrateMermaidBlocks(container) {
  if (!container || typeof container.querySelectorAll !== 'function') return
  const codeEls = Array.from(
    container.querySelectorAll('pre code.language-mermaid, pre code.language-mindmap')
  )
  if (codeEls.length === 0) return

  const mermaidApi = await loadMermaidApi()
  if (mermaidApi) {
    await mermaidApi.initialize({ startOnLoad: false })
  }

  for (const codeEl of codeEls) {
    const pre = codeEl.closest('pre')
    if (!pre || pre.dataset.mermaidState) continue
    const source = String(codeEl.textContent ?? '').trim()
    pre.dataset.mermaidState = 'pending'
    if (!source || !mermaidApi) {
      markMermaidFallback(pre)
      continue
    }
    try {
      const id = `mmd-${Date.now().toString(36)}-${mermaidSeq++}`
      const { svg, bindFunctions } = await mermaidApi.render(id, source)
      const holder = document.createElement('div')
      holder.className = 'mermaid-rendered'
      holder.innerHTML = svg
      if (typeof bindFunctions === 'function') {
        bindFunctions(holder)
      }
      pre.replaceWith(holder)
    } catch {
      markMermaidFallback(pre)
    }
  }
}
