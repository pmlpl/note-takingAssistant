/** 欢迎页功能展示区（左右交替布局，图片懒加载） */
export const WELCOME_FEATURES = [
  {
    id: 'ai-generate',
    title: 'AI 智能生成',
    subtitle: '主题 + 关键词，一键成稿',
    description:
      '支持参考笔记与图片，输出 Markdown / Word / 纯文本。流式生成让你实时看到 AI 如何组织段落与结构，适合课程笔记、读书摘要与项目文档。',
    image: '/welcome/welcome-feature-ai.png',
    cta: '登录后体验生成',
    route: '/login',
  },
  {
    id: 'summarize-translate',
    title: '总结 · 翻译',
    subtitle: '读懂长文，跨语言整理',
    description:
      '基于选定笔记或上传内容智能总结核心要点；翻译模块将富文本转为 Markdown 后流式输出，便于复习与双语对照。',
    image: '/welcome/welcome-feature-summary.png',
    reverse: true,
    cta: '立即开始',
    route: '/register',
  },
  {
    id: 'mindmap',
    title: '思维导图',
    subtitle: '把笔记变成知识网络',
    description:
      '从首页助手或导图页将 Mermaid 源码可视化，梳理章节关系与概念层级，适合考前复盘与项目拆解。',
    image: '/welcome/welcome-feature-mindmap.png',
    cta: '查看开源仓库',
    external: 'https://github.com/pmlpl/note-takingAssistant',
  },
  {
    id: 'notes',
    title: '笔记管理',
    subtitle: '富文本 · 标签 · 搜索',
    description:
      'WangEditor 与 Markdown 双模式；「我的笔记」与历史笔记分区；导入 Word / TXT，配合 Redis 缓存最近浏览，学习路径更连贯。',
    image: '/welcome/welcome-feature-notes.png',
    reverse: true,
    cta: '免费注册',
    route: '/register',
  },
]

export const GITHUB_REPO_URL = 'https://github.com/pmlpl/note-takingAssistant'

export const GITHUB_ISSUES_URL = `${GITHUB_REPO_URL}/issues`

/** 标准页脚导航分组 */
export const FOOTER_NAV_GROUPS = [
  {
    id: 'product',
    title: '产品',
    links: [
      { label: '核心功能', anchor: '#features' },
      { label: '客户端下载', anchor: '#download' },
      { label: '平台数据', anchor: '#stats' },
    ],
  },
  {
    id: 'resources',
    title: '资源',
    links: [
      { label: '使用手册', route: '/manual' },
      { label: '开源仓库', external: GITHUB_REPO_URL },
      { label: '问题反馈', external: GITHUB_ISSUES_URL },
    ],
  },
  {
    id: 'account',
    title: '账户',
    links: [
      { label: '登录', route: '/login' },
      { label: '免费注册', route: '/register' },
    ],
  },
]

export const DOWNLOAD_PLACEHOLDERS = [
  {
    id: 'windows',
    label: 'Windows 客户端',
    ext: '.exe',
    hint: '桌面客户端规划中，请使用 Web 版',
    icon: 'monitor',
  },
  {
    id: 'android',
    label: 'Android 客户端',
    ext: '.apk',
    hint: '移动端开发中，敬请期待',
    icon: 'phone',
  },
]
