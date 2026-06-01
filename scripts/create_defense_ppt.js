const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "AI 智能笔记助手";
pres.title = "基于大语言模型的智能笔记助手系统";

const C = {
  primary: "1E2761",
  secondary: "CADCFC",
  accent: "028090",
  dark: "1A1A2E",
  white: "FFFFFF",
  light: "F5F7FA",
  gray: "64748B",
  teal: "0D9488",
};

const FONT_TITLE = "Arial Black";
const FONT_BODY = "Arial";

const makeShadow = () => ({
  type: "outer",
  blur: 4,
  offset: 2,
  angle: 135,
  color: "000000",
  opacity: 0.1,
});

// ===== Slide 1: Title =====
let s1 = pres.addSlide();
s1.background = { color: C.primary };
s1.addShape(pres.shapes.RECTANGLE, {
  x: 0,
  y: 0,
  w: 0.12,
  h: 5.625,
  fill: { color: C.accent },
});
s1.addText("基于大语言模型的\n智能笔记助手系统", {
  x: 0.8,
  y: 1.0,
  w: 8.5,
  h: 2.2,
  fontSize: 36,
  fontFace: FONT_TITLE,
  color: C.white,
  bold: true,
  lineSpacingMultiple: 1.3,
});
s1.addText("设计与实现", {
  x: 0.8,
  y: 3.0,
  w: 5,
  h: 0.5,
  fontSize: 20,
  fontFace: FONT_BODY,
  color: C.secondary,
});
s1.addText("毕业设计答辩", {
  x: 0.8,
  y: 4.2,
  w: 4,
  h: 0.4,
  fontSize: 14,
  fontFace: FONT_BODY,
  color: C.secondary,
});

// ===== Slide 2: Contents =====
let s2 = pres.addSlide();
s2.background = { color: C.white };
s2.addShape(pres.shapes.RECTANGLE, {
  x: 0,
  y: 0,
  w: 10,
  h: 0.08,
  fill: { color: C.accent },
});
s2.addText("汇报提纲", {
  x: 0.6,
  y: 0.4,
  w: 5,
  h: 0.6,
  fontSize: 28,
  fontFace: FONT_TITLE,
  color: C.primary,
  margin: 0,
});
const items = [
  { num: "01", title: "项目背景与研究意义" },
  { num: "02", title: "系统技术架构" },
  { num: "03", title: "核心功能实现" },
  { num: "04", title: "关键技术难点" },
  { num: "05", title: "系统测试与结果" },
  { num: "06", title: "总结与展望" },
];
items.forEach((item, i) => {
  const yBase = 1.4 + i * 0.65;
  s2.addShape(pres.shapes.RECTANGLE, {
    x: 0.8,
    y: yBase,
    w: 0.65,
    h: 0.45,
    fill: { color: C.accent },
  });
  s2.addText(item.num, {
    x: 0.8,
    y: yBase,
    w: 0.65,
    h: 0.45,
    fontSize: 14,
    fontFace: FONT_BODY,
    color: C.white,
    align: "center",
    valign: "middle",
    bold: true,
  });
  s2.addText(item.title, {
    x: 1.7,
    y: yBase,
    w: 7,
    h: 0.45,
    fontSize: 16,
    fontFace: FONT_BODY,
    color: C.dark,
    valign: "middle",
    margin: 0,
  });
});

