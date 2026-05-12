# AI个人智能笔记助手 - 后端

基于 FastAPI + MySQL + Ollama 的智能笔记助手后端服务。

## 技术栈

- **框架**: FastAPI
- **数据库**: MySQL + SQLAlchemy
- **AI模型**: Ollama (本地部署)
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

编辑 `.env` 文件，设置数据库密码等信息。

### 3. 安装并启动 Ollama

```bash
# 安装 Ollama (https://ollama.ai)
# 拉取模型
ollama pull qwen:7b

# 启动 Ollama
ollama serve
```

### 4. 创建数据库

在 MySQL 中创建数据库：

```sql
CREATE DATABASE ai_note_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

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

### 笔记管理
- `POST /api/v1/note/` - 创建笔记
- `GET /api/v1/note/` - 获取笔记列表
- `GET /api/v1/note/{note_id}` - 获取笔记详情
- `PUT /api/v1/note/{note_id}` - 更新笔记
- `DELETE /api/v1/note/{note_id}` - 删除笔记

### AI功能
- `POST /api/v1/ai/generate-note` - AI生成笔记
- `POST /api/v1/ai/summarize-note` - AI总结笔记

## 开发说明

- 默认端口: 8000
- 数据库: MySQL (localhost:3306)
- AI模型: qwen:7b (可通过 Ollama 更换)

## License

MIT