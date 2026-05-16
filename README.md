# AI个人智能笔记助手 📝

一个基于 **Vue 3 + FastAPI + LM Studio**（或其它 OpenAI 兼容推理端）的全栈智能笔记应用，支持笔记管理、AI 生成/总结/翻译、思维导图与个人自带模型（BYOK）。

![Vue](https://img.shields.io/badge/Vue-3.3-brightgreen)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-blue)
![Python](https://img.shields.io/badge/Python-3.10+-yellow)

## ✨ 核心功能

### 📝 笔记管理
- 富文本（WangEditor）与 Markdown 双模式编辑
- 标签、搜索、筛选与收藏
- 历史笔记入口
- 导入 Word（`.docx`）与 TXT；支持与后端校验相关的合并/覆盖流程（详见接口）

### 🤖 AI 智能助手
- **生成**：主题 / 关键词、字数滑块，可选参考笔记与参考图片（列表仅由上传组件展示，避免重复）；输出格式 Markdown / Word / 纯文本
- **总结**：基于选定笔记或上传内容
- **翻译**：多目标语言（非中英文选项附带中文说明），译文含水印与脚注；**服务端**将 HTML 先转为 Markdown 再流式翻译，前端以 Markdown 渲染；有单次字数上限（以服务端为准）
- **对话**：首页助手面板，支持上下文与 `/note` 等指令（详见前端交互）

### 🗺️ 其它页面
- **思维导图**：独立路由 `/mindmap`（需登录）

### 📊 数据可视化
- 首页笔记统计（ECharts）、最近笔记等模块（Redis 可缓存加速）

### 🔐 用户系统
- JWT 注册 / 登录
- **个人中心**：资料与密码；可选配置「自带密钥」下的推理 **API 基址 / 模型 / Key**（与后端 Fernet 加密存储对齐）

### 💾 缓存（Redis）
- 用于「最近笔记」等；**未安装或未启动 Redis 时仍可正常使用**（降级逻辑见 `backend/app/core/redis_client.py`）

### 📖 使用手册
- 登录后通过顶部导航 **「使用手册」** 打开（路由 **`/manual`**），含项目介绍、操作说明、用户协议、隐私说明与反馈入口

### 🧭 前端路由缓存
- `keep-alive` 缓存首页、AI 生成/总结/**翻译笔记**、笔记列表/编辑/历史、使用手册等，切换路由后常见表单状态可保留（见 `frontend/src/App.vue`）

---

## 🏗️ 技术架构

### 前端
| 类别 | 技术 |
|------|------|
| 框架 | Vue 3（Composition API）、Vue Router 4、Pinia |
| UI | Element Plus |
| 富文本 | WangEditor |
| 图表 | ECharts |
| Markdown / 消毒 | Marked、isomorphic-dompurify |
| Word 导入 | Mammoth |
| 测试 | Vitest（`npm run test`） |
| 构建 | Vite 5（默认端口 **5174**） |

### 后端
| 类别 | 技术 |
|------|------|
| 框架 | FastAPI、Pydantic v2、Uvicorn |
| 数据 | MySQL + SQLAlchemy 2.x（异步 aiomysql） |
| AI | `openai` SDK，`LM_STUDIO_URL` / `LM_STUDIO_MODEL`；支持用户 BYOK 与会话级客户端（`llm_runtime`、`openai_client`） |
| 密钥加密 | `field_crypto`（`ENCRYPTION_KEY` 可选，否则由 `SECRET_KEY` 派生） |
| 其它 | JWT、Bcrypt、python-docx、Redis、`beautifulsoup4` |

---

## 📁 项目结构（节选）

```
note-takingAssistant/
├── .github/workflows/ci.yml   # 前端 build/test + 后端 pytest 等
├── backend/
│   ├── app/
│   │   ├── api/v1/           # user, note, ai
│   │   ├── core/             # config, security, database, redis_client, field_crypto, startup_migrations
│   │   ├── crud/, models/, services/, utils/
│   ├── migrations/           # SQLAlchemy 外的小型迁移脚本
│   ├── tests/                # pytest（含加密与 URL 规范化等）
│   ├── .env.example
│   ├── PROMPT_DESIGN_GUIDE.md
│   └── README.md             # 接口与环境说明（更细的 API 列表）
├── frontend/
│   ├── src/
│   │   ├── api/, router/, store/, utils/
│   │   ├── views/auth/, notes/, ai/, user/, mindmap/
│   │   ├── components/, composables/
│   └── vite.config.js
└── README.md                  # 本文件
```

---

## 🚀 快速开始

### 前置条件
- **Node.js** ≥ 18（推荐 20.x）
- **Python** ≥ 3.10
- **MySQL** ≥ 8.0
- **Redis**（可选）
- **推理端**：本机 [LM Studio](https://lmstudio.ai/) 或其它 OpenAI 兼容服务，`API 基址`须形如 **`…/v1`**（不要填浏览器里的 `…/v1/models`；服务端会对常见误填做规范化）

### CI（可选）
推送 / PR 时 [`.github/workflows/ci.yml`](.github/workflows/ci.yml) 会跑前端测试与构建、后端 `pytest` 等。本地示例：

```bash
cd frontend && npm ci && npm run test && npm run build
cd backend && pip install -r requirements.txt -r requirements-dev.txt && pytest -q
```

### 1. LM Studio（或其它兼容端）
1. 加载模型并启动 **Local Server**。
2. 在 `backend/.env` 中设置（模型 ID 须与界面一致）：
   - `LM_STUDIO_URL`，例如 `http://127.0.0.1:1234/v1`
   - `LM_STUDIO_MODEL`

### 2. 后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS
pip install -r requirements.txt
copy .env.example .env          # 或 cp；再编辑 .env
```

必填：`DB_*`、`SECRET_KEY`、`LM_STUDIO_URL`、`LM_STUDIO_MODEL`。可选：`REDIS_*`、`OPENAI_API_KEY`、`ENCRYPTION_KEY`（BYOK 加密；不配则从 `SECRET_KEY` 派生，**轮换 `SECRET_KEY` 后用户需在个人中心重新保存自带 Key**）。

数据库名称须与 `.env` 中 `DB_NAME` 一致（模板默认为 `note_db`）：

```sql
CREATE DATABASE note_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API 文档：<http://localhost:8000/docs>

### 3. 前端

```bash
cd frontend
npm install
copy .env.example .env
```

`frontend/.env` 中 `VITE_API_BASE_URL` 指向后端（开发环境也可依赖 Vite 将 `/api` 代理到该地址，见 `vite.config.js`）。

```bash
npm run dev
```

默认：<http://localhost:5174>

---

## 📖 使用提示（简要）

| 功能 | 路径 / 说明 |
|------|-------------|
| AI 生成 | `/ai/generate` — 参考笔记与参考图片通过上传区管理 |
| AI 总结 | `/ai/summarize` |
| 翻译笔记 | `/ai/translate` — 切换路由后表单一般由 `keep-alive` 保留 |
| 思维导图 | `/mindmap` |
| 个人中心 / BYOK | `/user` |
| 使用手册 | `/manual` — 应用内用户文档（需登录） |

---

## 📚 更多文档

- **终端用户**：登录后打开 **使用手册**（`/manual`），无需单独维护仓库内 Markdown 用户指南
- [`backend/README.md`](backend/README.md) — 后端 API 列表与环境变量
- [`backend/PROMPT_DESIGN_GUIDE.md`](backend/PROMPT_DESIGN_GUIDE.md) — 提示词与模型侧约定（若有）

---

## 🔧 开发命令摘要

```bash
# 后端
cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000
cd backend && pytest

# 前端
cd frontend && npm run dev
cd frontend && npm run build && npm run preview
cd frontend && npm run test
```

---

## ❓ 常见问题

- **AI 很慢或超时**：确认推理端已启动；可适当放宽后端 LLM HTTP 超时配置（见 `config`）；换更小模型。
- **Redis 报错**：可忽略或使用缓存；检查 `.env` 中 Redis 地址。
- **BYOK / 基址错误**：OpenAI 兼容 **`base_url` 应止于 `/v1`**；模型 ID 须与 LM Studio（或服务端）展示的一致。
- **前端空白**：看控制台与 Network；确认 `VITE_API_BASE_URL` / 代理与后端端口一致。

---

## 🤝 贡献

欢迎 Issue / PR：建议小步提交，便于评审。

## 📄 许可

如无特别声明，本项目可按 **MIT** 思路自由使用；若仓库后续补充 `LICENSE` 文件，以文件正文为准。

---

**最后更新**：2026-05-15  
