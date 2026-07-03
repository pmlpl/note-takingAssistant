# 更新日志（Changelog）

所有重要变更均记录于此。采用 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 规范。

格式：`YYYY-MM-DD`

---

## [1.1.0] - 2026-07-03

> **桌面端功能完善 + 安全加固**

### 🎉 新增

- **AI 助手独立页面**：桌面端左侧导航栏新增 AI 助手入口，支持多轮对话、快捷操作、笔记选择器
- **本地模型直连**：桌面端支持直连 LM Studio / vLLM 等 OpenAI 兼容本地模型，数据不经过后端转发
- **富文本预览/编辑双模式**：点击笔记默认进入预览模式，点击编辑按钮才进入编辑模式
- **关闭窗口行为设置**：支持直接退出（默认）、最小化到托盘、询问我三种行为，在个人中心配置
- **系统托盘图标**：右键托盘菜单支持显示主窗口、退出
- **每日笔记统计图表**：首页新增每日新建笔记柱状图
- **知识图谱图标区分**：导航栏知识图谱与思维导图图标明确区分

### 🔒 改进

- **生产环境禁用开发者工具**：移除菜单栏入口、禁用 F12/Ctrl+Shift+I 快捷键、自定义右键菜单移除「检查」
- **本地模型 URL 安全校验**：仅允许私有 IP + 白名单端口，禁止 file:// 等危险协议
- **桌面端 API 默认指向生产环境**：用户不可修改服务器设置
- **单实例锁 + sandbox**：增强桌面端安全性
- **自动更新支持**：集成 electron-updater，优雅降级处理

### 🐛 修复

- **编辑/预览模式混淆** → Vue Router hash 模式下 `window.location.search` 取不到查询参数，改用 `route.query`
- **云端模型不可用** → 流式接口路径与后端不一致（`/chat/stream` → `/chat-stream`），且原生 fetch 未携带认证 token
- **本地模型开关切换不生效** → 关闭开关时未同步更新 `local_llm_settings.enabled`，改为切换立即保存
- **AI 思考动画不显示** → 发送用户消息后预先推送空 assistant 占位消息
- **托盘图标打包后不显示** → `package.json` 的 `build.files` 未包含 `build` 目录，增强 `getIconPath()` 多路径搜索
- **关闭窗口后进程残留** → 添加关闭行为设置，根据用户选择决定退出或最小化

### 📄 文档

- `README.md` → 更新桌面版功能说明，日期更新至 2026-07-03
- `desktop/README.md` → 更新开发者工具说明、与 Web 端差异表格
- `CHANGELOG.md` → 新增桌面端 v1.1.0 变更记录

---

## [1.1.0] - 2026-06-28

> **多种登录方式 + 账号绑定 + 知识图谱**

### 🎉 新增

- **知识图谱**：笔记与概念关联可视化，力导向布局，节点拖拽交互，点击查看详情
- **GitHub OAuth 登录**：一键授权登录/注册，首次登录自动创建账号
- **邮箱验证码登录**：输入邮箱+验证码即可登录，未注册自动创建账号
- **账号绑定管理**：个人中心支持昵称修改、邮箱换绑、GitHub 绑定/解绑
- **OAuth 账号系统**：新增 `oauth_accounts` 表，支持多平台账号关联
- **邮箱验证码发送**：基于 QQ 邮箱 SMTP，Redis 存储验证码，5 分钟有效
- **OAuth 回调页**：`/oauth-callback` 路由，postMessage 与父窗口通信

### 🔒 改进

- **注册/登录以邮箱为主**：username 改为 nickname，email 作为唯一登录标识
- **用户模型扩展**：新增 `nickname`、`email_verified` 字段
- **绑定模式自动补全**：旧账号重新登录/绑定时自动补全 GitHub 用户名和头像
- **启动迁移脚本**：`startup_migrations.py` 新增 oauth_accounts 表及字段自动迁移
- **JWT 认证优化**：邮箱作为 sub，token_gen 代数用于改密后全量失效

### 🐛 修复