// ===== Slide 3: Background =====
let s3 = pres.addSlide();
s3.background = { color: C.white };
s3.addShape(pres.shapes.RECTANGLE, {
  x: 0,
  y: 0,
  w: 10,
  h: 0.08,
  fill: { color: C.accent },
});
s3.addText("项目背景与研究意义", {
  x: 0.6,
  y: 0.4,
  w: 6,
  h: 0.6,
  fontSize: 26,
  fontFace: FONT_TITLE,
  color: C.primary,
  margin: 0,
});
s3.addShape(pres.shapes.RECTANGLE, {
  x: 0.6,
  y: 1.1,
  w: 4.2,
  h: 3.8,
  fill: { color: C.light },
  shadow: makeShadow(),
});
s3.addText("现状与痛点", {
  x: 0.8,
  y: 1.2,
  w: 3.8,
  h: 0.4,
  fontSize: 16,
  fontFace: FONT_BODY,
  color: C.accent,
  bold: true,
  margin: 0,
});
s3.addText(
  [
    { text: "• 传统笔记工具缺乏智能处理能力", options: { breakLine: true } },
    { text: "• 云端 AI 笔记存在数据隐私隐患", options: { breakLine: true } },
    { text: "• 用户难以自由选择 AI 模型提供商", options: { breakLine: true } },
    { text: "• 开源 AI 笔记方案较少，扩展性差", options: {} },
  ],
  {
    x: 0.8,
    y: 1.7,
    w: 3.8,
    h: 2.8,
    fontSize: 13,
    fontFace: FONT_BODY,
    color: C.dark,
    lineSpacingMultiple: 1.6,
    valign: "top",
  }
);
s3.addShape(pres.shapes.RECTANGLE, {
  x: 5.3,
  y: 1.1,
  w: 4.2,
  h: 3.8,
  fill: { color: C.light },
  shadow: makeShadow(),
});
s3.addText("解决方案", {
  x: 5.5,
  y: 1.2,
  w: 3.8,
  h: 0.4,
  fontSize: 16,
  fontFace: FONT_BODY,
  color: C.teal,
  bold: true,
  margin: 0,
});
s3.addText(
  [
    { text: "• 深度集成大语言模型 AI 能力", options: { breakLine: true } },
    { text: "• 支持本地推理端，数据不出本机", options: { breakLine: true } },
    { text: "• BYOK 机制，用户自带模型和密钥", options: { breakLine: true } },
    { text: "• 全栈开源架构，方便定制扩展", options: {} },
  ],
  {
    x: 5.5,
    y: 1.7,
    w: 3.8,
    h: 2.8,
    fontSize: 13,
    fontFace: FONT_BODY,
    color: C.dark,
    lineSpacingMultiple: 1.6,
    valign: "top",
  }
);

// ===== Slide 4: Technology Stack =====
let s4 = pres.addSlide();
s4.background = { color: C.white };
s4.addShape(pres.shapes.RECTANGLE, {
  x: 0,
  y: 0,
  w: 10,
  h: 0.08,
  fill: { color: C.accent },
});
s4.addText("技术栈", {
  x: 0.6,
  y: 0.4,
  w: 5,
  h: 0.6,
  fontSize: 26,
  fontFace: FONT_TITLE,
  color: C.primary,
  margin: 0,
});
const techs = [
  { label: "前端", items: "Vue 3 + Element Plus + WangEditor + ECharts", color: C.accent },
  { label: "后端", items: "FastAPI + SQLAlchemy + Pydantic + JWT", color: C.teal },
  { label: "数据库", items: "MySQL (持久化) + Redis (缓存)", color: C.primary },
  { label: "AI 引擎", items: "LM Studio 本地推理 / OpenAI 兼容 API", color: "6D2E46" },
  { label: "部署", items: "Docker Compose + Nginx 反向代理", color: "B85042" },
];
techs.forEach((t, i) => {
  const yBase = 1.3 + i * 0.8;
  s4.addShape(pres.shapes.RECTANGLE, {
    x: 0.6,
    y: yBase,
    w: 1.4,
    h: 0.55,
    fill: { color: t.color },
  });
  s4.addText(t.label, {
    x: 0.6,
    y: yBase,
    w: 1.4,
    h: 0.55,
    fontSize: 13,
    fontFace: FONT_BODY,
    color: C.white,
    align: "center",
    valign: "middle",
    bold: true,
  });
  s4.addText(t.items, {
    x: 2.2,
    y: yBase,
    w: 7,
    h: 0.55,
    fontSize: 14,
    fontFace: FONT_BODY,
    color: C.dark,
    valign: "middle",
    margin: 0,
  });
});

