# 智能笔记助手（AI 个人智能笔记助手）

一个面向个人学习与写作的 **Web 全栈应用**：用 Vue 3 构建交互界面，用 FastAPI 提供 REST API，通过 **OpenAI 兼容协议** 对接 [LM Studio](https://lmstudio.ai/) 或其它本地/云端大模型，实现笔记管理与 AI 辅助创作。

![Vue](https://img.shields.io/badge/Vue-3.3-brightgreen)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-blue)
![Python](https://img.shields.io/badge/Python-3.10+-yellow)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange)

---

## 项目简介

本系统采用前后端分离架构，用户注册登录后即可：

- 创建、编辑、检索与收藏笔记（富文本 / Markdown）；
- 使用 AI 生成、总结、翻译笔记，或在首页与助手对话；
- 在个人中心配置自带模型地址与 API Key（BYOK）。

未登录访客可浏览**欢迎页**（产品介绍、功能说明、平台注册趋势统计）。

---

## 功能特性

### 欢迎页与站点导航

| 能力 | 说明 |
|------|------|
| 产品介绍 | 功能亮点、下载占位、锚点导航 |
| 平台统计 | 公开接口展示注册用户总量与近 30 日每日新增（ECharts 图表） |
| 统一页脚 | 品牌、产品/资源/账户链接；GitHub 外链 |
| 登录 / 注册 | 独立认证页，手绘风格图标与品牌视觉 |

### 笔记管理

| 能力 | 说明 |
|------|------|
| 双模式编辑 | WangEditor 富文本 + Markdown（Marked 渲染，DOMPurify 消毒） |
| 组织与检索 | 标签、搜索、筛选、收藏 |
| 历史笔记 | 独立历史列表入口 |
| 导入 | Word（`.docx`，Mammoth）、纯文本；支持与后端校验的合并/覆盖流程 |
| 图片上传 | 笔记内图片上传至服务端静态目录 |

### AI 智能能力

| 能力 | 说明 |
|------|------|
| **AI 生成** | 按主题/关键词与字数生成笔记；可选参考笔记、参考图；输出 Markdown / Word / 纯文本 |
| **AI 总结** | 基于选定笔记或上传内容生成摘要 |
| **AI 翻译** | 多目标语言；服务端 HTML→Markdown 后**流式**翻译，前端 Markdown 展示；含水印与脚注 |
| **AI 对话** | 首页助手面板，支持多轮上下文；提供流式接口 `/chat-stream` |
| **流式输出** | 生成、翻译、对话均支持流式响应，降低首字等待时间 |
| **超时与连接** | 可配置 LLM HTTP 读超时；本地推理默认不走系统代理（`LLM_HTTP_TRUST_ENV`） |

推理默认读取 `backend/.env` 中的 `LM_STUDIO_URL`、`LM_STUDIO_MODEL`；用户可在个人中心覆盖基址、模型与 Key。

### 首页与数据展示

- 笔记数量等统计（ECharts）
- **最近笔记**（Redis 缓存加速，未启用 Redis 时自动降级）
- AI 助手聊天区：上下文对话、`/note` 等快捷指令、跳转最新消息

### 其它功能页面

| 路由 | 功能 |
|------|------|
| `/mindmap` | 思维导图（需登录） |
| `/manual` | 应用内使用手册（协议、隐私、操作说明） |
| `/user` | 个人中心：资料、密码、LLM / BYOK 配置 |

### 用户与安全

- **JWT** 注册、登录、退出；令牌黑名单（Redis）
- **BYOK**：用户 API Key 使用 Fernet 加密存库（`ENCRYPTION_KEY` 可选，否则由 `SECRET_KEY` 派生）
- **OpenAI 兼容 URL 规范化**：自动纠正误填的 `/v1/models` 等路径

### 工程与体验

- 前端 `keep-alive` 缓存主要业务页，切换路由时保留表单状态
- 前端按路由懒加载；`mermaid` / `echarts` 等大库在对应页面动态 `import`，减小首屏体积
- Element Plus 图标按需在各页面引入，避免全量注册
- GitHub Actions CI：前端 `vitest` + 构建、后端 `pytest`
- AI 调用失败时返回可操作的连接/鉴权/模型提示（见 `app/utils/llm_errors.py`）

---

## 技术栈

### 前端

| 类别 | 技术 | 用途 |
|------|------|------|
| 框架 | **Vue 3**（Composition API） | 视图与组件 |
| 路由 / 状态 | **Vue Router 4**、**Pinia** | 页面路由、用户态 |
| UI | **Element Plus** | 表单、布局、反馈 |
| 构建 | **Vite 5** | 开发服务器（默认 **5174**）、生产构建 |
| 富文本 | **WangEditor 4** | 笔记编辑 |
| 图表 | **ECharts 6** | 统计与欢迎页图表 |
| Markdown | **Marked** + **isomorphic-dompurify** | 渲染与安全过滤 |
| 文档处理 | **Mammoth** | Word 导入 |
| 图表 / 导出 | **Mermaid**、**canvg**、**html-to-image** | 导图与导出相关能力 |
| HTTP | **Axios** | API 请求（开发环境 `/api` 代理至后端） |
| 测试 | **Vitest** + **happy-dom** | 单元测试 |

### 后端

| 类别 | 技术 | 用途 |
|------|------|------|
| 框架 | **FastAPI**、**Pydantic v2**、**Uvicorn** | 异步 API 服务 |
| ORM | **SQLAlchemy 2.x** + **aiomysql** | 异步访问 MySQL |
| 认证 | **python-jose**、**bcrypt** | JWT、密码哈希 |
| AI 调用 | **openai**（AsyncOpenAI）+ **httpx** | 兼容 LM Studio / OpenAI API |
| 缓存 | **Redis** | 最近笔记、JWT 黑名单（可选） |
| 文档 | **python-docx** | Word 导出 |
| HTML 处理 | **BeautifulSoup4**、**html2text** | 翻译前 HTML 转换 |
| 加密 | **cryptography**（Fernet） | BYOK 密钥加密 |
| 测试 | **pytest** | 接口与工具函数测试 |

### 基础设施

| 类别 | 技术 |
|------|------|
| 数据库 | **MySQL 8.0** |
| 缓存 | **Redis 7**（可选） |
| CI | **GitHub Actions** |

### AI 接入方式

```
浏览器 → FastAPI → openai.AsyncOpenAI → LM Studio / 其它 OpenAI 兼容端点
                      ↑
              用户 BYOK（个人中心，可选）
```

更完整的分层说明见 [`docs/architecture.md`](docs/architecture.md)、数据模型见 [`docs/er-diagram.md`](docs/er-diagram.md)。

---

## 项目结构

```
note-takingAssistant/
├── .github/workflows/ci.yml      # CI：前端测试/构建 + 后端 pytest
├── backend/
│   ├── app/
│   │   ├── api/v1/               # user, note, ai, public
│   │   ├── core/                 # config, database, security, redis, field_crypto
│   │   ├── crud/                 # 数据访问
│   │   ├── models/               # Pydantic / ORM 模型
│   │   ├── services/             # AI 生成/总结/翻译/对话、LLM 运行时
│   │   └── utils/
│   ├── tests/
│   ├── main.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/                  # Axios 封装
│   │   ├── components/           # 布局、页脚、图标、欢迎页模块
│   │   ├── views/                  # auth, notes, ai, user, mindmap, help
│   │   ├── router/, store/, utils/
│   │   └── App.vue
│   ├── vite.config.js
│   └── package.json
├── docs/                         # 架构图、ER 图等
└── README.md
```

---

## 快速开始

### 环境要求

| 依赖 | 版本建议 | 说明 |
|------|----------|------|
| Node.js | ≥ 18（推荐 20） | 前端 |
| Python | ≥ 3.10 | 后端 |
| MySQL | ≥ 8.0 | 主数据库 |
| Redis | 可选 | 缓存与令牌黑名单 |
| LM Studio 等 | — | OpenAI 兼容 API，`…/v1` 为基址 |

### 本地开发

**1. 配置 LM Studio（或其它兼容端）**

- 加载模型并启动 **Local Server**
- 若开启 API Token，需在 `.env` 配置 `OPENAI_API_KEY=<你的 Token>`
- 设置 `LM_STUDIO_URL=http://127.0.0.1:1234/v1`（须含 `/v1`）
- `LM_STUDIO_MODEL` 与 LM Studio 中模型 ID 一致

**2. 后端**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate   # Linux / macOS
pip install -r requirements.txt
copy .env.example .env          # 编辑 DB_*、SECRET_KEY、LM_STUDIO_* 等
```

```sql
CREATE DATABASE note_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**3. 前端**

```bash
cd frontend
npm install
copy .env.example .env          # VITE_API_BASE_URL 指向后端
npm run dev
```

访问 http://localhost:5174

---

## 主要页面

| 路径 | 说明 |
|------|------|
| `/` | 欢迎页（未登录）/ 首页（已登录，含 AI 助手） |
| `/login`、`/register` | 登录、注册 |
| `/notes`、`/notes/edit/:id` | 笔记列表与编辑 |
| `/history` | 历史笔记 |
| `/ai/generate`、`/ai/summarize`、`/ai/translate` | AI 生成 / 总结 / 翻译 |
| `/mindmap` | 思维导图 |
| `/user` | 个人中心（含 BYOK） |
| `/manual` | 使用手册 |

---

## 开发命令

```bash
# 后端
cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000
cd backend && pytest -q

# 前端
cd frontend && npm run dev
cd frontend && npm run build && npm run preview
cd frontend && npm run test
```

---

## 更多文档

| 文档 | 内容 |
|------|------|
| [`backend/README.md`](backend/README.md) | 后端 API 与环境变量 |
| [`backend/PROMPT_DESIGN_GUIDE.md`](backend/PROMPT_DESIGN_GUIDE.md) | 提示词设计说明 |
| [`docs/architecture.md`](docs/architecture.md) | 系统架构图 |
| [`docs/er-diagram.md`](docs/er-diagram.md) | 数据库 ER 图 |
| 应用内 `/manual` | 终端用户操作手册 |

---

## 常见问题

**AI 报错 `Connection error` 或无法对话**

- 确认 LM Studio（或其它端）已启动 Local Server，且 `LM_STUDIO_URL` 端口正确。
- 若 LM Studio 要求 API Token，在 `backend/.env` 设置 `OPENAI_API_KEY`，或在个人中心填写 API Key。
- 用 PowerShell 自测：`Invoke-RestMethod http://127.0.0.1:1234/v1/models -Headers @{ Authorization = "Bearer 你的token" }`

**AI 很慢或超时**

- 换更小模型；增大 `LLM_HTTP_READ_TIMEOUT_SECONDS`（见 `backend/.env.example`）。

**Redis 连接失败**

- 可暂不启动 Redis，核心功能仍可用；最近笔记缓存会降级。

**BYOK / 基址填写**

- OpenAI 兼容 `base_url` 应止于 `/v1`，不要填 `/v1/models`；模型名须与推理端一致。

**前端接口 404 / 跨域**

- 检查 `VITE_API_BASE_URL` 与 Vite 代理（`vite.config.js`）是否与后端端口一致。

---

## 贡献与许可

欢迎提交 Issue / Pull Request。若无另行声明，可按 **MIT** 思路使用；若仓库包含 `LICENSE` 文件，以文件为准。

---

**最后更新**：2026-06-02
