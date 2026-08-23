# NoteMind - 后端（v1.2.0）

基于 FastAPI + MySQL + Redis + **LM Studio**（OpenAI 兼容本地 API）的NoteMind 后端服务。

## 技术栈

| 类别 | 技术 |
|------|------|
| 框架 | **FastAPI** + Pydantic v2 + Uvicorn |
| 数据库 | **MySQL 8.0** + SQLAlchemy 2.x（异步） |
| 缓存 | **Redis 7**（异步 + JWT 黑名单 + 限流） |
| AI 推理 | **openai** (AsyncOpenAI) + httpx，兼容 LM Studio / OpenAI API |
| 认证 | **python-jose** (JWT) + **bcrypt**（密码哈希） |
| 加密 | **cryptography** (Fernet)，BYOK 密钥加密存储 |
| 测试 | **pytest** |

## 项目结构

```
backend/
├── alembic/                    # Alembic 迁移（versions/0001_initial.py）
├── app/
│   ├── api/v1/                # user, note, ai, public, kg, oauth 路由
│   ├── core/                  # config, database, security, redis, logger, rate_limit, field_crypto, startup_migrations
│   ├── crud/                  # 数据访问层（user / note / ai_usage / ai_conversation）
│   ├── models/                # Pydantic 请求/响应 + SQLAlchemy ORM
│   ├── services/              # AI 服务：agent/（主 Agent 多工具）、生成/总结/翻译/对话、OAuth、邮件
│   └── utils/                  # 文件上传、LLM 错误、URL 安全、统计序列
├── main.py                     # FastAPI 入口
├── requirements.txt
├── .env.example
├── create_test_user.py         # 测试用户创建脚本
├── scripts/                    # 辅助脚本（inspect_db、test_chat_api）
└── tests/                     # pytest 单元测试
```

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，填写以下**必填项**（与 `app/core/config.py`、`.env.example` 对齐）：

| 配置项 | 说明 | 示例值 |
|--------|------|--------|
| `API_HOST` | 服务器绑定地址 | `127.0.0.1` |
| `API_PORT` | 服务端口 | `8000` |
| `API_BASE_URL` | 外部访问地址 | `http://localhost:8000` |
| `FRONTEND_URL` | 前端地址（CORS） | `http://localhost:5174` |
| `CORS_ORIGINS` | 额外允许的 CORS origin（逗号分隔，可选） | `app://localhost,http://localhost:5173` |
| `DEBUG` | 开发模式（开启 uvicorn reload） | `true` |
| `DB_HOST` / `DB_PORT` / `DB_USER` / `DB_PASSWORD` / `DB_NAME` | MySQL 数据库 | - |
| `REDIS_HOST` / `REDIS_PORT` / `REDIS_DB` / `REDIS_PASSWORD` | Redis 配置（带密码） | - |
| `SECRET_KEY` | JWT 密钥（≥ 32 字符） | `change-me-in-production-...` |
| `ALGORITHM` | JWT 算法 | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token 过期时间（分钟） | `120` |
| `LM_STUDIO_URL` | LM Studio API 地址 | `http://127.0.0.1:1234/v1` |
| `LM_STUDIO_MODEL` | 使用的模型 ID | `your-model-id` |
| `LLM_HTTP_READ_TIMEOUT_SECONDS` | LLM 请求超时（秒） | `1200.0` |
| `LLM_HTTP_TRUST_ENV` | 是否读取系统代理 | `false` |

**可选配置：**
- `ENCRYPTION_KEY` - BYOK 加密密钥（留空则从 `SECRET_KEY` 派生）
- `OPENAI_API_KEY` - 服务端默认 API Key
- `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` / `GITHUB_REDIRECT_URI` - GitHub OAuth 登录（回调地址形如 `http://localhost:8000/api/v1/oauth/github/callback`）
- `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` / `SMTP_FROM_NAME` - SMTP 邮箱验证码（QQ 邮箱 465 端口）
- `MAX_IMPORT_BYTES` - 笔记导入大小上限（默认 20MB）
- `IMAGE_MAX_BYTES` - 笔记配图上传大小上限（默认 5MB）
- `RATE_LIMIT_DISABLED=1` - 测试环境禁用速率限制（避免 CI 单 IP 触发限流）

### 3. 创建数据库

```sql
CREATE DATABASE note_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. 启动 LM Studio（可选）

> 若不配置 AI 功能可跳过此步，笔记管理功能仍可正常使用。

1. 打开 [LM Studio](https://lmstudio.ai/)，下载并加载模型
2. 启动 **Local Server**，基址形如 `http://127.0.0.1:1234/v1`
3. 在 `.env` 中配置 `LM_STUDIO_URL`、`LM_STUDIO_MODEL`

### 5. 启动服务

```bash
# 开发模式（单进程，自动 reload）
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 生产模式（多 worker，根据 CPU 核心数自动计算）
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## API 文档

启动服务后访问：

- **Swagger UI**（推荐）：http://localhost:8000/docs
- **Redoc**：http://localhost:8000/redoc

---

## API 接口一览

> 路由挂载见 `backend/main.py`（`include_router`），以下列表与实际代码同步（`backend/app/api/v1/`）。

### 用户管理（`user.py`）

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/user/register` | 用户注册（邮箱 + 密码 + 昵称） |
| `POST` | `/api/v1/user/login` | 邮箱密码登录 |
| `POST` | `/api/v1/user/logout` | 退出登录（JWT jti 加入 Redis 黑名单） |
| `GET` | `/api/v1/user/me` | 获取当前用户信息 |
| `PUT` | `/api/v1/user/password` | 修改密码（改密后全部旧令牌失效） |
| `GET` | `/api/v1/user/me/llm-settings` | 获取 LLM / BYOK 设置（密钥仅返回后四位掩码） |
| `PUT` | `/api/v1/user/me/llm-settings` | 更新 LLM 基址、模型、可选自带 API Key |
| `POST` | `/api/v1/user/avatar` | 上传/更换头像（魔数 + 扩展名校验） |
| `GET` | `/api/v1/user/stats` | 获取用户统计（笔记数 / AI 使用次数 / 活跃天数） |
| `PUT` | `/api/v1/user/me/nickname` | 修改昵称 |
| `GET` | `/api/v1/user/me/bindings` | 获取账号绑定状态（邮箱 / GitHub） |
| `DELETE` | `/api/v1/user/me/bindings/email` | 解除邮箱绑定（需密码，且保留其他登录方式） |
| `DELETE` | `/api/v1/user/me/bindings/github` | 解除 GitHub 绑定 |

