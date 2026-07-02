/**
 * NoteMind Welcome 页面常量配置
 * 100% 按照 notemind-welcome-design 设计稿
 */

// GitHub 仓库地址
export const GITHUB_REPO_URL = 'https://github.com/pmlpl/note-takingAssistant'

// Hero 区域技术栈标签 (按照设计稿顺序)
export const TECH_CHIPS = ['Vue 3', 'FastAPI', 'PostgreSQL', 'Redis', 'Docker', 'LM Studio']

// 四大核心功能 (按照设计稿)
export const WELCOME_FEATURES = [
  {
    icon: 'sparkles',
    title: 'AI 智能生成',
    subtitle: 'Smart Content Creation',
    description: '基于 GPT-4 驱动，智能生成课堂笔记、学习摘要和知识卡片。只需输入关键词，AI 自动为你构建结构清晰、内容详实的笔记。',
    image: '/welcome/welcome-feature-ai.png',
    cta: 'Try Now',
  },
  {
    icon: 'languages',
    title: '总结 · 翻译',
    subtitle: 'Summarize & Translate',
    description: '一键总结长篇笔记的核心要点，支持中英双语互译。快速提取关键信息，让你的学习资料更加精炼、高效。',
    image: '/welcome/welcome-feature-summary.png',
    cta: 'Try Now',
  },
  {
    icon: 'gitBranch',
    title: '思维导图',
    subtitle: 'Mind Mapping',
    description: '自动将笔记转化为可视化的思维导图，清晰呈现知识脉络与逻辑关系。支持拖拽编辑、自由调整布局。',
    image: '/welcome/welcome-feature-mindmap.png',
    cta: 'Try Now',
  },
  {
    icon: 'notebookPen',
    title: '笔记管理',
    subtitle: 'Note Management',
    description: '强大的笔记管理工具，支持标签分类、全文搜索、Markdown 编辑。你的每一份知识都能被有序保存和快速检索。',
    image: '/welcome/welcome-feature-notes.png',
    cta: 'Try Now',
  },
]

// 使用步骤 (按照设计稿)
export const HOW_IT_WORKS = [
  { step: 1, title: '注册账号', description: '填写基本信息，快速创建你的 NoteMind 账号。' },
  { step: 2, title: '创建笔记', description: '新建一个笔记本，输入课堂内容或上传学习资料。' },
  { step: 3, title: 'AI 处理', description: '一键调用 AI，自动生成摘要、翻译或思维导图。' },
  { step: 4, title: '高效学习', description: '随时回顾笔记，用导图梳理知识，持续提升效率。' },
]

// 统计数据 (按照设计稿 - 固定值，不需要从后端获取)
export const STATS_DATA = [
  { label: 'Active Users', displayValue: '10,000', suffix: '+', color: 'blue' },
  { label: 'Notes Created', displayValue: '50,000', suffix: '+', color: 'green' },
  { label: 'Uptime', displayValue: '99.9', suffix: '%', color: 'accent' },
  { label: 'Core Features', displayValue: '4', suffix: '', color: 'yellow' },
]

// 旧常量保留（兼容其他地方使用）
export const TECH_HIGHLIGHTS = TECH_CHIPS.map((chip) => ({ label: chip }))