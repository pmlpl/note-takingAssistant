<div align="center">

<img src="docs/logo.svg" width="120" height="120" alt="NoteMind Logo">

# NoteMind

![Version](https://img.shields.io/badge/Version-1.1.0-10b981?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-f59e0b?style=for-the-badge)

</div>

<div align="center">

![Vue](https://img.shields.io/badge/Vue-3.3-42b883?style=for-the-badge&logo=vuedotjs&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)

</div>

---

## 🌠 项目简介

> 面向个人学习与创作的 **Web 全栈智能笔记应用**

- **前端**：Vue 3 + Element Plus，流畅的交互体验
- **后端**：FastAPI + 异步 MySQL/Redis，高并发稳
- **AI 能力**：基于 **OpenAI 兼容协议**，支持云端大模型
- **BYOK（自带密钥）**：Web 版需用户自行配置云端 API Key；桌面版可直连本机 LM Studio
- **密钥安全**：用户 API Key 使用 Fernet 对称加密存储，仅返回后四位掩码用于确认
- **桌面版优势**：桌面客户端可直接连接本机 LM Studio，AI 完全本地运行，无需云端依赖

**v1.1.0 功能总览**

| 模块 | 能力 |
|------|------|
| 📝 **笔记管理** | 创建 / 编辑 / 搜索 / 收藏 / 富文本 & Markdown |
| 🤖 **AI 辅助** | 生成笔记 / 总结 / 翻译 / 多轮对话（流式输出） |
| 🧠 **知识图谱** | 笔记与概念关联可视化，力导向布局，节点拖拽 |
| 🗺️ **思维导图** | 笔记结构可视化 |
| 📊 **数据统计** | 个人笔记统计 + 平台注册趋势图 |
| 🔐 **安全体系** | JWT 认证 / 密码复杂度校验 / 速率限制 / SSRF 防护 / BYOK 密钥加密 |
| 🐳 **一键部署** | Docker Compose 全套拉起，HTTPS 自动续期 |
| 🔗 **多种登录方式** | 邮箱密码 / 邮箱验证码 / GitHub OAuth |
| 👤 **账号管理** | 昵称修改 / 邮箱换绑 / GitHub 绑定解绑 |

---

## ✨ 功能亮点

### 核心功能

| 能力 | 说明 |
|------|------|
| **富文本 & Markdown 双模式** | WangEditor 富文本 + Marked 渲染，切换流畅 |
| **AI 笔记生成** | 按主题、关键词、字数生成；可参考已有笔记做扩展 |
| **AI 流式翻译** | HTML→Markdown 预处理，逐段流式返回，首字等待时间短 |
| **AI 对话助手** | 首页多轮对话面板，支持上下文与快捷指令 |
| **知识图谱** | 笔记与概念关联可视化，力导向布局，节点拖拽交互 |
| **AI 推理方式** | Web 版：用户自带云端 API Key；桌面版：直连本机 LM Studio 或云端 API |
| **多种登录方式** | 邮箱密码 / 邮箱验证码 / GitHub OAuth 一键登录 |
| **账号绑定管理** | 昵称修改、邮箱换绑、GitHub 绑定/解绑，多方式灵活管理 |

### 工程与安全

| 方面 | 说明 |
|------|------|
| **JWT 加固** | 2 小时短有效期 + 令牌代数(Token Gen) + Redis 黑名单登出 |
| **速率限制** | 匿名接口 60 次/分；AI 生成限流；防暴力注册/登录 |
| **SSRF 防护** | LLM 自定义 URL 校验协议/IP/端口，拦截内网请求 |
| **密码安全** | bcrypt 哈希 + 前端 8 位含字母数字强度校验 |
| **BYOK 加密** | 用户 API Key 使用 Fernet 对称加密存库，前端展示仅返回后四位掩码 |
| **文件上传安全** | 魔数校验 + 扩展名白名单 + 随机文件名重命名 |
| **日志体系** | 结构化 JSON 日志，便于排障与审计 |

---

## 🛠️ 技术栈

### 前端

| 技术 | 用途 |
|------|------|
| **Vue 3**（Composition API） | 视图与组件 |
| **Vue Router 4** + **Pinia** | 路由与状态 |
| **Element Plus** | 表单、布局、交互反馈 |
| **Vite 5** | 构建与开发服务器（5174 端口） |
| **WangEditor 4** | 富文本编辑 |
| **ECharts 6** | 统计图表 |
| **Marked** + **isomorphic-dompurify** | Markdown 渲染与 XSS 过滤 |
| **Axios** | 前后端通信 |
| **Mammoth** | Word 文档导入 |

### 后端

| 技术 | 用途 |
|------|------|
| **FastAPI** + **Pydantic v2** + **Uvicorn** | 异步 REST API 服务 |
| **SQLAlchemy 2.x** + **aiomysql** | 异步 MySQL ORM |
| **python-jose** + **bcrypt** | JWT 认证与密码哈希 |
| **openai** (AsyncOpenAI) + **httpx** | LLM 推理客户端 |
| **Redis** (redis-py 异步) | 缓存 + JWT 黑名单 + 限流 |
| **python-docx** | Word 导出 |
| **BeautifulSoup4** + **html2text** | HTML 预处理 |
| **cryptography** (Fernet) | BYOK 密钥加密 |
| **pytest** | 单元测试 |

### 部署

| 技术 | 用途 |
|------|------|
| **Docker** + **Docker Compose** | 容器化一键部署 |
| **Nginx** | 前端托管 + 反向代理 + HTTPS |
| **Certbot (Let's Encrypt)** | 免费 SSL 证书自动申请与续期 |

---

## 📁 项目结构

```
note-takingAssistant/
├── .github/workflows/ci.yml      # CI：前端测试/构建 + 后端 pytest
├── backend/
│   ├── app/
│   │   ├── api/v1/                # user, note, ai, public 路由
│   │   ├── core/                  # config, database, security, redis, logger
│   │   ├── crud/                  # 数据访问层
│   │   ├── models/                # Pydantic 请求/响应 + SQLAlchemy ORM
│   │   ├── services/              # AI 生成/总结/翻译/对话
│   │   └── utils/                 # 文件上传校验、LLM 错误处理、URL 安全
│   ├── main.py                    # FastAPI 入口
│   ├── requirements.txt
│   ├── .env.example
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── api/                   # Axios 请求封装
│   │   ├── components/            # 布局、图标、业务组件
│   │   ├── views/                 # auth, notes, ai, user, mindmap
│   │   ├── router/, store/, utils/
│   │   └── App.vue
│   ├── nginx.http.conf            # HTTP 模式配置（证书到位前）
│   ├── nginx.https.conf           # HTTPS 模式配置（证书到位后自动切换）
│   ├── entrypoint.sh              # Nginx 启动脚本（HTTP/HTTPS 自动切换）
│   ├── vite.config.js
│   └── package.json
├── docker-compose.yml             # ⭐ 生产部署核心文件
├── .env.docker                    # 生产环境变量模板
├── docs/                          # 架构图、ER 图等
└── README.md                      # 就是本文件
```

---

## 🚀 快速开始

### 方式一：本地开发（推荐用于调试）

**环境要求**：Node.js ≥ 18、Python ≥ 3.10、MySQL ≥ 8.0、Redis（可选）

#### 1. 启动 LM Studio（或其它 OpenAI 兼容服务）

```
下载模型 → 启动 Local Server → 基址形如 http://127.0.0.1:1234/v1
```

#### 2. 启动后端

```bash
cd backend
python -m venv .venv
# Windows:   .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env      # 编辑 DB_*、SECRET_KEY、LM_STUDIO_* 等

# 创建数据库
mysql -uroot -p -e "CREATE DATABASE note_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 启动
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. 启动前端

```bash
cd frontend
npm install
copy .env.example .env       # VITE_API_BASE_URL 指向后端
npm run dev
```

访问 http://localhost:5174

### 方式二：Docker Compose（生产部署 ⭐ 推荐）

#### 1. 服务器准备（Ubuntu 20.04+）

```bash
# 安装 Docker（官方脚本）
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

#### 2. 拉取代码并构建前端

```bash
git clone <你的仓库地址> note-app
cd note-app

cd frontend
npm install
npm run build
cd ..
```

#### 3. 生成随机密钥

```bash
cp .env.docker .env
# ⚠️ 把 .env 里的 DB_PASSWORD / REDIS_PASSWORD / SECRET_KEY 都换成随机长字符串
# 生成建议：
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
nano .env
```

#### 4. 一键启动

```bash
docker compose up -d --build

# 等 2-3 分钟，检查状态
docker compose ps
# 全部状态应为 Up / Up (healthy)
```

#### 5. 申请免费 HTTPS 证书（替换邮箱为你的）

```bash
docker compose run --rm certbot certonly --webroot \
    -w /var/www/certbot \
    -d momo.makeup -d www.momo.makeup \
    --email your@email.com --agree-tos --no-eff-email

# 证书到位后重启前端容器，自动从 HTTP 切换到 HTTPS
docker compose restart frontend
```

#### 6. 验证

```bash
# 浏览器打开
https://momo.makeup
# 应有 🔒 图标
```

> 💡 **证书自动续期**：certbot 容器每 12 小时检查一次，到期前自动续期，无需手动干预。

---

## 📄 API 文档

后端启动后访问：

- **Swagger UI**：http://localhost:8000/docs
- **Redoc**：http://localhost:8000/redoc

**主要接口一览**

| 模块 | 接口 |
|------|------|
| 👤 用户 | `POST /api/v1/user/register` · `POST /api/v1/user/login` · `POST /api/v1/user/logout` · `GET /api/v1/user/me` |
| 📝 笔记 | `POST /api/v1/note/` · `GET /api/v1/note/` · `GET /api/v1/note/{id}` · `PUT /api/v1/note/{id}` · `DELETE /api/v1/note/{id}` |
| 🤖 AI | `POST /api/v1/ai/generate-note` · `POST /api/v1/ai/summarize-note` · `POST /api/v1/ai/translate-note-stream` · `POST /api/v1/ai/chat-stream` |
| 🔐 OAuth | `GET /api/v1/oauth/github/authorize` · `GET /api/v1/oauth/github/callback` |
| 📧 邮箱验证码 | `POST /api/v1/auth/send-code` · `POST /api/v1/auth/login-by-code` |
| 🔗 账号绑定 | `GET /api/v1/user/me/bindings` · `PUT /api/v1/user/me/nickname` · `DELETE /api/v1/user/me/bindings/github` · `DELETE /api/v1/user/me/bindings/email` |
| 🌐 公开统计 | `GET /api/v1/public/stats` · `GET /api/v1/public/daily-registrations` |

---

## 🌐 页面路由

| 路径 | 页面 | 登录要求 |
|------|------|---------|
| `/` | 欢迎页 / 首页（AI 助手） | 未登录/已登录 |
| `/login`、`/register` | 登录 / 注册 | 否 |
| `/notes`、`/notes/edit/:id` | 笔记列表 / 编辑 | 是 |
| `/history` | 历史笔记 | 是 |
| `/ai/generate`、`/ai/summarize`、`/ai/translate` | AI 创作工具 | 是 |
| `/kg` | 知识图谱 | 是 |
| `/mindmap` | 思维导图 | 是 |
| `/user` | 个人中心（账号绑定、BYOK 配置） | 是 |
| `/manual` | 使用手册 | 否 |
| `/oauth-callback` | OAuth 回调页（静默跳转） | 否 |

---

## 🛡️ 安全设计要点

```
┌────────────────────────────────────────────────────────────┐
│                      安全分层防护                            │
├────────────────────────────────────────────────────────────┤
│  ① 网络层 — Nginx HTTPS + HSTS + 同源代理 / CORS 收紧      │
│  ② 认证层 — JWT 2h 短有效期 + Token Gen 代数 + 登出黑名单   │
│  ③ 速率层 — Redis 滑动窗口限流：注册/登录/AI 分级控制       │
│  ④ 输入层 — 用户名正则 + 密码强度 + HTML DOMPurify 过滤    │
│  ⑤ 输出层 — SSRF 防护（协议/IP/端口三重校验 + DNS 解析）   │
│  ⑥ 存储层 — bcrypt 密码哈希 + BYOK Fernet 对称加密          │
│  ⑦ 文件层 — 图片魔数校验 + 扩展名白名单 + 随机文件名         │
│  ⑧ 监控层 — 结构化日志 + 异常告警 + 数据库/Redis 健康检查   │
└────────────────────────────────────────────────────────────┘
```

---

## ❓ 常见问题

**Q1：AI 报错 Connection error / 无法对话？**
- 确认 LM Studio Local Server 已启动，且 `LM_STUDIO_URL` 端口正确
- 若有 API Token，在 `backend/.env` 设置 `OPENAI_API_KEY`，或在个人中心填写
- 自测：`curl http://127.0.0.1:1234/v1/models -H "Authorization: Bearer <token>"`

**Q2：AI 响应很慢或超时？**
- 换更小的模型；或增大 `LLM_HTTP_READ_TIMEOUT_SECONDS`

**Q3：Redis 连接失败？**
- Redis 为可选组件，不启动时核心功能仍可用，缓存自动降级

**Q4：BYOK 基址怎么填？**
- `base_url` 应止于 `/v1`（例如 `https://api.openai.com/v1`），不要填到 `/v1/models`

**Q5：前端接口 404 / 跨域？**
- 检查 `VITE_API_BASE_URL` 与 Vite 代理配置是否与后端端口一致

---

## 📦 开发命令速查

```bash
# 后端
cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000
cd backend && pytest -q

# 前端
cd frontend && npm run dev
cd frontend && npm run build
cd frontend && npm run test

# 生产
docker compose up -d --build
docker compose logs -f backend        # 查看后端日志
docker compose logs -f frontend       # 查看前端日志
docker compose restart                # 重启所有服务
docker compose down                   # 停止并移除容器（保留数据）
```

---

## 📚 更多文档

| 文档 | 内容 |
|------|------|
| [`backend/README.md`](backend/README.md) | 后端 API 与环境变量 |
| [`backend/PROMPT_DESIGN_GUIDE.md`](backend/PROMPT_DESIGN_GUIDE.md) | 提示词设计说明 |
| [`docs/architecture.md`](docs/architecture.md) | 系统架构图 |
| [`docs/er-diagram.md`](docs/er-diagram.md) | 数据库 ER 图 |
| 应用内 `/manual` | 终端用户操作手册 |

---

## 🤝 贡献

欢迎提交 Issue / Pull Request！

---

## 📄 License

**MIT License**

---

<div align="center">

**🌟 如果你觉得这个项目还不错，点个 Star 支持一下～**

<br>

**v1.1.0** · 最后更新：2026-06-28

</div>
