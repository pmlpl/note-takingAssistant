// 消息提示时长配置（毫秒）
export const MESSAGE_DURATION = {
  SHORT: 1000,    // 短提示：1秒
  NORMAL: 1500,   // 普通提示：1.5秒
  LONG: 2000      // 长提示：2秒
}

export function formatDate(dateStr, format = 'YYYY-MM-DD HH:mm:ss') {
  const date = new Date(dateStr)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  
  return format
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds)
}

/**
 * 判断笔记 HTML/纯文本是否「几乎为空」（用于上传文件等场景的弱提示）
 */
export function hasMeaningfulNoteText(content) {
  if (content == null) return false
  const s = String(content)
  if (!s.trim()) return false
  const decoded = s.replace(/&nbsp;/gi, ' ').replace(/&#160;/g, ' ').replace(/\u00a0/g, ' ')
  const plain = decoded.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim()
  if (plain.length > 0) return true
  if (decoded.length >= 80) return true
  if (/<(img|table|figure|iframe|video|embed)\b/i.test(decoded)) return true
  return false
}

/**
 * 是否应把笔记内容塞进 AI 请求（避免 hasMeaningfulNoteText 对富文本误判导致整段不上送）
 */
export function shouldAttachNoteContext(raw) {
  if (raw == null) return false
  const t = String(raw)
    .replace(/&nbsp;/gi, ' ')
    .replace(/&#160;/g, ' ')
    .replace(/\u00a0/g, ' ')
    .trim()
  return t.length > 0
}

/** 单段笔记随 chat 发送的最大字符，避免占满分词窗口导致模型丢弃正文 */
export const MAX_NOTE_CONTEXT_CHARS = 28000

export function clipNoteForAiContext(text) {
  const s = String(text ?? '')
  if (s.length <= MAX_NOTE_CONTEXT_CHARS) return s
  return `${s.slice(0, MAX_NOTE_CONTEXT_CHARS)}\n\n[…正文过长，此处已截断；可在笔记编辑页查看全文…]`
}

/**
 * 将笔记正文与当前用户问题合并为一条 user 消息发给模型（比仅靠 system 更易被本地模型读到）
 */
export function composeUserMessageWithNoteContext(userMessage, noteTitle, rawContent) {
  const clipped = clipNoteForAiContext(rawContent)
  const title = noteTitle || '未命名笔记'
  return (
    `下面提供笔记《${title}》的正文。你必须先阅读「笔记正文」再回答最后的【用户问题】，不要声称未收到或未看到笔记内容。\n\n` +
    `----------笔记正文开始----------\n${clipped}\n----------笔记正文结束----------\n\n` +
    `【用户问题】\n${userMessage}`
  )
}

/** 思维导图页 localStorage 缓存键（与 Mindmap.vue 共用） */
export const MINDMAP_LOCAL_STORAGE_KEY = 'mindmap_mermaid_source'

/** sessionStorage：从首页 AI 助手带源码跳转思维导图页时写入，目标页读取后删除 */
export const MINDMAP_PENDING_SESSION_KEY = 'mindmap_pending_mermaid_source'

/** 首页「思维导图」快捷按钮发送的提示词：强制模型输出 ```mermaid 可渲染块 */
export const AI_MINDMAP_QUICK_PROMPT = [
  '请根据当前笔记或对话上下文，整理一张知识结构思维导图。',
  '',
  '【必须遵守的格式】回复中必须包含一段 Markdown 代码块：围栏第一行必须是三个反引号 + 小写 mermaid（即 ```mermaid），内容为可被 Mermaid 直接解析的源码，例如：',
  '```mermaid',
  'flowchart TD',
  '  Root[主题] --> A[分支一]',
  '  Root --> B[分支二]',
  '```',
  '',
  '若内容含代码、装饰器、列表推导式等，优先用 flowchart TD + 简短节点名；若用 mindmap，节点只能是缩进纯文字或 nodeId[\"说明\"] 形式，禁止在节点行直接写类似 [x for x in range]、@decorator 等源码片段。',
  '不要用其它语言标记代替 mermaid；不要只用列表或纯文字描述而不给出上述代码块。除代码块外可附一两句简短说明。'
].join('\n')

/**
 * mindmap 中一行若以 [ 开头、含 @xxx、或方括号内出现 for…in 等，易与语法冲突导致解析失败。
 * 将此类行改为 mmdfixN["原文"]（Mermaid 官方 nodeId["标签"] 形式）。
 */
function mindmapLineNeedsQuotedSafeNode(trimmedBody) {
  const s = trimmedBody.trim()
  if (!s) return false
  if (/^[A-Za-z_\u4e00-\u9fff][\w\u4e00-\u9fff]*\["/.test(s)) return false
  if (/^[A-Za-z_\u4e00-\u9fff][\w\u4e00-\u9fff]*\(\(/.test(s)) return false
  if (s.startsWith('[')) return true
  if (/^@\w/.test(s)) return true
  if (/(?:^|\s)@\w/.test(s)) return true
  if (/\[[^\]]*\bfor\b[^\]]*\bin\b[^\]]*\]/i.test(s)) return true
  return false
}

export function prepareMermaidSourceForRender(src) {
  const text = String(src ?? '')
    .replace(/\r\n/g, '\n')
    .replace(/^\uFEFF/, '')
  const lines = text.split('\n')
  if (lines.length === 0) return text
  const firstTrim = (lines[0] || '').trim()
  if (!/^mindmap\b/i.test(firstTrim)) return text

  let auto = 0
  const out = [lines[0]]
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i]
    const m = /^(\s*)(.*)$/.exec(line)
    if (!m || !m[2].trim()) {
      out.push(line)
      continue
    }
    const ind = m[1]
    const body = m[2]
    const t = body.trim()
    if (mindmapLineNeedsQuotedSafeNode(t)) {
      const id = `mmdfix${auto++}`
      const esc = t.replace(/\\/g, '\\\\').replace(/"/g, '\\"')
      out.push(`${ind}${id}["${esc}"]`)
    } else {
      out.push(line)
    }
  }
  return out.join('\n')
}

/** 从某行判断是否为 Mermaid 图表起始（用于无 ```mermaid 标记的代码块或正文） */
const MERMAID_DIAGRAM_LINE =
  /^\s*((?:flowchart|graph)\s+(?:TD|TB|BT|RL|LR|DR)|sequenceDiagram|classDiagram|stateDiagram-v2|stateDiagram|erDiagram|journey|gantt|pie|gitGraph|mindmap|timeline|C4Context|C4Container|C4Component|sankey-beta|block-beta|packet-beta|kanban|architecture|xychart-beta|quadrantChart|requirement)\b/i

function lineLooksLikeMermaidStart(line) {
  const t = (line || '').trim()
  if (!t || t.startsWith('```')) return false
  return MERMAID_DIAGRAM_LINE.test(t)
}

/**
 * 从 Markdown 中提取首个 ```mermaid / ```mindmap 围栏内源码（不含围栏），失败返回空串
 */
export function extractFirstMermaidSource(markdown) {
  if (markdown == null || typeof markdown !== 'string') return ''
  const re = /```\s*(?:mermaid|mindmap)\s*(?:\r?\n)?([\s\S]*?)```/i
  const m = markdown.match(re)
  if (!m) return ''
  return m[1].replace(/^\uFEFF/, '').trim()
}

function extractMermaidFromGenericCodeBlocks(markdown) {
  const re = /```\s*([\w-]*)\s*(?:\r?\n)?([\s\S]*?)```/gi
  let m
  let candidate = ''
  while ((m = re.exec(markdown)) !== null) {
    const lang = (m[1] || '').trim().toLowerCase()
    const body = (m[2] || '').replace(/^\uFEFF/, '').trim()
    if (!body) continue
    if (lang === 'mermaid' || lang === 'mindmap') return body
    const firstMeaningful = body.split(/\r?\n/).find((l) => l.trim().length) || ''
    if (MERMAID_DIAGRAM_LINE.test(firstMeaningful.trim())) {
      if (!candidate || body.length > candidate.length) candidate = body
    }
  }
  return candidate
}

function extractUnfencedMermaidBlock(markdown) {
  const lines = markdown.split(/\r?\n/)
  let start = -1
  for (let i = 0; i < lines.length; i++) {
    if (lineLooksLikeMermaidStart(lines[i])) {
      start = i
      break
    }
  }
  if (start < 0) return ''
  return lines.slice(start).join('\n').trim()
}

/**
 * 从 AI 回复中提取可交给 Mermaid 渲染的源码（显式 mermaid 围栏、其它围栏内的 flowchart 等、或未围栏的图表正文）
 */
export function extractMindmapDiagramSource(markdown) {
  if (markdown == null || typeof markdown !== 'string') return ''
  const explicit = extractFirstMermaidSource(markdown)
  if (explicit) return explicit
  const fromGeneric = extractMermaidFromGenericCodeBlocks(markdown)
  if (fromGeneric) return fromGeneric
  return extractUnfencedMermaidBlock(markdown)
}

/** 同页内存桥：避免仅依赖 sessionStorage 时偶发未写入即跳转导致目标页读空 */
let mindmapNavBridge = ''
export function setMindmapNavBridgeSource(src) {
  mindmapNavBridge = typeof src === 'string' ? src : ''
}
export function takeMindmapNavBridgeSource() {
  const s = mindmapNavBridge
  mindmapNavBridge = ''
  return s
}

export function debounce(fn, delay) {
  let timer = null
  return function(...args) {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      fn.apply(this, args)
    }, delay)
  }
}

export function throttle(fn, delay) {
  let lastTime = 0
  return function(...args) {
    const now = Date.now()
    if (now - lastTime >= delay) {
      lastTime = now
      fn.apply(this, args)
    }
  }
}

export function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).substr(2)
}

export function stripHtml(html) {
  return html.replace(/<[^>]*>/g, '')
}