// ===== Slide 5: Architecture =====
let s5 = pres.addSlide();
s5.background = { color: C.white };
s5.addShape(pres.shapes.RECTANGLE, {
  x: 0,
  y: 0,
  w: 10,
  h: 0.08,
  fill: { color: C.accent },
});
s5.addText("系统架构", {
  x: 0.6,
  y: 0.3,
  w: 5,
  h: 0.6,
  fontSize: 26,
  fontFace: FONT_TITLE,
  color: C.primary,
  margin: 0,
});
// Frontend layer
s5.addShape(pres.shapes.RECTANGLE, {
  x: 0.6,
  y: 1.1,
  w: 2.2,
  h: 1.2,
  fill: { color: "E0F2FE" },
});
s5.addText("前端展示层", {
  x: 0.6,
  y: 1.2,
  w: 2.2,
  h: 0.35,
  fontSize: 12,
  fontFace: FONT_BODY,
  color: C.primary,
  align: "center",
  bold: true,
  margin: 0,
});
s5.addText("Vue 3 SPA\nElement Plus\nECharts", {
  x: 0.6,
  y: 1.55,
  w: 2.2,
  h: 0.7,
  fontSize: 10,
  fontFace: FONT_BODY,
  color: C.gray,
  align: "center",
  margin: 0,
});
// Arrow
s5.addText("→", {
  x: 2.8,
  y: 1.3,
  w: 0.5,
  h: 0.8,
  fontSize: 24,
  color: C.accent,
  align: "center",
  valign: "middle",
});
// Backend layer
s5.addShape(pres.shapes.RECTANGLE, {
  x: 3.3,
  y: 1.1,
  w: 2.8,
  h: 1.2,
  fill: { color: "E0F2FE" },
});
s5.addText("后端服务层", {
  x: 3.3,
  y: 1.2,
  w: 2.8,
  h: 0.35,
  fontSize: 12,
  fontFace: FONT_BODY,
  color: C.primary,
  align: "center",
  bold: true,
  margin: 0,
});
s5.addText("FastAPI RESTful API\nJWT 认证 · 业务逻辑", {
  x: 3.3,
  y: 1.55,
  w: 2.8,
  h: 0.7,
  fontSize: 10,
  fontFace: FONT_BODY,
  color: C.gray,
  align: "center",
  margin: 0,
});
// Arrow
s5.addText("→", {
  x: 6.1,
  y: 1.3,
  w: 0.5,
  h: 0.8,
  fontSize: 24,
  color: C.accent,
  align: "center",
  valign: "middle",
});
// Data layer
s5.addShape(pres.shapes.RECTANGLE, {
  x: 6.6,
  y: 1.1,
  w: 2.8,
  h: 1.2,
  fill: { color: "E0F2FE" },
});
s5.addText("数据层", {
  x: 6.6,
  y: 1.2,
  w: 2.8,
  h: 0.35,
  fontSize: 12,
  fontFace: FONT_BODY,
  color: C.primary,
  align: "center",
  bold: true,
  margin: 0,
});
s5.addText("MySQL · Redis\n文件存储", {
  x: 6.6,
  y: 1.55,
  w: 2.8,
  h: 0.7,
  fontSize: 10,
  fontFace: FONT_BODY,
  color: C.gray,
  align: "center",
  margin: 0,
});
// AI layer
s5.addShape(pres.shapes.RECTANGLE, {
  x: 2.5,
  y: 2.8,
  w: 5,
  h: 1.2,
  fill: { color: "FEF3C7" },
});
s5.addText("AI 推理层", {
  x: 2.5,
  y: 2.9,
  w: 5,
  h: 0.35,
  fontSize: 12,
  fontFace: FONT_BODY,
  color: "B45309",
  align: "center",
  bold: true,
  margin: 0,
});
s5.addText("LM Studio 本地推理（Qwen/Llama 等）\nOpenAI 兼容云端 API\nBYOK 自带密钥机制", {
  x: 2.5,
  y: 3.25,
  w: 5,
  h: 0.7,
  fontSize: 10,
  fontFace: FONT_BODY,
  color: C.gray,
  align: "center",
  margin: 0,
});
// Connection from backend to AI
s5.addShape(pres.shapes.LINE, {
  x: 4.7,
  y: 2.3,
  w: 0,
  h: 0.5,
  line: { color: C.accent, width: 1.5, dashType: "dash" },
});
// Feature cards at bottom
const features = [
  { icon: "笔记管理", desc: "增删改查\n搜索分页\n富文本/MD" },
  { icon: "AI 生成", desc: "主题生成\n参考笔记\n流式输出" },
  { icon: "AI 翻译", desc: "多语种\n流式翻译\n格式保持" },
  { icon: "AI 对话", desc: "上下文感知\n笔记引用\n思维导图" },
];
features.forEach((f, i) => {
  const xBase = 0.6 + i * 2.35;
  s5.addShape(pres.shapes.RECTANGLE, {
    x: xBase,
    y: 4.3,
    w: 2.15,
    h: 1.1,
    fill: { color: C.light },
  });
  s5.addText(f.icon, {
    x: xBase + 0.1,
    y: 4.35,
    w: 1.95,
    h: 0.3,
    fontSize: 11,
    fontFace: FONT_BODY,
    color: C.accent,
    bold: true,
    margin: 0,
  });
  s5.addText(f.desc, {
    x: xBase + 0.1,
    y: 4.65,
    w: 1.95,
    h: 0.65,
    fontSize: 9,
    fontFace: FONT_BODY,
    color: C.gray,
    margin: 0,
  });
});