- GitHub OAuth URL 编码问题 → 使用 `urllib.parse.urlencode(safe=":/")`
- 授权后页面不跳转 → state 参数区分登录/绑定模式，绑定成功 postMessage 通知
- 绑定信息不显示用户名 → 新增 provider_username 字段并展示
- 同步 Redis 调用阻塞事件循环 → 使用线程池执行

### 📄 文档

- `README.md` → v1.1.0（新增知识图谱、多种登录方式、账号绑定、OAuth 接口）
- `frontend/src/views/help/UserManual.vue` → v1.1.0（全面更新登录方式、账号绑定、知识图谱说明）
- 功能总览表格新增知识图谱、多种登录方式、账号管理模块

---

## [1.1.0] - 2026-06-20

> **安全加固 + 生产部署 + 前端校验同步**

### 🎉 新增

- **HTTPS 生产部署**：Nginx 支持 TLS 1.2/1.3、HSTS、安全响应头（X-Frame-Options、X-Content-Type-Options、Referrer-Policy）
- **Let's Encrypt 自动 HTTPS**：Certbot 容器化，申请一次后自动续期（每 12 小时检查）
- **Redis 密码支持**：Redis 配置 `REDIS_PASSWORD`，连接更安全
- **前端注册密码校验**：表单规则同步更新为"至少 8 位，须同时含字母和数字"
- **前端注册邮箱重复检测**：注册接口同时检查用户名和邮箱唯一性
- **前端表单验证集成**：注册页使用 Element Plus `formRef.validate()`，不绕过任何校验
- **前端用户名校验**：3-32 字符，字母数字开头，仅含字母/数字/下划线/短横线
- **前端密码二次确认**：注册页新增"确认密码"字段，实时校验一致性
- **UserCenter 密码强度提示**：修正强度计算（8 位/12 位分档），新增"须含字母和数字"校验

### 🔒 改进

- **JWT 令牌代数（token_gen）**：`users.token_gen` 列使用 `server_default='0'`，改密后自增 1，令牌立即失效
- **启动迁移脚本**：`startup_migrations.py` 新增 `token_gen` 列检测，老数据库自动补列
- **数据库模型**：UserDB 修正 `server_default`，确保数据库侧有默认值
- **print → 结构化日志**：`main.py` 全部 `print()` 替换为 `logger.warning()`，便于生产排障
- **Uvicorn 多 Worker**：Dockerfile 生产模式启动 `workers = min(CPU×2, 8)`，提升并发
- **CORS 收紧**：`FRONTEND_URL` 改为 `https://momo.makeup` 固定域名

### 🐛 修复

- 前端注册页密码提示"至少 6 位"与后端实际要求"8 位"不一致 → 已同步
- UserCenter 修改密码"至少 6 位"提示错误 → 已更新为 8 位
- 注册流程缺少邮箱唯一性检查 → 后端 `crud/user.py` 新增 `get_user_by_email`，注册时双重校验

### 📄 文档

- `README.md` → v1.1.0（新增安全分层图、部署架构、Docker Compose 步骤）
- `DEPLOY.md` → v1.1.0（新增前端构建步骤、`docker compose` V2 命令、HTTPS 证书申请）
- `backend/README.md` → v1.1.0（新增 Redis 密码、`ACCESS_TOKEN_EXPIRE_MINUTES` 修正为 120 分钟）
- `docs/architecture.md` → v1.1.0（新增生产架构 Mermaid 图、端口映射表、数据安全要点）
- `docs/er-diagram.md` → v1.1.0（新增 `token_gen` 列、索引说明）
- `frontend/src/views/help/UserManual.vue` → 密码说明"6 位"改为"8 位，须含字母和数字"

---

## [1.0.0] - 2026-06-02

> **首个正式版本**

### 🎉 新增

- 用户注册、登录、退出（含 JWT 黑名单）
- 笔记管理（创建/编辑/搜索/收藏/富文本 + Markdown）
- AI 笔记生成、总结、翻译（流式输出）
- AI 多轮对话（首页助手面板）
- 思维导图（Mermaid 可视化）
- 欢迎页（产品介绍、注册趋势统计 ECharts）
- 个人中心（头像、密码、LLM / BYOK 配置）
- Docker Compose 一键部署（MySQL + Redis + 后端 + Nginx 前端）
- GitHub Actions CI（前端 vitest + 构建、后端 pytest）
