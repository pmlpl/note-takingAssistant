<div align="center">

<img src="docs/logo.svg" width="120" height="120" alt="NoteMind Logo">

# NoteMind

![Version](https://img.shields.io/badge/Version-1.2.0-10b981?style=for-the-badge)
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

## 项目简介

面向个人学习与创作的 **Web 全栈智能笔记应用**。

- **前端**：Vue 3 + Element Plus，流畅的交互体验
- **后端**：FastAPI + 异步 MySQL/Redis，高性能稳
- **AI 能力**：基于 OpenAI 兼容协议，支持云端大模型
- **BYOK（自带密钥）**：Web 版需用户自行配置云端 API Key；桌面版可直连本机 LM Studio
- **桌面版优势**：Windows 原生客户端，AI 完全本地运行，无需云端依赖

---

## 功能总览

| 模块 | 能力 |
|------|------|
| 📝 **笔记管理** | 创建 / 编辑 / 搜索 / 收藏 / 富文本 & Markdown |
| 🤖 **AI 辅助** | 生成笔记 / 总结 / 翻译 / 多轮对话（流式输出） |
| 🧠 **知识图谱** | 笔记与概念关联可视化 |
| 🗺️ **思维导图** | 笔记结构可视化 |
| 📊 **数据统计** | 个人笔记统计 + 平台趋势图 |
| 🔐 **安全体系** | 认证鉴权 / 密码安全 / 速率限制 / SSRF 防护 / 密钥加密 |
| 🐳 **容器化部署** | Docker Compose 一键部署，HTTPS 自动续期 |
| 🔗 **多种登录方式** | 邮箱密码 / 邮箱验证码 / GitHub OAuth |

---

## Web 版与桌面版

| 特性 | Web 版 | 桌面版 |
|------|--------|--------|
| **AI 使用方式** | 用户自带云端 API Key | 直连本机 LM Studio / 云端 API |
| **数据存储** | 服务端数据库 | 本地 SQLite |
| **网络依赖** | 必须联网 | 本地 AI 无需网络 |
| **隐私性** | 数据经服务器转发 | AI 完全本地运行 |

> 💡 **提示**：如果您希望使用本地模型进行 AI 推理，推荐使用桌面版。

---

## 技术栈

### 前端

Vue 3、Vue Router、Pinia、Element Plus、Vite、WangEditor、ECharts、Axios、Marked

### 后端

FastAPI、SQLAlchemy、MySQL、Redis、OpenAI SDK、bcrypt、pytest

### 部署

Docker、Docker Compose、Nginx、Certbot

### 工程化

GitHub Actions（CI 自动测试 + lint）、Ruff、ESLint、GitHub Container Registry（GHCR 镜像发布）

---

## 快速开始

### 本地开发

**环境要求**：Node.js ≥ 18、Python ≥ 3.10、MySQL ≥ 8.0

1. **配置后端**：进入 `backend/` 目录，复制 `.env.example` 为 `.env`，填写数据库配置与 LLM 配置
2. **安装依赖并启动后端**：`pip install -r requirements.txt`，然后 `uvicorn main:app --reload`
3. **安装依赖并启动前端**：进入 `frontend/` 目录，`npm install`，然后 `npm run dev`

访问 http://localhost:5174

### 生产部署

1. 复制 `cp .env.docker .env` 并填写真实配置
2. 执行 `docker compose up -d` 启动所有服务

详见部署文档（DEPLOY.md，本地分发）。

---

## CI/CD 与发布流程

本项目接入了完整的 GitHub Actions CI/CD 流水线：

### 持续集成（CI）

每次推送到 `master` 分支或提交 PR 时自动触发：

- **前端**：`npm ci` → ESLint 检查 → Vitest 单元测试 → Vite 构建 → npm audit
- **后端**：`pip install` → Ruff lint/format 检查 → pytest（含 MySQL + Redis service） → pip-audit
- **桌面端**：Electron 构建验证

Lint 步骤为 informational 模式（`continue-on-error: true`），不阻断流水线，便于渐进式修复历史代码。

### 持续交付（CD）

推送 `v*.*.*` 格式的 tag 时自动触发 release workflow：

```bash
# 发布新版本
git tag v1.2.0
git push origin v1.2.0
```

自动完成：

1. **构建并推送 Docker 镜像到 GHCR**：
   - `ghcr.io/<owner>/note-taking-assistant/backend:v1.2.0`
   - `ghcr.io/<owner>/note-taking-assistant/frontend:v1.2.0`
   - 同时打 `:latest` 标签
2. **创建 GitHub Release**：自动从 CHANGELOG.md 提取本版本说明，附 Docker 镜像拉取命令

部署时只需在 `docker-compose.yml` 中将 `build:` 替换为 `image:` 指向 GHCR 镜像即可。

---

## API 文档

后端启动后访问 `http://localhost:8000/docs` 查看 Swagger UI。

---

## 安全说明

我们重视用户数据安全，采取了多层防护措施。具体安全机制请参考内部文档。

---

## 常见问题

**Q：AI 功能不可用？**
- Web 版：请先在个人中心配置您的云端 API Key
- 桌面版：请确认 LM Studio Local Server 已启动

**Q：API Key 安全吗？**
- 您的密钥经过加密存储，我们不会明文记录或泄露。前端展示时仅返回后四位掩码用于确认。

**Q：支持哪些 LLM 服务？**
- 所有兼容 OpenAI API 格式的服务均可使用

---

## 更多文档

| 文档 | 内容 |
|------|------|
| [`CHANGELOG.md`](CHANGELOG.md) | 版本更新记录（Keep a Changelog） |
| [`docs/architecture.md`](docs/architecture.md) | 架构说明（开发/生产架构、端口映射、安全） |
| [`docs/er-diagram.md`](docs/er-diagram.md) | 数据库 ER 图（9 张表） |
| [`backend/README.md`](backend/README.md) | 后端开发说明与 API 接口一览 |
| [`desktop/README.md`](desktop/README.md) | 桌面版说明 |
| [`docs/specs/`](docs/specs/) | 历史方案与审查文档归档 |
| 应用内 `/manual` | 终端用户操作手册 |

---

## 贡献

欢迎提交 Issue / Pull Request！

---

## License

**MIT License**（详见 [LICENSE](LICENSE)）

---

<div align="center">

**🌟 如果你觉得这个项目还不错，点个 Star 支持一下～**

<br>

**v1.2.0** · 最后更新：2026-08-23

</div>
