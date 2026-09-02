import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  sanitizeHtml,
  renderMarkdownToSafeHtml,
  renderContentToSafeHtml,
  isLikelyHtmlContent,
  sanitizeInlineAlignmentStyle,
  hydrateMermaidBlocks
} from './htmlSanitize'

const mermaidMock = vi.hoisted(() => ({
  initialize: vi.fn(async () => {}),
  render: vi.fn(async () => ({ svg: '<svg><g>chart</g></svg>', bindFunctions: null }))
}))

vi.mock('mermaid', () => ({ default: mermaidMock }))

describe('sanitizeHtml', () => {
  it('removes script tags', () => {
    const out = sanitizeHtml('<p>hi</p><script>alert(1)</script>')
    expect(out.toLowerCase()).not.toContain('<script')
  })

  it('removes inline event handlers', () => {
    const out = sanitizeHtml('<img src="x" onerror="alert(1)">')
    expect(out.toLowerCase()).not.toContain('onerror')
  })

  it('keeps benign formatting', () => {
    const out = sanitizeHtml('<p><strong>x</strong></p>')
    expect(out).toContain('<strong>')
    expect(out).toContain('x')
  })

  it('keeps text-align in style and drops dangerous declarations', () => {
    const out = sanitizeHtml(
      '<p style="text-align: center; color: red; background: url(javascript:void)">Hi</p>'
    )
    expect(out.toLowerCase()).toContain('text-align')
    expect(out.toLowerCase()).toContain('center')
    expect(out.toLowerCase()).not.toContain('background')
    expect(out.toLowerCase()).not.toContain('javascript')
    expect(out).toContain('Hi')
  })

  it('keeps safe align attribute', () => {
    const out = sanitizeHtml('<p align="CENTER">x</p>')
    expect(out.toLowerCase()).toContain('center')
    expect(out).toContain('x')
  })

  it('keeps Word-like font-size and drops mso-* noise', () => {
    const out = sanitizeHtml(
      '<p style="text-align: center; font-size: 18.0pt; mso-bidi-font-size: 12.0pt"><strong>课程</strong></p>'
    )
    expect(out).toContain('text-align')
    expect(out).toContain('center')
    expect(out).toContain('font-size')
    expect(out).toContain('18')
    expect(out.toLowerCase()).not.toContain('mso-')
  })
})

describe('isLikelyHtmlContent', () => {
  it('detects common HTML fragments', () => {
    expect(isLikelyHtmlContent('<p>Hello</p>')).toBe(true)
    expect(isLikelyHtmlContent('<div class="x">a</div>')).toBe(true)
    expect(isLikelyHtmlContent('<table><tr><td>x</td></tr></table>')).toBe(
      true
    )
  })

  it('treats plain markdown as non-HTML', () => {
    expect(isLikelyHtmlContent('# Title\n\nHello **world**')).toBe(false)
    expect(isLikelyHtmlContent('just text')).toBe(false)
  })

  it('treats markdown with HTML inside code fences as markdown', () => {
    expect(isLikelyHtmlContent('## 示例\n\n```html\n<p>hi</p>\n```')).toBe(false)
    expect(isLikelyHtmlContent('```\n<div>raw</div>\n```')).toBe(false)
  })

  it('treats markdown lists/headings with inline tags as markdown', () => {
    expect(isLikelyHtmlContent('- item\n- <p>inline</p>')).toBe(false)
    expect(isLikelyHtmlContent('> 引用 <p>inline</p>')).toBe(false)
  })

  it('treats comparison expressions as non-HTML', () => {
    expect(isLikelyHtmlContent('1 < 2 and 3 > 4')).toBe(false)
    expect(isLikelyHtmlContent('a < b')).toBe(false)
  })

  it('detects doctype and comments as HTML', () => {
    expect(isLikelyHtmlContent('<!DOCTYPE html><html><body>x</body></html>')).toBe(
      true
    )
    expect(isLikelyHtmlContent('<!-- note -->\n<p>text</p>')).toBe(true)
  })

  it('detects known tags anywhere in text as HTML', () => {
    expect(isLikelyHtmlContent('text <p>inline</p>')).toBe(true)
    expect(isLikelyHtmlContent('text<br>more')).toBe(true)
  })

  it('keeps parity with backend tag list (bold is not HTML by itself)', () => {
    expect(isLikelyHtmlContent('<b>bold</b>')).toBe(false)
  })
})

