# AI个人智能笔记助手 - 后端

基于 FastAPI + MySQL + **LM Studio**（OpenAI 兼容本地 API）的智能笔记助手后端服务。

## 技术栈

- **框架**: FastAPI
- **数据库**: MySQL + SQLAlchemy
- **AI 推理**: LM Studio 本地服务（`openai` SDK，`base_url` 指向 `LM_STUDIO_URL`）
- **认证**: JWT
- **异步服务器**: Uvicorn

## 项目结构

```
backend/
├── app/
│   ├── api/v1/          # API路由
│   ├── core/            # 核心配置
│   ├── crud/            # 数据库操作
│   ├── models/          # 数据模型
│   ├── services/        # 业务逻辑
│   └── utils/           # 工具函数
├── requirements.txt     # 依赖包
└── main.py             # 入口文件
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`，并修改配置：

```bash
cp .env.example .env
```

编辑 `.env`：填写 MySQL、JWT，以及 **LM Studio** 的 `LM_STUDIO_URL`（通常为 `http://127.0.0.1:1234/v1`）与 `LM_STUDIO_MODEL`（与 LM Studio 服务器页显示的模型 ID 一致）。若启用「用户自带 API Key（BYOK）」保存功能：可不配 `ENCRYPTION_KEY`，服务端会用现有 `SECRET_KEY` 派生加密密钥（换 `SECRET_KEY` 后用户需重新保存自带密钥）；也可单独配置 `ENCRYPTION_KEY`（见 `.env.example`）。

### 3. 启动 LM Studio 本地 API

1. 打开 [LM Studio](https://lmstudio.ai/)，下载并加载模型。
2. 在 **Local Server** 中启动服务，确认浏览器或文档中给出的 **Base URL**（须带 `/v1` 后缀以匹配本项目的 OpenAI 兼容客户端）。
3. 保持 LM Studio 运行后再启动本后端。

### 4. 创建数据库

在 MySQL 中创建数据库：

```sql
CREATE DATABASE note_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

（名称须与 `.env` 中 `DB_NAME` 一致，模板默认为 `note_db`。）

### 5. 启动服务

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API文档

启动服务后访问（假设使用默认配置）：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

> 注意：如果修改了API端口，请相应调整URL中的端口号

## API接口

### 用户管理
- `POST /api/v1/user/register` - 用户注册
- `POST /api/v1/user/login` - 用户登录
- `GET /api/v1/user/me` - 获取当前用户信息
- `GET /api/v1/user/me/llm-settings` - 获取当前用户 LLM / BYOK 设置（密钥仅返回后四位掩码）
- `PUT /api/v1/user/me/llm-settings` - 更新 LLM 基址、模型、可选自带 API Key（服务端 Fernet 加密存储；未配 `ENCRYPTION_KEY` 时用 `SECRET_KEY` 派生）

### 笔记管理
- `POST /api/v1/note/` - 创建笔记
- `GET /api/v1/note/` - 获取笔记列表
- `GET /api/v1/note/{note_id}` - 获取笔记详情
- `PUT /api/v1/note/{note_id}` - 更新笔记
- `DELETE /api/v1/note/{note_id}` - 删除笔记

### AI功能
- `POST /api/v1/ai/generate-note` - AI生成笔记
- `POST /api/v1/ai/summarize-note` - AI总结笔记
- `POST /api/v1/ai/translate-note` - 翻译笔记（请求体 `content`、`targetLang`，返回 `content`、`truncated`）

## 开发说明

- 默认端口: 8000
- 数据库: MySQL (localhost:3306)
- AI：通过 `.env` 中的 `LM_STUDIO_URL`、`LM_STUDIO_MODEL`（及可选 `OPENAI_API_KEY`）连接 LM Studio 或其它 OpenAI 兼容端点；用户可在个人中心配置自带密钥与端点，覆盖未配置项时仍回退到上述服务端默认值。

## License

MIT