// ===== Slide 6: Core Features - Notes =====
let s6 = pres.addSlide();
s6.background = { color: C.white };
s6.addShape(pres.shapes.RECTANGLE, {
  x: 0,
  y: 0,
  w: 10,
  h: 0.08,
  fill: { color: C.accent },
});
s6.addText("核心功能 — 笔记管理", {
  x: 0.6,
  y: 0.4,
  w: 7,
  h: 0.6,
  fontSize: 26,
  fontFace: FONT_TITLE,
  color: C.primary,
  margin: 0,
});
const noteFeatures = [
  { title: "双模式编辑", desc: "富文本 (WangEditor) 与 Markdown 可实时切换，所见即所得" },
  { title: "智能搜索", desc: "支持标题+内容模糊搜索，按收藏状态筛选，后端分页查询" },
  { title: "笔记导入", desc: "支持 TXT / MD / DOCX 格式导入，自动检测重名并支持覆盖" },
  { title: "最近笔记", desc: "Redis 缓存最近 20 条记录，自动降级到 MySQL 查询" },
  { title: "统计可视化", desc: "ECharts 展示笔记数量趋势、AI 使用次数、活跃天数" },
];
noteFeatures.forEach((f, i) => {
  const yBase = 1.3 + i * 0.8;
  s6.addShape(pres.shapes.RECTANGLE, {
    x: 0.6,
    y: yBase,
    w: 8.5,
    h: 0.65,
    fill: { color: i % 2 === 0 ? C.light : C.white },
  });
  s6.addShape(pres.shapes.RECTANGLE, {
    x: 0.6,
    y: yBase,
    w: 0.06,
    h: 0.65,
    fill: { color: C.accent },
  });
  s6.addText(f.title, {
    x: 0.85,
    y: yBase + 0.02,
    w: 2,
    h: 0.3,
    fontSize: 12,
    fontFace: FONT_BODY,
    color: C.primary,
    bold: true,
    margin: 0,
  });
  s6.addText(f.desc, {
    x: 0.85,
    y: yBase + 0.3,
    w: 8,
    h: 0.3,
    fontSize: 10,
    fontFace: FONT_BODY,
    color: C.gray,
    margin: 0,
  });
});

