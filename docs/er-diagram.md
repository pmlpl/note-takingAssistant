# 数据库 ER 图（v1.1.0）

```mermaid
erDiagram
    users {
        int id PK "主键，自增"
        varchar username "用户名（唯一索引）"
        varchar email "邮箱（唯一索引，可为空）"
        varchar hashed_password "bcrypt 密码哈希"
        text avatar_url "头像 URL（可为空）"
        text llm_base_url "BYOK API 基址（可为空）"
        varchar llm_model "BYOK 模型名（可为空）"
        text llm_api_key_encrypted "BYOK 密钥（Fernet 加密）"
        int token_gen "令牌代数，改密后 +1"
        datetime created_at "注册时间"
    }

    notes {
        int id PK "主键，自增"
        int user_id FK "用户 ID（关联 users.id）"
        varchar title "笔记标题"
        text content "正文（HTML 富文本或 Markdown）"
        varchar tags "标签，逗号分隔（可为空）"
        int is_favorite "是否收藏：0=否，1=是"
        datetime created_at "创建时间"
        datetime updated_at "更新时间"
    }

    ai_usage_logs {
        int id PK "主键，自增"
        int user_id FK "用户 ID（关联 users.id）"
        varchar usage_type "使用类型：generate / summarize / translate / chat"
        datetime created_at "调用时间"
    }

    users ||--o{ notes : "拥有"
    users ||--o{ ai_usage_logs : "产生"
```

## 表说明

| 表名 | 说明 |
|------|------|
| `users` | 用户账户信息，含 BYOK 配置 |
| `notes` | 笔记正文，按用户隔离 |
| `ai_usage_logs` | AI 功能调用记录（用于统计分析） |

## 索引

| 表 | 索引字段 | 类型 |
|----|----------|------|
| `users` | `username` | UNIQUE |
| `users` | `email` | UNIQUE |
| `users` | `id` | PRIMARY |
| `notes` | `user_id` | 普通索引 |
| `notes` | `title` | 普通索引（全文搜索可扩展） |
| `ai_usage_logs` | `user_id` | 普通索引 |
