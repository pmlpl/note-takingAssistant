const ALLOWED_SCHEMES = ['http', 'https']

const ALLOWED_PORTS = new Set([80, 443, 1234, 2000, 3000, 8000, 8081, 8082, 8083, 8084, 8085, 8888, 11434, 30000, 30001])

function isPrivateIpv4(ip) {
  const ipParts = ip.split('.').map(Number)
  if (ipParts.length !== 4) return false
  if (ipParts.some(p => isNaN(p) || p < 0 || p > 255)) return false
  return (
    ipParts[0] === 10 ||
    (ipParts[0] === 172 && ipParts[1] >= 16 && ipParts[1] <= 31) ||
    (ipParts[0] === 192 && ipParts[1] === 168) ||
    ipParts[0] === 127 ||
    (ipParts[0] === 169 && ipParts[1] === 254)
  )
}

function isPrivateIpv6(ip) {
  if (ip === '::1') return true
  if (ip.startsWith('fe80:')) return true
  if (ip.startsWith('fc00:')) return true
  if (ip.startsWith('fd00:')) return true
  const parts = ip.split(':')
  if (parts.length >= 2 && parts[0] === '0' && parts[1] === '0') return true
  return false
}

function isPrivateIp(ip) {
  if (!ip) return false
  const hostname = ip.toLowerCase()
  if (hostname === 'localhost') return true
  if (hostname.includes(':')) return isPrivateIpv6(hostname)
  return isPrivateIpv4(hostname)
}

function validateLocalModelUrl(url) {
  try {
    const u = new URL(url)
    if (!ALLOWED_SCHEMES.includes(u.protocol.replace(':', ''))) {
      return { valid: false, message: '仅支持 http/https 协议' }
    }
    const hostname = u.hostname.toLowerCase()
    if (!isPrivateIp(hostname)) {
      return { valid: false, message: '仅允许连接本地模型（私有IP地址）' }
    }
    const port = u.port ? parseInt(u.port) : (u.protocol === 'https:' ? 443 : 80)
    if (!ALLOWED_PORTS.has(port)) {
      return { valid: false, message: `端口 ${port} 不在允许列表内` }
    }
    return { valid: true, message: '' }
  } catch {
    return { valid: false, message: '无效的URL格式' }
  }
}

function isLocalUrl(url) {
  const result = validateLocalModelUrl(url)
  return result.valid
}

async function streamChatCompletion({ baseUrl, apiKey, model, messages, onChunk, signal, timeout = 600000 }) {
  const timeoutController = new AbortController()
  const timeoutId = setTimeout(() => timeoutController.abort(), timeout)
  const combinedSignal = signal ? AbortSignal.any([signal, timeoutController.signal]) : timeoutController.signal

  const url = `${baseUrl}/chat/completions`
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey || 'not-needed'}`
    },
    body: JSON.stringify({
      model: model || 'gpt-3.5-turbo',
      messages,
      stream: true
    }),
    signal: combinedSignal
  })

  if (!res.ok) {
    let detail = `HTTP ${res.status}`
    try {
      const ct = res.headers.get('content-type') || ''
      if (ct.includes('application/json')) {
        const j = await res.json()
        detail = j.error?.message ?? j.detail ?? JSON.stringify(j)
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
    
    const chunk = decoder.decode(value, { stream: true })
    const lines = chunk.split('\n')
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6)
        if (data === '[DONE]') continue
        try {
          const parsed = JSON.parse(data)
          const content = parsed.choices?.[0]?.delta?.content
          if (content) {
            acc += content
            onChunk?.(acc)
          }
        } catch {
          /* ignore parsing errors */
        }
      }
    }
  }
  
  acc += decoder.decode()
  onChunk?.(acc)
  clearTimeout(timeoutId)
  return acc
}

async function chatCompletion({ baseUrl, apiKey, model, messages, timeout = 600000 }) {
  const timeoutController = new AbortController()
  const timeoutId = setTimeout(() => timeoutController.abort(), timeout)

  const url = `${baseUrl}/chat/completions`
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey || 'not-needed'}`
    },
    body: JSON.stringify({
      model: model || 'gpt-3.5-turbo',
      messages,
      stream: false
    }),
    signal: timeoutController.signal
  })

  if (!res.ok) {
    let detail = `HTTP ${res.status}`
    try {
      const ct = res.headers.get('content-type') || ''
      if (ct.includes('application/json')) {
        const j = await res.json()
        detail = j.error?.message ?? j.detail ?? JSON.stringify(j)
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

  const data = await res.json()
  clearTimeout(timeoutId)
  return data.choices?.[0]?.message?.content || ''
}

export { isLocalUrl, validateLocalModelUrl, streamChatCompletion, chatCompletion }