# 系统架构图

## 开发架构（本地联调）

```mermaid
graph TB
    subgraph 前端层
        Vue3[Vue 3 + Element Plus]
        Router[Vue Router 4]
        Pinia[Pinia 状态管理]
        Axios[Axios HTTP 客户端]
    end

    subgraph 后端层
        FastAPI[FastAPI 框架]
        RouterAPI[API 路由层]
        Service[业务逻辑层<br/>AI生成/总结/翻译/对话]
        CRUD[数据访问层]
        Auth[JWT 认证中间件]
        RateLimit[Redis 速率限制]
        Logger[结构化日志]
    end

    subgraph AI层
        LMStudio[LM Studio 本地推理端<br/>或 OpenAI 兼容 API]
        BYOK[用户自带密钥 BYOK]
        SSRF[SSRF 防护]
    end

    subgraph 数据层
        MySQL[(MySQL 8.0<br/>异步 ORM)]
        Redis[(Redis 7<br/>缓存/限流/黑名单)]
        Uploads[本地文件存储<br/>头像/图片]
    end

    Axios -->|HTTP| FastAPI
    Vue3 --> Router
    Vue3 --> Pinia

    FastAPI --> RouterAPI
    RouterAPI --> Auth
    RouterAPI --> RateLimit
    RouterAPI --> Service
    RouterAPI --> CRUD
    RouterAPI --> Logger
    Service --> LMStudio
    Service --> SSRF
    Service --> BYOK
    CRUD --> MySQL
    CRUD --> Redis
    RouterAPI --> Uploads

    classDef layer fill:#f0f4ff,stroke:#409eff,stroke-width:2px
    classDef data fill:#f0fff0,stroke:#67c23a,stroke-width:2px
    classDef ai fill:#fff7e6,stroke:#e6a23c,stroke-width:2px

    class Vue3,Router,Pinia,Axios layer
    class FastAPI,RouterAPI,Service,CRUD,Auth,RateLimit,Logger layer
    class MySQL,Redis,Uploads data
    class LMStudio,BYOK,SSRF ai
```

本地开发时，Vite 将 `/api` 代理到 FastAPI（默认端口 5174 → 8000）。

---

## 生产架构（Docker Compose + Nginx + HTTPS）

```mermaid
graph TB
    subgraph 用户层
        Browser[浏览器<br/>HTTPS 443]
    end

    subgraph 基础设施层
        Nginx[Nginx<br/>HTTPS + TLS 1.2/1.3<br/>HSTS + gzip + 安全头]
        Certbot[Certbot<br/>Let's Encrypt<br/>自动续期]
    end

    subgraph 容器层["Docker Compose (5 服务)"]
        Frontend[Nginx Frontend<br/>静态资源托管<br/>反向代理 API]
        Backend[FastAPI Backend<br/>多 Worker Uvicorn<br/>异步 MySQL/Redis]
        MySQL[(MySQL 8.0<br/>数据持久化)]
        Redis[(Redis 7<br/>缓存/限流/黑名单<br/>带密码)]
        CertbotVol[Certbot<br/>证书存储]
    end

    subgraph 外部服务
        AIModel[LLM API<br/>LM Studio / OpenAI<br/>BYOK 可选]
    end

    Browser -->|HTTPS 443| Nginx
    Nginx -->|HTTP 内部| Frontend
    Frontend -->|proxy_pass| Backend
    Backend -->|SQL| MySQL
    Backend -->|Redis| Redis
    Backend -->|OpenAI 协议| AIModel
    Certbot --> CertbotVol
    Nginx -->|读取证书| CertbotVol

    classDef infra fill:#e8f4fd,stroke:#1e90ff,stroke-width:2px
    classDef container fill:#f9f0ff,stroke:#8b5cf6,stroke-width:2px
    classDef external fill:#fff0f0,stroke:#ff6b6b,stroke-width:2px

    class Nginx,Certbot infra
    class Frontend,Backend,MySQL,Redis,CertbotVol container
    class AIModel external
```

### 端口映射

| 容器 | 内部端口 | 外部暴露 | 说明 |
|------|----------|----------|------|
| `frontend` (Nginx) | 80, 443 | 80, 443 | 静态资源 + API 反向代理 |
| `backend` (FastAPI) | 8000 | 不对外 | 仅供 Nginx 容器内访问 |
| `mysql` | 3306 | ❌ 不暴露 | 容器内部网络 |
| `redis` | 6379 | ❌ 不暴露 | 容器内部网络，带密码 |
| `certbot` | - | ❌ 不暴露 | 按需运行申请证书 |

### 数据安全要点

| 层 | 措施 |
|----|------|
| **网络隔离** | MySQL/Redis 仅通过 Docker 内部网络通信，不暴露到宿主机 |
| **传输加密** | Nginx 终止 TLS，内外通信走 Docker 网络 |
| **密钥隔离** | DB_PASSWORD / REDIS_PASSWORD / SECRET_KEY 通过 `.env` 注入，不硬编码 |
| **令牌安全** | JWT 2h 有效期 + Token Gen 代数 + Redis 黑名单 |
| **BYOK 加密** | 用户 API Key 使用 Fernet 加密存储 |