// ===== Slide 7: Core Features - AI =====
let s7 = pres.addSlide();
s7.background = { color: C.white };
s7.addShape(pres.shapes.RECTANGLE, {
  x: 0,
  y: 0,
  w: 10,
  h: 0.08,
  fill: { color: C.accent },
});
s7.addText("核心功能 — AI 智能助手", {
  x: 0.6,
  y: 0.4,
  w: 7,
  h: 0.6,
  fontSize: 26,
  fontFace: FONT_TITLE,
  color: C.primary,
  margin: 0,
});
const aiCards = [
  { title: "AI 生成", desc: "输入主题/关键词\n参考已有笔记\n字数可调滑块\n输出 Markdown/Word" },
  { title: "AI 总结", desc: "分析笔记质量\n给出优缺点\n改进建议\nJSON 结构化输出" },
  { title: "AI 翻译", desc: "支持中英日韩法德\nHTML→Markdown→翻译\n流式文字输出\n译文含脚注水印" },
  { title: "AI 对话", desc: "首页侧边栏常驻\n/note 引用笔记\n40 条上下文记忆\n流式输出可中止" },
];
aiCards.forEach((card, i) => {
  const xBase = 0.4 + i * 2.35;
  s7.addShape(pres.shapes.RECTANGLE, {
    x: xBase,
    y: 1.2,
    w: 2.15,
    h: 3.8,
    fill: { color: C.light },
    shadow: makeShadow(),
  });
  s7.addShape(pres.shapes.RECTANGLE, {
    x: xBase,
    y: 1.2,
    w: 2.15,
    h: 0.5,
    fill: { color: C.accent },
  });
  s7.addText(card.title, {
    x: xBase + 0.1,
    y: 1.25,
    w: 1.95,
    h: 0.4,
    fontSize: 14,
    fontFace: FONT_BODY,
    color: C.white,
    bold: true,
    align: "center",
    margin: 0,
  });
  s7.addText(card.desc, {
    x: xBase + 0.15,
    y: 1.9,
    w: 1.85,
    h: 2.8,
    fontSize: 11,
    fontFace: FONT_BODY,
    color: C.dark,
    valign: "top",
    lineSpacingMultiple: 1.5,
    margin: 0,
  });
});

// ===== Slide 8: BYOK =====
let s8 = pres.addSlide();
s8.background = { color: C.white };
s8.addShape(pres.shapes.RECTANGLE, {
  x: 0,
  y: 0,
  w: 10,
  h: 0.08,
  fill: { color: C.accent },
});
s8.addText("BYOK 自带密钥机制", {
  x: 0.6,
  y: 0.4,
  w: 7,
  h: 0.6,
  fontSize: 26,
  fontFace: FONT_TITLE,
  color: C.primary,
  margin: 0,
});
s8.addShape(pres.shapes.RECTANGLE, {
  x: 0.6,
  y: 1.3,
  w: 4.3,
  h: 3.5,
  fill: { color: C.light },
  shadow: makeShadow(),
});
s8.addText("工作原理", {
  x: 0.8,
  y: 1.4,
  w: 3.9,
  h: 0.4,
  fontSize: 16,
  fontFace: FONT_BODY,
  color: C.accent,
  bold: true,
  margin: 0,
});
s8.addText(
  [
    { text: "1. 用户在个人中心配置 API 基址、模型、Key", options: { breakLine: true } },
    { text: "", options: { breakLine: true } },
    { text: "2. API Key 经 Fernet 加密后存入 MySQL", options: { breakLine: true } },
    { text: "", options: { breakLine: true } },
    { text: "3. AI 请求时解密 Key，构建 OpenAI 客户端", options: { breakLine: true } },
    { text: "", options: { breakLine: true } },
    { text: "4. 请求发送至用户指定的推理端点", options: { breakLine: true } },
    { text: "", options: { breakLine: true } },
    { text: "5. 返回前端时 Key 仅显示后 4 位", options: {} },
  ],
  {
    x: 0.8,
    y: 1.9,
    w: 3.9,
    h: 2.6,
    fontSize: 12,
    fontFace: FONT_BODY,
    color: C.dark,
    valign: "top",
    lineSpacingMultiple: 0.8,
    margin: 0,
  }
);
s8.addShape(pres.shapes.RECTANGLE, {
  x: 5.2,
  y: 1.3,
  w: 4.3,
  h: 3.5,
  fill: { color: C.light },
  shadow: makeShadow(),
});
s8.addText("技术优势", {
  x: 5.4,
  y: 1.4,
  w: 3.9,
  h: 0.4,
  fontSize: 16,
  fontFace: FONT_BODY,
  color: C.teal,
  bold: true,
  margin: 0,
});
s8.addText(
  [
    { text: "🔒 隐私保护：支持 LM Studio 本地推理", options: { breakLine: true } },
    { text: "", options: { breakLine: true } },
    { text: "🔑 灵活选择：自由切换模型提供商", options: { breakLine: true } },
    { text: "", options: { breakLine: true } },
    { text: "🛡 安全加密：Fernet AES-128 + HMAC", options: { breakLine: true } },
    { text: "", options: { breakLine: true } },
    { text: "📦 自动回退：未配置时使用服务端默认模型", options: {} },
  ],
  {
    x: 5.4,
    y: 1.9,
    w: 3.9,
    h: 2.6,
    fontSize: 12,
    fontFace: FONT_BODY,
    color: C.dark,
    valign: "top",
    lineSpacingMultiple: 0.8,
    margin: 0,
  }
);

