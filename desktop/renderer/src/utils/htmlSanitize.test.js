import { describe, it, expect } from 'vitest'
import {
  sanitizeHtml,
  renderMarkdownToSafeHtml,
  isLikelyHtmlContent,
  sanitizeInlineAlignmentStyle
} from './htmlSanitize'

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
