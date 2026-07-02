import api from './index'
import { streamPlainTextPost } from '@/utils/streamPlainTextPost'
import { streamChatCompletion, chatCompletion } from '@/utils/localLlmClient'
import { getApiBaseUrl } from './index'

const AI_REQUEST_TIMEOUT_MS =
  Number(import.meta.env.VITE_AI_REQUEST_TIMEOUT_MS) || 600_000

const NOTE_GENERATION_SYSTEM_PROMPT = `你是一位专业的学习笔记助手，专门为大学生和自学者创建高质量的学习笔记。

你的特点：
1. 结构清晰：使用标题、列表、重点标注等方式组织内容
2. 深入浅出：用通俗易懂的语言解释复杂概念
3. 实用导向：注重知识点的实际应用和考试要点
4. 格式规范：使用 Markdown 格式，包含适当的标题层级、列表、代码块等

输出要求：
- 使用 Markdown 格式
- 包含清晰的标题层级（# ## ###）
- 重要概念使用 **加粗** 标注
- 代码示例使用 \`\`\`代码块\`\`\`
- 适当使用列表（有序/无序）
- 字数控制在 500-800 字
- 语言简洁明了，适合学习复习`

const NOTE_ANALYSIS_SYSTEM_PROMPT = `你是一位经验丰富的学习笔记评审专家，擅长评估笔记质量并提供改进建议。

你的分析维度：
1. 内容完整性：是否覆盖了主题的核心知识点
2. 结构清晰度：逻辑是否清晰，层次是否分明
3. 表达准确性：概念解释是否准确，语言是否通顺
4. 实用性：是否便于复习和理解

输出要求：
- 必须返回严格的 JSON 格式
- summary: 150字以内的精炼总结
- strengths: 3个优点（具体、有针对性）
- weaknesses: 3个不足（建设性批评）
- suggestions: 3条改进建议（可操作、具体）
- 所有评价都要基于笔记实际内容，避免空泛`

const CHAT_SYSTEM_PROMPT = `你是一位NoteMind，专门帮助用户管理和优化学习笔记。

你的能力：
1. 回答关于学习方法、笔记技巧的问题
2. 帮助总结和优化笔记内容
3. 提供学习建议和知识解释
4. 协助整理和组织笔记结构

你的特点：
- 友好、专业、耐心
- 回答简洁明了，重点突出
- 适当使用 Markdown 格式增强可读性
- 鼓励用户主动学习和思考

注意：
- 如果用户询问与笔记无关的问题，友好地引导回学习主题
- 保持回答的实用性和可操作性
- 避免过于冗长的回答
- 当系统消息中出现「附加上下文」或「笔记内容」时，必须基于其中提供的正文作答，不要声称未收到或未阅读笔记。`

const NOTE_TRANSLATION_SYSTEM_PROMPT = `You are a professional translator for study notes.

Rules:
1. Output ONLY the translated document. No preamble, no postscript, no phrases like "Here is the translation".
2. Preserve Markdown structure: heading levels (# ## ###), lists, blockquotes, links, tables, and fenced code blocks (\`\`\` ... \`\`\`) exactly as structure; keep code inside fences unchanged — do not translate identifiers, keywords, or string literals inside code blocks.
3. Translate inline code (\`like this\`) only when it is natural language; if it looks like a symbol or API name, keep it.
4. Match the tone of educational / technical notes.
5. Do NOT append signatures, watermarks, or footers — the application will add one line at the end.`

const TARGET_LANGUAGE_LABELS = {
  zh: 'Simplified Chinese (简体中文)',
  en: 'English',
  ja: 'Japanese (日本語)',
  ko: 'Korean (한국어)',
  fr: 'French (français)',
  es: 'Spanish (español)'
}

async function getLocalLLMSettings() {
  if (typeof window !== 'undefined' && window.electronAPI?.store?.get) {
    try {
      const settings = await window.electronAPI.store.get('local_llm_settings')
      if (settings && typeof settings === 'object') {
        return settings
      }
    } catch {
      /* ignore */
    }
  }
  return null
}

async function useLocalModel() {
  const settings = await getLocalLLMSettings()
  return !!(settings?.enabled && settings?.baseUrl)
}

