# AGENTS.md — 仓库约定与 Agent 协作规范

面向在本仓库工作的 agent（含 Multica 文档专员）的协作与文档维护约定。

## 项目概况

NoteMind 智能笔记助手，个人学习与创作场景的全栈应用。

| 模块 | 技术栈 | 说明 |
|------|--------|------|
| `frontend/` | Vue 3 + Vite + Element Plus | Web 前端（本地开发端口 5174） |
| `backend/` | FastAPI + SQLAlchemy 2.x + MySQL 8 + Redis 7 | 后端 API（端口 8000，`uvicorn main:app`） |
| `desktop/` | Electron 28.x | Windows 桌面客户端（AI 可直连本地 LM Studio） |
| `docs/` | Markdown | 架构 / ER 图 / 方案归档 |
| `docker-compose.yml` | MySQL + Redis + backend + frontend + certbot | 生产一键部署 |

## 文档结构（职责归属）

| 文档 | 职责 | 维护要求 |
|------|------|----------|
| `README.md` | 项目总览 + 全文档入口 | 版本徽标与 CHANGELOG 对齐；页脚日期随更新同步 |
| `CHANGELOG.md` | 版本变更记录（Keep a Changelog） | **唯一版本基准**；每次对外变更必须记录 |
| `DEPLOY.md` | 部署指南 | ⚠️ 冻结态：被 `.gitignore` 忽略但仍在 git index，含本机路径与域名，是否公开待 owner 决策 |
| `docs/architecture.md` | 架构说明（Mermaid、端口、安全） | 与 `docker-compose.yml` 保持一致 |
| `docs/er-diagram.md` | 数据库 ER 图（9 张表） | 与 `backend/app/models/` 保持一致 |
| `backend/README.md` | 后端开发说明 + API 接口一览 | API 表与 `backend/app/api/v1/*.py` 路由同步 |
| `desktop/README.md` | 桌面端说明 | 与 desktop 代码、差异表同步 |
| `frontend/src/views/help/UserManual.vue` | 终端用户操作手册（应用内 /manual） | 用户可见功能变更时同步 |
| `docs/specs/` | 历史方案与审查文档归档 | 命名 `<YYYY-MM-DD>-<kebab-case>.md`；内容不删 |
| `LICENSE` | MIT License（Copyright (c) 2026 pmlpl） | 版权持有人变更需 owner 确认 |
| `AGENTS.md` | 本文件 | 与仓库实际状态同步 |

## 文档规范

- **命名**：kebab-case 小写英文文件名；方案/审查类文档带日期前缀（`<YYYY-MM-DD>-<kebab-case>.md`）。
- **语言**：对外发布文档用英文（README 徽标、CI 描述）；内部文档以中文为主。
- **内容溯源**：文档结论必须源自实际代码与 git 历史，标注依据（`path/to/file.py:行号` 或 commit hash），禁止臆造。
- **删除文档**：先确认无其他文档引用（grep），并在变更说明中给出「删什么 + 为什么 + 是否被引用」。

## 更新规则（触发即同步）

以下任一情况发生时，必须同步更新 CHANGELOG 与受影响文档，且不留过期信息：

- PR 合并 / release / 版本打 tag
- 功能上线 / 破坏性改动（API 契约、数据库结构、配置项变化）
- 依赖升级、CI/CD 或部署配置变更
- 前端/后端/桌面端测试基线完成

## 已知不一致（截至 2026-08-23）

- **版本治理**：`git tag` 仅有 v1.0.1 / v1.1.0，**v1.2.0 从未打 tag**；`frontend/package.json` 与 `desktop/package.json` 版本仍为 1.1.0；CHANGELOG 的 [1.1.0] / [1.1.1] 条目分别对应 tag v1.0.1 / v1.1.0（错位一位）。统一策略待产品决策，改动版本相关文档前先确认。
- **重复文档（已解决）**：`desktop/renderer/src/components/icons/README.md` 曾与 `frontend/src/components/icons/README.md` 字节级重复（SHA256 一致），已由 owner 确认后删除（2026-08-23），保留 `frontend/` 副本。
- **README 页脚**：`v1.2.0 · 最后更新` 日期在每次文档更新时同步。

## 本仓库 agent 职责边界

- **文档专员**只新增/修改/删除文档文件（`*.md`、`LICENSE` 等），不修改产品业务代码；每轮结束在 issue 评论写明改动清单、依据与是否需要新 issue 跟进。
- 其他 agent 修改代码时，如涉及 API / 数据库 / 配置 / 版本变化，应在 PR 说明中提示文档专员同步文档（或直接更新对应文档）。