// ===== Slide 9: Technical Highlights =====
let s9 = pres.addSlide();
s9.background = { color: C.white };
s9.addShape(pres.shapes.RECTANGLE, {
  x: 0,
  y: 0,
  w: 10,
  h: 0.08,
  fill: { color: C.accent },
});
s9.addText("关键技术难点与解决方案", {
  x: 0.6,
  y: 0.4,
  w: 8,
  h: 0.6,
  fontSize: 26,
  fontFace: FONT_TITLE,
  color: C.primary,
  margin: 0,
});
const techCards = [
  { title: "流式输出", desc: "AI 响应逐块推送，前端使用 AbortController 支持中途取消。显著降低用户等待感知。" },
  { title: "异步架构", desc: "FastAPI + aiomysql 全程异步，AI 请求不阻塞其他 API，提升并发吞吐能力。" },
  { title: "缓存降级", desc: "Redis 不可用时自动降级为 MySQL 查询，系统不中断，日志输出告警。" },
  { title: "XSS 防护", desc: "isomorphic-dompurify 双端消毒，Markdown 经 marked 渲染后再消毒，防止注入。" },
  { title: "Prompt 工程", desc: "角色定义 + 结构化约束 + 格式要求的三层提示词模板，保障 AI 输出质量。" },
  { title: "全文搜索", desc: "后端 SQL LIKE 模糊搜索 + 分页，替代低效的前端全量加载后过滤方案。" },
];
techCards.forEach((card, i) => {
  const col = i % 2;
  const row = Math.floor(i / 2);
  const xBase = 0.4 + col * 4.8;
  const yBase = 1.2 + row * 1.35;
  s9.addShape(pres.shapes.RECTANGLE, {
    x: xBase,
    y: yBase,
    w: 4.6,
    h: 1.2,
    fill: { color: C.light },
  });
  s9.addShape(pres.shapes.RECTANGLE, {
    x: xBase,
    y: yBase,
    w: 0.06,
    h: 1.2,
    fill: { color: C.accent },
  });
  s9.addText(card.title, {
    x: xBase + 0.2,
    y: yBase + 0.05,
    w: 4.2,
    h: 0.35,
    fontSize: 13,
    fontFace: FONT_BODY,
    color: C.primary,
    bold: true,
    margin: 0,
  });
  s9.addText(card.desc, {
    x: xBase + 0.2,
    y: yBase + 0.4,
    w: 4.2,
    h: 0.7,
    fontSize: 10,
    fontFace: FONT_BODY,
    color: C.gray,
    margin: 0,
  });
});