async function getLocalLLMConfig() {
  const settings = await getLocalLLMSettings()
  if (settings?.enabled && settings?.baseUrl) {
    return {
      baseUrl: settings.baseUrl,
      model: settings.model || 'gpt-3.5-turbo',
      apiKey: settings.apiKey || ''
    }
  }
  return null
}

function buildTranslationPrompt(content, targetLang) {
  const langLabel = TARGET_LANGUAGE_LABELS[targetLang?.toLowerCase()] || targetLang
  const userPrompt = `目标语言：${langLabel}

请翻译以下笔记全文（保持 Markdown 与代码块规则见系统说明）：

---
${content}
---`
  return [
    { role: 'system', content: NOTE_TRANSLATION_SYSTEM_PROMPT },
    { role: 'user', content: userPrompt }
  ]
}

function buildGenerationPrompt(topic, keyword, referenceNotes, wordCount) {
  let userPrompt = `请为主题「${topic}」生成一篇学习笔记。`

  if (keyword) {
    userPrompt += `\n\n重点关注的关键词：${keyword}`
  }

  if (referenceNotes && referenceNotes.length > 0) {
    userPrompt += '\n\n以下是参考材料，请结合这些内容生成笔记：\n'
    referenceNotes.forEach((note, i) => {
      const filename = note.filename || '未知文件'
      let content = note.content || ''
      if (content.length > 2000) {
        content = content.slice(0, 2000) + '...（内容过长，已截断）'
      }
      userPrompt += `\n【参考资料${i + 1} - ${filename}】\n${content}`
    })
  }

  userPrompt += '\n\n请按照以下结构生成笔记：\n'
  userPrompt += '1. 核心概念介绍\n'
  userPrompt += '2. 关键知识点详解（分点阐述）\n'
  userPrompt += '3. 实际应用或示例\n'
  userPrompt += '4. 总结与复习要点\n'

  const minWords = Math.max(300, (wordCount || 600) - 100)
  const maxWords = (wordCount || 600) + 100
  userPrompt += `\n字数要求：${minWords}-${maxWords}字左右\n`

  return [
    { role: 'system', content: NOTE_GENERATION_SYSTEM_PROMPT },
    { role: 'user', content: userPrompt }
  ]
}

function buildSummarizePrompt(content) {
  const userPrompt = `请对以下学习笔记进行专业分析和评估：

【笔记内容】
${content}

请从以下几个维度进行分析：
1. 内容完整性：是否覆盖了主题的核心知识点
2. 结构清晰度：逻辑是否清晰，层次是否分明
3. 表达准确性：概念解释是否准确，语言是否通顺
4. 实用性：是否便于复习和理解

请以严格的 JSON 格式返回分析结果，不要包含其他文字或 Markdown 标记。`
  return [
    { role: 'system', content: NOTE_ANALYSIS_SYSTEM_PROMPT },
    { role: 'user', content: userPrompt }
  ]
}

function buildChatMessages(message, history) {
  const messages = [{ role: 'system', content: CHAT_SYSTEM_PROMPT }]
  if (history && history.length > 0) {
    messages.push(...history.map(h => ({ role: h.role, content: h.content })))
  }
  messages.push({ role: 'user', content: message })
  return messages
}

export async function translateNoteStream({ content, targetLang, onChunk, signal }) {
  const isLocal = await useLocalModel()

  if (isLocal) {
    const localConfig = await getLocalLLMConfig()
    const messages = buildTranslationPrompt(content, targetLang)
    return streamChatCompletion({
      baseUrl: localConfig.baseUrl,
      apiKey: localConfig.apiKey,
      model: localConfig.model,
      messages,
      onChunk,
      signal
    })
  }

  const base = getApiBaseUrl().replace(/\/$/, '')
  await streamPlainTextPost({
    url: `${base}/v1/ai/translate-note/stream`,
    body: { content, target_lang: targetLang },
    onChunk,
    signal,
    timeoutMs: AI_REQUEST_TIMEOUT_MS
  })
}

