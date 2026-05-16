# 系统架构图

```mermaid
graph TB
    subgraph 前端层
        Vue3[Vue 3 + Element Plus]
        Router[Vue Router]
        Pinia[Pinia 状态管理]
        Axios[Axios HTTP 客户端]
    end

    subgraph 网关层
        Nginx[Nginx 反向代理<br/>/api -> 后端 /uploads -> 后端]
    end

    subgraph 后端层
        FastAPI[FastAPI 框架]
        RouterAPI[API 路由层]
        Service[业务逻辑层<br/>AI生成/总结/翻译/对话]
        CRUD[数据访问层]
        Auth[JWT 认证中间件]
    end

    subgraph AI层
        LMStudio[LM Studio 本地推理端<br/>或 OpenAI 兼容 API]
        BYOK[用户自带密钥 BYOK]
    end

    subgraph 数据层
        MySQL[(MySQL 数据库)]
        Redis[(Redis 缓存)]
        Uploads[本地文件存储<br/>头像/图片]
    end

    %% 前端调用关系
    Axios --> Nginx
    Nginx --> FastAPI
    Vue3 --> Router
    Vue3 --> Pinia

    %% 后端调用关系
    FastAPI --> RouterAPI
    RouterAPI --> Auth
    RouterAPI --> Service
    RouterAPI --> CRUD
    Service --> LMStudio
    Service --> BYOK
    CRUD --> MySQL
    CRUD --> Redis
    RouterAPI --> Uploads

    %% 数据流标注
    classDef layer fill:#f0f4ff,stroke:#409eff,stroke-width:2px
    classDef data fill:#f0fff0,stroke:#67c23a,stroke-width:2px
    classDef ai fill:#fff7e6,stroke:#e6a23c,stroke-width:2px

    class Vue3,Router,Pinia,Axios,Nginx layer
    class FastAPI,RouterAPI,Service,CRUD,Auth layer
    class MySQL,Redis,Uploads data
    class LMStudio,BYOK ai
```
