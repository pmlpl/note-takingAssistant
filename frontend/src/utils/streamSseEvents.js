/**
 * POST JSON，按 SSE（Server-Sent Events）格式解析响应体流。
 *
 * 后端响应 content-type 为 `text/event-stream`，每个事件为：
 *   data: {json}\n\n
 *
 * 该函数逐 chunk 解码，按双换行切分事件，再解析每个 data: 行的 JSON。
 *
 * @param {object} opts
 * @param {string} opts.url 完整请求 URL（含 /api 前缀）
 * @param {object} opts.body 将 JSON.stringify 作为请求体
 * @param {Record<string, string>} [opts.headers] 额外请求头
 * @param {(event: { type: string, [key: string]: any }) => void} [opts.onEvent] 每个事件回调
 * @param {AbortSignal} [opts.signal]
 * @returns {Promise<void>} 流结束时 resolve
 */
export async function streamSseEventsPost({
  url,
  body,
  headers = {},
  onEvent,
  signal
}) {
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
      ...headers
    },
    body: JSON.stringify(body),
    signal
  })

  if (!res.ok) {
    let detail = `HTTP ${res.status}`
    try {
      const ct = res.headers.get('content-type') || ''
      if (ct.includes('application/json')) {
        const j = await res.json()
        detail = j.detail ?? JSON.stringify(j)
      } else {
        const t = await res.text()
        if (t) detail = t.slice(0, 500)
      }
    } catch {
      /* ignore */
    }
    const err = new Error(typeof detail === 'string' ? detail : '请求失败')
    err.response = { status: res.status, data: { detail } }
    throw err
  }

  if (!res.body) {
    return
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  const dispatchEvents = (chunkText) => {
    buffer += chunkText
    // 事件之间以 \n\n 分隔
    const parts = buffer.split('\n\n')
    // 最后一段可能不完整，保留到下一次
    buffer = parts.pop() || ''

    for (const part of parts) {
      const trimmed = part.trim()
      if (!trimmed) continue
      // 一个事件可能含多行 data:，按 SSE 规范应拼接
      // 此处后端只发单行 data:，简化为提取所有以 data: 开头的行
      const dataLines = trimmed
        .split('\n')
        .filter((line) => line.startsWith('data:'))
        .map((line) => line.slice(5).trimStart())
      if (dataLines.length === 0) continue
      const dataStr = dataLines.join('\n')
      try {
        const evt = JSON.parse(dataStr)
        onEvent?.(evt)
      } catch (e) {
        // 忽略无法解析的事件，避免阻塞后续
        console.warn('SSE 事件解析失败：', dataStr, e)
      }
    }
  }

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    const text = decoder.decode(value, { stream: true })
    dispatchEvents(text)
  }
  // 处理最后残留
  if (buffer.trim()) {
    dispatchEvents('\n\n')
  }
}