export async function generateNoteStream({
  topic,
  keywords,
  wordCount,
  images,
  referenceNotes,
  onChunk,
  signal
}) {
  const isLocal = await useLocalModel()

  if (isLocal) {
    const localConfig = await getLocalLLMConfig()
    const messages = buildGenerationPrompt(topic, keywords, referenceNotes, wordCount)
    return streamChatCompletion({
      baseUrl: localConfig.baseUrl,
      apiKey: localConfig.apiKey,
      model: localConfig.model,
      messages,
      onChunk,
      signal
    })
  }

  const base = getApiBaseUrl().replace(/\/$/, '')
  await streamPlainTextPost({
    url: `${base}/v1/ai/generate-note/stream`,
    body: { topic, keywords, word_count: wordCount, images, reference_notes: referenceNotes },
    onChunk,
    signal,
    timeoutMs: AI_REQUEST_TIMEOUT_MS
  })
}

export async function chatStream({ message, history, onChunk, signal }) {
  const isLocal = await useLocalModel()

  if (isLocal) {
    const localConfig = await getLocalLLMConfig()
    const messages = buildChatMessages(message, history)
    return streamChatCompletion({
      baseUrl: localConfig.baseUrl,
      apiKey: localConfig.apiKey,
      model: localConfig.model,
      messages,
      onChunk,
      signal
    })
  }

  const base = getApiBaseUrl().replace(/\/$/, '')
  await streamPlainTextPost({
    url: `${base}/v1/ai/chat/stream`,
    body: { message, history },
    onChunk,
    signal,
    timeoutMs: AI_REQUEST_TIMEOUT_MS
  })
}

export const aiApi = {
  async generateNote(data) {
    const isLocal = await useLocalModel()

    if (isLocal) {
      const localConfig = await getLocalLLMConfig()
      const messages = buildGenerationPrompt(
        data.topic,
        data.keywords,
        data.referenceNotes,
        data.wordCount
      )
      const result = await chatCompletion({
        baseUrl: localConfig.baseUrl,
        apiKey: localConfig.apiKey,
        model: localConfig.model,
        messages
      })
      return { code: 200, message: '生成成功', data: { content: result } }
    }

    return api.post('/v1/ai/generate-note', data)
  },

  async summarizeNote(data) {
    const isLocal = await useLocalModel()

    if (isLocal) {
      const localConfig = await getLocalLLMConfig()
      const messages = buildSummarizePrompt(data.content)
      const result = await chatCompletion({
        baseUrl: localConfig.baseUrl,
        apiKey: localConfig.apiKey,
        model: localConfig.model,
        messages
      })

      let resultText = (result || '').trim()
      if (resultText.includes('```json')) {
        resultText = resultText.split('```json')[1].split('```')[0].trim()
      } else if (resultText.includes('```')) {
        resultText = resultText.split('```')[1].split('```')[0].trim()
      }
      resultText = resultText.replace(/,+$/g, '')

      let parsed
      try {
        parsed = JSON.parse(resultText)
      } catch {
        parsed = {
          summary: 'AI 分析完成，但返回格式有误',
          strengths: ['笔记结构清晰', '内容较为完整'],
          weaknesses: ['可以增加更多实例', '表达可以更精炼'],
          suggestions: ['建议补充相关案例', '优化段落结构']
        }
      }

      return {
        code: 200,
        message: '分析成功',
        data: {
          summary: parsed.summary || '暂无总结',
          strengths: parsed.strengths || ['笔记结构清晰'],
          weaknesses: parsed.weaknesses || ['可以增加更多实例'],
          suggestions: parsed.suggestions || ['建议补充相关案例']
        }
      }
    }

    return api.post('/v1/ai/summarize-note', data)
  },

  translateNoteStream,
  generateNoteStream,
  chatStream,

  async chat(data) {
    const isLocal = await useLocalModel()

    if (isLocal) {
      const localConfig = await getLocalLLMConfig()
      const messages = buildChatMessages(data.message, data.history)
      const result = await chatCompletion({
        baseUrl: localConfig.baseUrl,
        apiKey: localConfig.apiKey,
        model: localConfig.model,
        messages
      })
      return { reply: result }
    }

    return api.post('/v1/ai/chat', data)
  }
}