// ===== Slide 10: Testing =====
let s10 = pres.addSlide();
s10.background = { color: C.white };
s10.addShape(pres.shapes.RECTANGLE, {
  x: 0,
  y: 0,
  w: 10,
  h: 0.08,
  fill: { color: C.accent },
});
s10.addText("系统测试", {
  x: 0.6,
  y: 0.4,
  w: 5,
  h: 0.6,
  fontSize: 26,
  fontFace: FONT_TITLE,
  color: C.primary,
  margin: 0,
});
// Left: Frontend
s10.addShape(pres.shapes.RECTANGLE, {
  x: 0.6,
  y: 1.2,
  w: 4.3,
  h: 3.5,
  fill: { color: C.light },
  shadow: makeShadow(),
});
s10.addText("前端测试 (Vitest)", {
  x: 0.8,
  y: 1.3,
  w: 3.9,
  h: 0.4,
  fontSize: 16,
  fontFace: FONT_BODY,
  color: C.accent,
  bold: true,
  margin: 0,
});
s10.addText("27 tests 全部通过", {
  x: 0.8,
  y: 1.8,
  w: 3.9,
  h: 0.5,
  fontSize: 20,
  fontFace: FONT_BODY,
  color: C.accent,
  bold: true,
  margin: 0,
});
s10.addText(
  [
    { text: "✓ HTML 消毒 (XSS 防护)", options: { breakLine: true } },
    { text: "✓ Markdown 渲染安全", options: { breakLine: true } },
    { text: "✓ 日期格式化、文本处理", options: { breakLine: true } },
    { text: "✓ Mermaid 源码提取与修复", options: { breakLine: true } },
    { text: "✓ AI 上下文拼接逻辑", options: {} },
  ],
  {
    x: 0.8,
    y: 2.4,
    w: 3.9,
    h: 2,
    fontSize: 11,
    fontFace: FONT_BODY,
    color: C.dark,
    lineSpacingMultiple: 1.5,
    margin: 0,
  }
);
// Right: Backend
s10.addShape(pres.shapes.RECTANGLE, {
  x: 5.2,
  y: 1.2,
  w: 4.3,
  h: 3.5,
  fill: { color: C.light },
  shadow: makeShadow(),
});
s10.addText("后端测试 (pytest)", {
  x: 5.4,
  y: 1.3,
  w: 3.9,
  h: 0.4,
  fontSize: 16,
  fontFace: FONT_BODY,
  color: C.teal,
  bold: true,
  margin: 0,
});
s10.addText("11 tests 全部通过", {
  x: 5.4,
  y: 1.8,
  w: 3.9,
  h: 0.5,
  fontSize: 20,
  fontFace: FONT_BODY,
  color: C.teal,
  bold: true,
  margin: 0,
});
s10.addText(
  [
    { text: "✓ 密码哈希与验证", options: { breakLine: true } },
    { text: "✓ 字段加密与解密", options: { breakLine: true } },
    { text: "✓ API Key 掩码处理", options: { breakLine: true } },
    { text: "✓ URL 规范化", options: { breakLine: true } },
    { text: "✓ 健康检查接口", options: {} },
  ],
  {
    x: 5.4,
    y: 2.4,
    w: 3.9,
    h: 2,
    fontSize: 11,
    fontFace: FONT_BODY,
    color: C.dark,
    lineSpacingMultiple: 1.5,
    margin: 0,
  }
);

// ===== Slide 11: Demo Screenshots Placeholder =====
let s11 = pres.addSlide();
s11.background = { color: C.primary };
s11.addText("演示环节", {
  x: 0.6,
  y: 1.5,
  w: 8.5,
  h: 1,
  fontSize: 36,
  fontFace: FONT_TITLE,
  color: C.white,
  align: "center",
});
s11.addText("系统功能现场演示", {
  x: 0.6,
  y: 2.6,
  w: 8.5,
  h: 0.6,
  fontSize: 20,
  fontFace: FONT_BODY,
  color: C.secondary,
  align: "center",
});
s11.addText("请准备 Docker 或本地开发环境进行实时演示", {
  x: 0.6,
  y: 3.5,
  w: 8.5,
  h: 0.5,
  fontSize: 14,
  fontFace: FONT_BODY,
  color: C.secondary,
  align: "center",
});

