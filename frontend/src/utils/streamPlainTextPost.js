/**
 * POST JSON，按 UTF-8 读取响应体流并累积文本；适用于后端 `StreamingResponse(text/plain)`。
 *
 * @param {object} opts
 * @param {string} opts.url 完整请求 URL（含 /api 前缀，与现有 translate 等一致）
 * @param {object} opts.body 将 JSON.stringify 作为请求体
 * @param {Record<string, string>} [opts.headers] 额外请求头（如 Authorization）
 * @param {(accumulated: string) => void} [opts.onChunk] 每次解码增量后传入当前全文
 * @param {AbortSignal} [opts.signal]
 * @returns {Promise<string>} 最终完整文本
 */
export async function streamPlainTextPost({
  url,
  body,
  headers = {},
  onChunk,
  signal
}) {
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
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
    const text = await res.text()
    onChunk?.(text)
    return text
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let acc = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    acc += decoder.decode(value, { stream: true })
    onChunk?.(acc)
  }
  acc += decoder.decode()
  onChunk?.(acc)
  return acc
}
