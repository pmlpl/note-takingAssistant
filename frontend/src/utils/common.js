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