// ===== Slide 12: Summary =====
let s12 = pres.addSlide();
s12.background = { color: C.white };
s12.addShape(pres.shapes.RECTANGLE, {
  x: 0,
  y: 0,
  w: 10,
  h: 0.08,
  fill: { color: C.accent },
});
s12.addText("总结与展望", {
  x: 0.6,
  y: 0.4,
  w: 5,
  h: 0.6,
  fontSize: 26,
  fontFace: FONT_TITLE,
  color: C.primary,
  margin: 0,
});
s12.addShape(pres.shapes.RECTANGLE, {
  x: 0.6,
  y: 1.2,
  w: 4.3,
  h: 3.5,
  fill: { color: C.light },
  shadow: makeShadow(),
});
s12.addText("已完成工作", {
  x: 0.8,
  y: 1.3,
  w: 3.9,
  h: 0.4,
  fontSize: 16,
  fontFace: FONT_BODY,
  color: C.accent,
  bold: true,
  margin: 0,
});
s12.addText(
  [
    { text: "✓ 全栈笔记管理系统", options: { breakLine: true } },
    { text: "✓ 四大 AI 智能功能", options: { breakLine: true } },
    { text: "✓ BYOK 自带密钥机制", options: { breakLine: true } },
    { text: "✓ 流式输出与异步架构", options: { breakLine: true } },
    { text: "✓ Docker 一键部署", options: { breakLine: true } },
    { text: "✓ 27+11 测试用例覆盖", options: {} },
  ],
  {
    x: 0.8,
    y: 1.8,
    w: 3.9,
    h: 2.6,
    fontSize: 12,
    fontFace: FONT_BODY,
    color: C.dark,
    lineSpacingMultiple: 1.6,
    margin: 0,
  }
);
s12.addShape(pres.shapes.RECTANGLE, {
  x: 5.2,
  y: 1.2,
  w: 4.3,
  h: 3.5,
  fill: { color: C.light },
  shadow: makeShadow(),
});
s12.addText("未来展望", {
  x: 5.4,
  y: 1.3,
  w: 3.9,
  h: 0.4,
  fontSize: 16,
  fontFace: FONT_BODY,
  color: C.teal,
  bold: true,
  margin: 0,
});
s12.addText(
  [
    { text: "• 多模态支持（图片理解 / OCR）", options: { breakLine: true } },
    { text: "• 团队协作与分享", options: { breakLine: true } },
    { text: "• 移动端适配 / PWA", options: { breakLine: true } },
    { text: "• 个性化智能推荐", options: { breakLine: true } },
    { text: "• 批量笔记处理", options: {} },
  ],
  {
    x: 5.4,
    y: 1.8,
    w: 3.9,
    h: 2.6,
    fontSize: 12,
    fontFace: FONT_BODY,
    color: C.dark,
    lineSpacingMultiple: 1.6,
    margin: 0,
  }
);

// ===== Slide 13: Thank You =====
let s13 = pres.addSlide();
s13.background = { color: C.primary };
s13.addText("谢谢！", {
  x: 0.6,
  y: 1.8,
  w: 8.5,
  h: 1,
  fontSize: 44,
  fontFace: FONT_TITLE,
  color: C.white,
  align: "center",
});
s13.addText("欢迎提问", {
  x: 0.6,
  y: 2.9,
  w: 8.5,
  h: 0.6,
  fontSize: 20,
  fontFace: FONT_BODY,
  color: C.secondary,
  align: "center",
});

pres.writeFile({ fileName: "C:\\Users\\MOM\\Desktop\\note-takingAssistant\\答辩PPT.pptx" })
  .then(() => console.log("PPT created successfully!"))
  .catch((err) => console.error("Error:", err));
