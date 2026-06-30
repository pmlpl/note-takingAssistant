# NoteMind - 后端（v1.1.0）

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
├── app/
│   ├── api/v1/                # user, note, ai, public 路由
│   ├── core/                  # config, database, security, redis, logger, rate_limit
│   ├── crud/                  # 数据访问层
│   ├── models/                # Pydantic 请求/响应 + SQLAlchemy ORM
│   ├── services/               # AI 生成/总结/翻译/对话
│   └── utils/                  # 文件上传、LLM 错误、URL 安全
├── main.py                     # FastAPI 入口
├── requirements.txt
├── .env.example
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

编辑 `.env`，填写以下**必填项**：

| 配置项 | 说明 | 示例值 |
|--------|------|--------|
| `API_HOST` | 服务器绑定地址 | `0.0.0.0` |
| `API_PORT` | 服务端口 | `8000` |
| `API_BASE_URL` | 外部访问地址 | `https://momo.makeup` |
| `FRONTEND_URL` | 前端地址（CORS） | `https://momo.makeup` |
| `DEBUG` | 生产环境 | `false` |
| `DB_HOST` / `DB_PORT` / `DB_USER` / `DB_PASSWORD` / `DB_NAME` | MySQL 数据库 | - |
| `REDIS_HOST` / `REDIS_PORT` / `REDIS_DB` / `REDIS_PASSWORD` | Redis 配置（带密码） | - |
| `SECRET_KEY` | JWT 密钥（≥ 32 字符） | `your-secret-key-...` |
| `ALGORITHM` | JWT 算法 | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token 过期时间（分钟） | `120` |
| `LM_STUDIO_URL` | LM Studio API 地址 | `http://127.0.0.1:1234/v1` |
| `LM_STUDIO_MODEL` | 使用的模型 ID | `qwen3.5-9b-q4_k_m_gguf` |
| `LLM_HTTP_READ_TIMEOUT_SECONDS` | LLM 请求超时（秒） | `1200.0` |
| `LLM_HTTP_TRUST_ENV` | 是否读取系统代理 | `false` |

**可选配置：**
- `ENCRYPTION_KEY` - BYOK 加密密钥（留空则从 `SECRET_KEY` 派生）
- `OPENAI_API_KEY` - 服务端默认 API Key

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

### 用户管理

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/user/register` | 用户注册 |
| `POST` | `/api/v1/user/login` | 用户登录 |
| `POST` | `/api/v1/user/logout` | 退出登录（JWT 黑名单） |
| `GET` | `/api/v1/user/me` | 获取当前用户信息 |
| `PUT` | `/api/v1/user/password` | 修改密码 |
| `GET` | `/api/v1/user/me/llm-settings` | 获取 LLM / BYOK 设置（密钥返回后四位掩码） |
| `PUT` | `/api/v1/user/me/llm-settings` | 更新 LLM 基址、模型、可选自带 API Key |
| `POST` | `/api/v1/user/avatar` | 上传/更换头像 |

### 笔记管理

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/note/` | 创建笔记 |
| `GET` | `/api/v1/note/` | 获取笔记列表（支持搜索/筛选/分页） |
| `GET` | `/api/v1/note/{note_id}` | 获取笔记详情 |
| `PUT` | `/api/v1/note/{note_id}` | 更新笔记 |
| `DELETE` | `/api/v1/note/{note_id}` | 删除笔记 |
| `POST` | `/api/v1/note/{note_id}/favorite` | 收藏/取消收藏笔记 |

### AI 功能

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/ai/generate-note` | AI 生成笔记 |
| `POST` | `/api/v1/ai/summarize-note` | AI 总结笔记 |
| `POST` | `/api/v1/ai/translate-note-stream` | 流式翻译笔记 |
| `POST` | `/api/v1/ai/chat-stream` | 流式 AI 对话 |

### 公开接口（无需登录）

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/public/stats` | 平台统计数据 |
| `GET` | `/api/v1/public/daily-registrations` | 近 30 日每日注册量 |

---

## 安全机制

| 机制 | 说明 |
|------|------|
| **JWT 加固** | 2 小时短有效期 + Token Gen 代数 + Redis 黑名单登出 |
| **速率限制** | Redis 滑动窗口：注册 5/分钟、登录 5/分钟、AI 生成 3/分钟 |
| **密码安全** | bcrypt 哈希 + 至少 8 位含字母数字 |
| **SSRF 防护** | LLM 自定义 URL 协议/IP/端口三重校验 + DNS 解析验证 |
| **BYOK 加密** | Fernet 对称加密存库 |
| **文件上传** | 魔数校验 + 扩展名白名单 + 随机文件名 |

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