### OAuth 与邮箱登录（`oauth.py`）

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/oauth/github/config` | 获取 GitHub 登录配置（enabled） |
| `POST` | `/api/v1/oauth/github/authorize` | 获取 GitHub 授权 URL（已登录时为绑定模式） |
| `GET` | `/api/v1/oauth/github/callback` | GitHub OAuth 回调（登录/注册/绑定） |
| `POST` | `/api/v1/oauth/email/send-code` | 发送邮箱验证码（Redis 存储，5 分钟有效） |
| `POST` | `/api/v1/oauth/email/verify` | 验证码登录/注册 |
| `POST` | `/api/v1/oauth/email/bind-code` | 发送邮箱绑定/换绑验证码（10 分钟有效） |
| `POST` | `/api/v1/oauth/email/bind` | 验证码绑定/换绑邮箱 |

### 笔记管理（`note.py`）

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/note/upload-image` | 上传笔记配图（魔数 + MD5 校验，≤5MB） |
| `GET` | `/api/v1/note/search` | 按标题模糊搜索笔记（分页） |
| `POST` | `/api/v1/note/` | 创建笔记（标题查重，冲突返回 409） |
| `GET` | `/api/v1/note/` | 获取笔记列表（分页） |
| `GET` | `/api/v1/note/recent` | 获取最近笔记（最多 20 条，Redis 缓存优先） |
| `POST` | `/api/v1/note/recent/update` | 更新最近笔记顺序 |
| `GET` | `/api/v1/note/{note_id}` | 获取笔记详情 |
| `PUT` | `/api/v1/note/{note_id}` | 更新笔记 |
| `DELETE` | `/api/v1/note/{note_id}` | 删除笔记（联动清理关联图片与缓存） |
| `POST` | `/api/v1/note/import` | 导入笔记（.txt / .md / .docx，≤20MB，可选覆盖） |

### AI 功能（`ai.py`）

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/ai/generate-note` | AI 生成笔记（服务端聚合流式结果后返回 JSON） |
| `POST` | `/api/v1/ai/generate-note-stream` | 流式生成笔记（text/plain 增量） |
| `POST` | `/api/v1/ai/summarize-note` | AI 总结笔记（总结/优缺点/建议） |
| `POST` | `/api/v1/ai/translate-note-stream` | 流式翻译笔记（HTML 先转 Markdown） |
| `POST` | `/api/v1/ai/chat` | AI 对话（非流式） |
| `POST` | `/api/v1/ai/chat-stream` | 流式 AI 对话（text/plain 增量） |
| `POST` | `/api/v1/ai/agent-chat-stream` | 主 Agent 流式对话（SSE + 工具调用，自动持久化到对话历史） |
| `GET` | `/api/v1/ai/conversations` | 获取对话列表 |
| `POST` | `/api/v1/ai/conversations` | 新建对话 |
| `GET` | `/api/v1/ai/conversations/{conversation_id}` | 获取对话详情（含全部消息） |
| `PATCH` | `/api/v1/ai/conversations/{conversation_id}` | 重命名对话标题 |
| `DELETE` | `/api/v1/ai/conversations/{conversation_id}` | 删除对话（级联删除消息） |

### 知识图谱（`kg.py`）

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/kg/graph` | 获取知识图谱数据（数据库缓存优先，否则即时构建） |
| `POST` | `/api/v1/kg/refresh` | 后台异步重新生成图谱 |
| `GET` | `/api/v1/kg/status` | 获取图谱生成状态（idle / generating / ready / failed） |

### 公开接口（无需登录，`public.py`）

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/public/welcome-stats` | 欢迎页平台统计（用户/笔记/AI 调用总量 + 近 30 日每日注册） |

> 注：旧版文档记载的 `POST /api/v1/note/{note_id}/favorite`（收藏）端点已随代码演进移除，收藏状态通过 `is_favorite` 字段在创建/更新笔记时设置。

---

## 安全机制

| 机制 | 说明 |
|------|------|
| **JWT 加固** | 2 小时短有效期 + token_gen 代数（改密全量失效）+ Redis jti 黑名单登出 |
| **速率限制** | Redis 滑动窗口（`rate_limit.py`）：注册 10/小时、登录 5/分钟、邮箱验证码 3/5 分钟、AI 60/分钟、笔记 120/分钟；Redis 不可用时降级放行 |
| **密码安全** | bcrypt 哈希 + 至少 8 位含字母数字 |
| **SSRF 防护** | LLM 自定义 URL 协议/IP/端口三重校验 + DNS 解析验证 |
| **BYOK 加密** | Fernet 对称加密存库，仅返回后四位掩码 |
| **文件上传** | 魔数 + 扩展名白名单 + MD5 校验 + 大小上限（图片 5MB / 导入 20MB） |

---

## 开发命令

```bash
# 启动（开发模式）
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 测试
pytest -q

# 带详细输出
pytest -v
```

---

## License

**MIT License**
