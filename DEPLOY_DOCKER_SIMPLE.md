# NoteMind Docker 一键部署指南（简化版）

> 面向本地/单机部署场景：安装 Docker Desktop 后，一条命令启动完整服务，浏览器直接访问。
> 生产服务器 + HTTPS 部署请参考 `DEPLOY.md`。

---

## 一、前置条件

| 软件 | 版本要求 | 说明 |
|------|---------|------|
| Docker Desktop | 最新版 | Windows / macOS / Linux 均可 |
| Docker Compose | V2 及以上 | Docker Desktop 自带 |
| 内存 | ≥ 4GB 可用 | MySQL + Redis + Backend + Frontend |
| 磁盘 | ≥ 5GB 空闲 | 镜像 + 数据卷 |

**检查 Docker：**
```bash
docker --version
docker compose version
```

---

## 二、快速开始（3 步）

### 第 1 步：启动 Docker Desktop

确保 Docker Desktop 已启动且运行正常（系统托盘鲸鱼图标稳定）。

### 第 2 步：一键部署

**Windows 用户（推荐）：** 双击 `deploy.bat`

**或命令行执行：**
```bash
# 进入项目根目录
cd note-takingAssistant

# 复制环境配置（首次）
copy .env.simple .env

# 构建并启动
docker compose -f docker-compose.simple.yml --env-file .env up -d --build
```

### 第 3 步：访问网页

打开浏览器访问：**http://localhost:8090**

> 首次启动需要等待 15-30 秒（数据库初始化 + 后端建表），页面报错请刷新。

---

## 三、架构说明

```
┌─────────────────────────────────────────────┐
│           浏览器 (localhost:8090)            │
└──────────────────┬──────────────────────────┘
                   │ 唯一对外端口
┌──────────────────▼──────────────────────────┐
│  frontend 容器 (Nginx :80)                   │
│  ├─ 静态资源 /  → /var/www/note-app         │
│  ├─ /api/     → proxy_pass backend:8000    │
│  └─ /uploads/ → proxy_pass backend:8000    │
└──────────────────┬──────────────────────────┘
                   │ Docker 内部网络
┌──────────────────▼──────────────────────────┐
│  backend 容器 (FastAPI :8000)                │
│  ├─ 启动时自动 Base.metadata.create_all 建表 │
│  ├─ MySQL 连接 → mysql:3306                  │
│  └─ Redis 连接 → redis:6379                  │
└──────┬───────────────────┬───────────────────┘
       │                   │
┌──────▼──────┐    ┌───────▼──────┐
│ mysql :3306 │    │ redis :6379  │
│ 数据卷持久化  │    │ 数据卷持久化   │
└─────────────┘    └──────────────┘
```

**端口规划：**
- 宿主机：仅 `8090`（可通过 `.env` 中 `EXTERNAL_PORT` 修改）
- Docker 内部：backend `8000`、mysql `3306`、redis `6379`（不对外暴露）

---

## 四、配置说明

### 环境变量（.env）

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `EXTERNAL_PORT` | `8090` | 浏览器访问端口 |
| `DB_PASSWORD` | 自动生成 | MySQL root 密码 |
| `DB_NAME` | `note_db` | 数据库名 |
| `REDIS_PASSWORD` | 自动生成 | Redis 密码 |
| `SECRET_KEY` | 自动生成 | JWT 签名密钥 |

> 修改端口后需重新执行 `docker compose up -d` 生效。
> 生产环境建议修改三个密钥为随机长字符串。

### 数据持久化

所有数据通过 Docker named volume 持久化，删除容器不会丢失数据：

| Volume | 用途 |
|--------|------|
| `mysql_data` | MySQL 数据库文件 |
| `redis_data` | Redis 持久化数据 |
| `backend_uploads` | 用户上传的图片/文件 |

---

## 五、常用命令

```bash
# 启动 / 构建
docker compose -f docker-compose.simple.yml --env-file .env up -d --build

# 查看运行状态
docker compose -f docker-compose.simple.yml ps

# 查看实时日志
docker compose -f docker-compose.simple.yml logs -f

# 查看某个服务日志
docker compose -f docker-compose.simple.yml logs -f backend

# 重启服务
docker compose -f docker-compose.simple.yml restart

# 停止服务（保留数据）
docker compose -f docker-compose.simple.yml down

# 停止并删除所有数据（谨慎！）
docker compose -f docker-compose.simple.yml down -v
```

---

## 六、AI 功能配置

AI 功能（智能问答、知识图谱、笔记摘要等）需要用户在网页内配置 API Key：

1. 登录后进入 **个人中心 → AI 设置**
2. 填写 OpenAI 兼容 API 的 Base URL、模型名称、API Key
3. 保存后即可使用 AI 功能

> 服务器不需要本地运行大模型，所有 AI 请求转发到用户配置的 API 端点。

---

## 七、常见问题

### Q: 首次打开页面白屏或 502？
A: 后端正在初始化数据库表，等待 30 秒后刷新页面。可通过 `docker compose logs -f backend` 查看启动进度。

### Q: 端口 8090 被占用？
A: 修改 `.env` 中的 `EXTERNAL_PORT` 为其他端口（如 8081），然后 `docker compose up -d` 重启。

### Q: 如何更新代码后重新部署？
A: 拉取最新代码后，重新执行 `docker compose -f docker-compose.simple.yml --env-file .env up -d --build`，Docker 会自动重建变更的镜像。

### Q: 数据会丢失吗？
A: 不会。MySQL、Redis、上传文件都使用 named volume 持久化，`docker compose down` 不会删除数据。只有执行 `down -v` 才会清除数据。

### Q: 后端启动报数据库连接错误？
A: MySQL 首次初始化需要较长时间。compose 配置了 healthcheck，backend 会等待 mysql 健康后才启动。如果持续报错，执行 `docker compose restart backend`。

---

## 八、文件清单

| 文件 | 说明 |
|------|------|
| `docker-compose.simple.yml` | 简化版 Compose 配置（4 服务，单端口） |
| `.env.simple` | 环境变量模板 |
| `deploy.bat` | Windows 一键部署脚本 |
| `deploy.ps1` | PowerShell 一键部署脚本 |
| `frontend/Dockerfile.simple` | 前端多阶段构建 Dockerfile |
| `frontend/nginx.simple.conf` | 简化版 Nginx 配置 |
| `backend/Dockerfile.simple` | 后端 Dockerfile（Python 3.12） |

> 原始生产配置（`docker-compose.yml`、`DEPLOY.md`、HTTPS/certbot）保持不变，面向服务器部署场景。
