import { describe, it, expect } from 'vitest'
import {
  formatDate,
  hasMeaningfulNoteText,
  shouldAttachNoteContext,
  clipNoteForAiContext,
  composeUserMessageWithNoteContext,
  prepareMermaidSourceForRender,
  extractMindmapDiagramSource,
  stripHtml,
  debounce,
  throttle,
  generateId,
} from './common'

describe('formatDate', () => {
  it('formats date correctly', () => {
    const result = formatDate('2026-05-16T10:30:00Z', 'YYYY-MM-DD')
    expect(result).toBe('2026-05-16')
  })
})

describe('hasMeaningfulNoteText', () => {
  it('returns false for null/empty', () => {
    expect(hasMeaningfulNoteText(null)).toBe(false)
    expect(hasMeaningfulNoteText('')).toBe(false)
  })

  it('returns true for plain text', () => {
    expect(hasMeaningfulNoteText('Hello world')).toBe(true)
  })

  it('returns true for rich content with images', () => {
    expect(hasMeaningfulNoteText('<img src="x.png" />')).toBe(true)
  })
})

describe('shouldAttachNoteContext', () => {
  it('returns false for null/empty', () => {
    expect(shouldAttachNoteContext(null)).toBe(false)
    expect(shouldAttachNoteContext('')).toBe(false)
  })

  it('returns true for non-empty', () => {
    expect(shouldAttachNoteContext('content')).toBe(true)
  })
})

describe('clipNoteForAiContext', () => {
  it('returns text unchanged if under limit', () => {
    expect(clipNoteForAiContext('short')).toBe('short')
  })
})

describe('composeUserMessageWithNoteContext', () => {
  it('wraps note content with user message', () => {
    const msg = composeUserMessageWithNoteContext('what is this?', 'MyNote', 'some content')
    expect(msg).toContain('MyNote')
    expect(msg).toContain('some content')
    expect(msg).toContain('what is this?')
  })
})

describe('prepareMermaidSourceForRender', () => {
  it('passes through non-mindmap sources', () => {
    const src = 'flowchart TD\nA-->B'
    expect(prepareMermaidSourceForRender(src)).toBe(src)
  })

  it('fixes risky mindmap lines', () => {
    const src = 'mindmap\n  root[主题]\n    [x for x in range]'
    const result = prepareMermaidSourceForRender(src)
    expect(result).toContain('mmdfix')
    expect(result).toContain('root[主题]')
  })
})

describe('extractMindmapDiagramSource', () => {
  it('extracts mermaid code block', () => {
    const md = 'text\n```mermaid\nflowchart TD\nA-->B\n```\nend'
    expect(extractMindmapDiagramSource(md)).toBe('flowchart TD\nA-->B')
  })

  it('extracts mindmap code block', () => {
    const md = '```mindmap\nroot\n  a\n```'
    expect(extractMindmapDiagramSource(md)).toBe('root\n  a')
  })

  it('returns empty for plain text', () => {
    expect(extractMindmapDiagramSource('hello')).toBe('')
  })
})

describe('stripHtml', () => {
  it('removes HTML tags', () => {
    expect(stripHtml('<p>Hello <b>World</b></p>')).toBe('Hello World')
  })
})

describe('generateId', () => {
  it('generates non-empty string', () => {
    expect(generateId().length).toBeGreaterThan(0)
  })
})