describe('sanitizeInlineAlignmentStyle', () => {
  it('extracts text-align and margin auto', () => {
    expect(sanitizeInlineAlignmentStyle('text-align: center')).toBe(
      'text-align: center'
    )
    expect(
      sanitizeInlineAlignmentStyle('margin: 0px auto; text-align: right')
    ).toBe('margin: 0 auto; text-align: right')
  })

  it('keeps font-size and skips mso-*', () => {
    expect(
      sanitizeInlineAlignmentStyle(
        'font-size: 14.0pt; mso-font-kerning: 1.0pt; text-align: center'
      )
    ).toBe('font-size: 14.0pt; text-align: center')
  })
})

describe('renderMarkdownToSafeHtml', () => {
  it('renders markdown headings and paragraphs', () => {
    const out = renderMarkdownToSafeHtml('# Title\n\nHello **world**')
    expect(out).toContain('Title')
    expect(out).toContain('world')
  })

  it('strips dangerous URL schemes from links', () => {
    const out = renderMarkdownToSafeHtml('[click](javascript:alert(1))')
    expect(out.toLowerCase()).not.toContain('javascript:')
  })
})

describe('renderContentToSafeHtml', () => {
  it('returns empty string for empty input', () => {
    expect(renderContentToSafeHtml('')).toBe('')
    expect(renderContentToSafeHtml(null)).toBe('')
    expect(renderContentToSafeHtml(undefined)).toBe('')
  })

  it('sanitizes HTML content and keeps its structure', () => {
    const out = renderContentToSafeHtml('<table><tr><td>单元格</td></tr></table>')
    expect(out).toContain('<table>')
    expect(out).toContain('单元格')
  })

  it('renders markdown content', () => {
    const out = renderContentToSafeHtml('# Title\n\nHello **world**')
    expect(out).toContain('Title')
    expect(out).toContain('<strong>')
  })

  it('renders plain text with comparison expressions safely', () => {
    const out = renderContentToSafeHtml('1 < 2 and 3 > 4')
    expect(out).toContain('1 &lt; 2')
    expect(out).not.toContain('&lt;2 and')
  })

  it('keeps mermaid fence as a hydratable code block', () => {
    const out = renderContentToSafeHtml('```mermaid\nflowchart TD\nA-->B\n```')
    expect(out).toContain('language-mermaid')
    expect(out).toContain('flowchart')
  })
})

describe('hydrateMermaidBlocks', () => {
  beforeEach(() => {
    mermaidMock.initialize.mockClear()
    mermaidMock.render.mockClear()
    mermaidMock.render.mockResolvedValue({
      svg: '<svg><g>chart</g></svg>',
      bindFunctions: null
    })
  })

  it('renders mermaid code blocks into .mermaid-rendered divs', async () => {
    const container = document.createElement('div')
    container.innerHTML =
      '<pre><code class="language-mermaid">flowchart TD\nA--&gt;B</code></pre>'
    await hydrateMermaidBlocks(container)
    expect(container.querySelector('.mermaid-rendered')).toBeTruthy()
    expect(container.querySelector('svg')).toBeTruthy()
    expect(container.querySelector('pre')).toBeNull()
  })

  it('calls bindFunctions on the rendered holder when provided', async () => {
    const bindFunctions = vi.fn()
    mermaidMock.render.mockResolvedValueOnce({
      svg: '<svg></svg>',
      bindFunctions
    })
    const container = document.createElement('div')
    container.innerHTML =
      '<pre><code class="language-mermaid">graph LR\nA-->B</code></pre>'
    await hydrateMermaidBlocks(container)
    expect(bindFunctions).toHaveBeenCalledWith(
      container.querySelector('.mermaid-rendered')
    )
  })

  it('falls back to source code when mermaid render fails', async () => {
    mermaidMock.render.mockRejectedValueOnce(new Error('parse error'))
    const container = document.createElement('div')
    container.innerHTML =
      '<pre><code class="language-mermaid">flowchart TD\nA--&gt;B</code></pre>'
    await hydrateMermaidBlocks(container)
    const pre = container.querySelector('pre')
    expect(pre).toBeTruthy()
    expect(pre.classList.contains('mermaid-fallback')).toBe(true)
    expect(pre.dataset.mermaidState).toBe('fallback')
  })

  it('skips non-mermaid code blocks', async () => {
    const container = document.createElement('div')
    container.innerHTML =
      '<pre><code class="language-js">const a = 1</code></pre>'
    await hydrateMermaidBlocks(container)
    expect(mermaidMock.render).not.toHaveBeenCalled()
  })

  it('is a no-op without a container', async () => {
    await expect(hydrateMermaidBlocks(null)).resolves.toBeUndefined()
  })
})
