# 智能笔记助手 — 代码库健康审查与修改方案

> 审查日期：2026-06-29  
> 项目版本：v1.1.0  
> 审查范围：`note-takingAssistant/`（Web 全栈）+ `Desktop-note/`（桌面客户端）  
> **执行状态**：第 1 轮已由 Trae 完成 10/13 项（77%），第 2 轮待完成 3 项

---

## 执行进度追踪

| 批次 | 编号 | 问题 | 状态 | 验证结果 |
|------|------|------|------|----------|
| 1 | 2.3 | 死依赖清理 | ✅ 完成 | `mysql-connector-python` + `requests` 已删除，Dockerfile 已简化 |
| 1 | 3.5 | Nginx HTTP gzip | ✅ 完成 | `nginx.http.conf` 已添加 gzip 块 |
| 1 | 3.1 | 路由名称统一 | ✅ 完成 | `/kg` 为主路由，`/knowledge-graph` 重定向 |
| 1 | 3.2 | /manual 权限修复 | ✅ 完成 | `requiresAuth: false` |
| 1 | 3.3 | KG 数量限制 | ✅ 完成 | `MAX_NOTES_FOR_GRAPH = 100` + `.limit()` |
| 1 | 3.4 | 桌面端 CI | ✅ 完成 | `.github/workflows/desktop-ci.yml` 已创建 |
| 1 | 4.2 | 测试覆盖率 | ✅ 完成 | `pytest-cov` 已添加，CI 已改为 `--cov=app` |
| 2 | 2.4 | wangeditor v4→v5 | ✅ 完成 | `RichText.vue` 已重写为 v5 API，构建通过 |
| - | 2.1 | 删除冗余迁移脚本 | ✅ 完成 | `migrate_add_token_gen.py` + `add_user_llm_settings.py` 已删除 |
| - | 4.3 | inspect_db.py 整理 | ✅ 完成 | 已移入 `backend/scripts/` |
| 2 | **2.1** | **引入 Alembic** | ❌ 未做 | 无 `alembic/`、无 `alembic.ini` |
| 3 | **2.2** | **UserCenter 拆分** | ❌ 未做 | 仍为 1806 行 |
| 3 | **4.4** | **ai_service.py 清理** | ❌ 未做 | 兼容层文件仍在 |

### 额外发现

- `npm install` 后显示 **8 个漏洞（3 moderate, 4 high, 1 critical）**，应及时排查修复
- 后端 `pytest` 8 个测试因本地 MySQL 未启动而跳过，非代码问题

---

## 👇 以下为待完成项目（请继续执行）

---


---

## 1. 项目现状概览

| 维度 | 评价 | 说明 |
|------|------|------|
| 目录结构 | ✅ 优秀 | `api/core/crud/models/services/utils` 分层清晰，前后端分离明确 |
| 配置管理 | ⚠️ 良好 | `.env.example` 完整，但存在 3 份 `.env` 分散在不同目录 |
| 安全设计 | ✅ 优秀 | 7 层安全防护；jti 黑名单 + token_gen 代数双重令牌撤销 |
| API 契约 | ✅ 良好 | 前端 Axios 封装统一，后端 Pydantic 验证完备 |
| 文档 | ✅ 优秀 | README、CHANGELOG、DEPLOY、架构图、ER 图、提示词指南齐全 |
| 测试 | ⚠️ 基本 | 后端 8 个测试文件 + 前端 2 个测试，但无覆盖率度量 |
| 依赖管理 | ⚠️ 良好 | 含未使用依赖，需清理 |
| 性能 | ⚠️ 部分风险 | 知识图谱全量加载无分页；AI 流式输出设计良好 |
| 迁移 | 🔴 需改进 | 3 种迁移方式共存，无版本追踪 |
| CI/CD | ⚠️ 基本 | Web 端有 GitHub Actions，桌面端无 CI |

---

## 2. P1 — 建议优先处理

### 2.1 迁移方案碎片化（严重）

**现状排查结果：**

项目中存在 **3 种不同的数据库迁移机制**，没有统一的版本追踪：

| 方式 | 文件 | 位置 |
|------|------|------|
| **启动时自动迁移** | `startup_migrations.py` | `backend/app/core/` |
| **独立迁移脚本** | `add_avatar_to_users.py`, `add_user_llm_settings.py`, `check_user_avatar.py`, `cleanup_orphan_avatars.py`, `create_ai_usage_log.py` | `backend/migrations/`（5 个文件） |
| **根目录迁移** | `migrate_add_token_gen.py` | `backend/`（不在 migrations 目录） |

**重复/冲突分析：**

| 功能 | 出现位置 | 冲突风险 |
|------|----------|----------|
| `token_gen` 列 | `startup_migrations.py:19` + `migrate_add_token_gen.py` | 🔴 两处都尝试创建同名列 |
| `llm_base_url` 等列 | `startup_migrations.py:16-18` + `add_user_llm_settings.py` | 🟡 后者直接委托前者执行 |
| `oauth_accounts` 表 | `startup_migrations.py:90-135` | 🟢 仅一处 |

**代码风格不一致：**
- `migrate_add_token_gen.py` 使用 `engine.begin()`
- `add_user_llm_settings.py` 使用 `AsyncSessionLocal()`
- `startup_migrations.py` 使用 `AsyncSession` 作为参数
- 错误处理和日志格式各不相同

**修改方案：**

引入 **Alembic** 统一管理迁移，步骤如下：

```
步骤 1：安装 alembic
  backend/requirements.txt 添加: alembic>=1.13.0

步骤 2：初始化 Alembic
  cd backend && alembic init alembic

步骤 3：将现有迁移转换为 Alembic 版本
  - 简化 startup_migrations.py，只保留 idempotent 检测逻辑
  - 所有手动迁移合并为初始 Alembic revision

步骤 4：移除重复/冗余脚本
  - 删除 backend/migrate_add_token_gen.py（已被 startup_migrations 覆盖）
  - 删除 migrations/add_user_llm_settings.py（直接委托，无独立价值）
  - 保留 check_user_avatar.py（检查脚本，非迁移）
  - 保留 cleanup_orphan_avatars.py（维护工具，非迁移）
```

**影响文件：**
| 文件 | 操作 |
|------|------|
| `backend/requirements.txt` | 添加 `alembic>=1.13.0` |
| `backend/alembic/` | 新增目录 |
| `backend/alembic.ini` | 新增 |
| `backend/migrate_add_token_gen.py` | 删除 |
| `backend/migrations/add_user_llm_settings.py` | 删除 |
| `backend/app/core/startup_migrations.py` | 简化（移除与 Alembic 重复的 DDL） |

---

### 2.2 超大 Vue 组件（严重）

**现状排查结果：**

| 文件 | 行数 | 包含内容 |
|------|------|----------|
| `UserCenter.vue` | **1806** | 6 张卡片 + 5 个对话框 + 头像上传 + 密码修改 + LLM 设置 + 账号绑定 + 法律文档 |
| `KnowledgeGraph.vue` | **1370** | Three.js 3D 渲染 + ECharts + 图谱操作 + 数据加载 |
| `UserManual.vue` | 1097 | 纯静态 Markdown 渲染 |
| `NoteTranslate.vue` | 999 | 翻译界面 + 流式输出 + 文件上传 |
| `AiGenerate.vue` | 809 | 笔记生成 |
| `AiSummarize.vue` | 875 | 笔记总结 |

**修改方案（以 UserCenter.vue 为例）：**

```
拆分目标（每个子组件 100-250 行）：

src/views/user/UserCenter.vue        (主容器，~200行)
src/views/user/UserProfileCard.vue   (个人信息 + 头像上传)
src/views/user/UserStatsCard.vue     (数据统计)
src/views/user/UserLlmSettings.vue   (AI/BYOK 设置)
src/views/user/UserAboutCard.vue     (关于与本机)
src/views/user/UserPasswordForm.vue  (安全设置/改密码)
src/views/user/UserBindingsPanel.vue (账号绑定)
src/views/user/UserLegalDialogs.vue  (用户协议 + 隐私政策)
```

每个子组件：
- `defineProps` 接收数据
- `defineEmits` 通知父组件事件
- 自包含 `<script setup>` 逻辑

**影响文件：**
| 文件 | 操作 |
|------|------|
| `frontend/src/views/user/UserCenter.vue` | 重写为容器组件（1806 → ~200 行） |
| `frontend/src/views/user/UserProfileCard.vue` | 新增 |
| `frontend/src/views/user/UserStatsCard.vue` | 新增 |
| `frontend/src/views/user/UserLlmSettings.vue` | 新增 |
| `frontend/src/views/user/UserAboutCard.vue` | 新增 |
| `frontend/src/views/user/UserPasswordForm.vue` | 新增 |
| `frontend/src/views/user/UserBindingsPanel.vue` | 新增 |
| `frontend/src/views/user/UserLegalDialogs.vue` | 新增 |

> 其他大组件（KnowledgeGraph.vue、NoteTranslate.vue 等）可后续按同样原则拆分。

---

### 2.3 死依赖（中等）

**现状排查结果：**

| 依赖 | 位置 | 使用情况 | 建议 |
|------|------|----------|------|
| `mysql-connector-python>=9.1.0` | `backend/requirements.txt:12` | ❌ 未使用（已在源码中 grep 确认无 `import mysql.connector`） | **删除** |
| `requests>=2.32.0` | `backend/requirements.txt:9` | ⚠️ 仅在 `tests/test_chat_api.py:4` 使用 | **移至 `requirements-dev.txt`** |
| `three: ^0.185.0` | `frontend/package.json:25` | ✅ 仅 `KnowledgeGraph.vue:126` 使用（`import * as THREE`） | 保留（合理使用） |
| `gsap: ^3.15.0` | `frontend/package.json:18` | ✅ 仅 `KnowledgeGraph.vue:129` 使用（`import { gsap }`） | 保留（合理使用） |

**`mysql-connector-python` 为什么存在？**
- 这是同步 MySQL 驱动，项目实际使用 `aiomysql`（异步）+ `SQLAlchemy`
- 可能是早期开发时引入的残留，或 `pip install mysql-connector-python aiomysql` 误操作
- Dockerfile 中安装的 `default-libmysqlclient-dev` 也是为这个包准备的

**修改方案：**

```
1. requirements.txt:
   - 删除 mysql-connector-python>=9.1.0
   - 删除 requests>=2.32.0

2. requirements-dev.txt:
   + requests>=2.32.0  （测试用）
   + httpx>=0.27.0     （已有）

3. Dockerfile:
   - 删除 RUN apt-get install ... default-libmysqlclient-dev
   （aiomysql 不需要 libmysqlclient，它用纯 Python 实现）

 修改前 (Dockerfile:6-9):
   RUN apt-get update && apt-get install -y --no-install-recommends \
       gcc \
       default-libmysqlclient-dev \
       && rm -rf /var/lib/apt/lists/*

 修改后:
   # aiomysql 使用纯 Python MySQL 协议，无需系统级 MySQL 客户端库
   RUN apt-get update && apt-get install -y --no-install-recommends \
       gcc \
       && rm -rf /var/lib/apt/lists/*
```

**影响文件：**
| 文件 | 操作 |
|------|------|
| `backend/requirements.txt` | 删除 2 行 |
| `backend/requirements-dev.txt` | 添加 `requests>=2.32.0` |
| `backend/Dockerfile` | 删除 `default-libmysqlclient-dev` |

---

### 2.4 wangeditor v4 已弃用（中等）

**现状排查结果：**

| 项 | 详情 |
|----|------|
| 当前版本 | `wangeditor: ^4.7.15` |
| 使用点 | 仅 `frontend/src/components/RichText.vue`（1 个文件，106 行） |
| 用法 | `new WangEditor(el)`, `.config.uploadImgShowBase64`, `.txt.html()` |
| 官方状态 | v4 已停止维护，v5 已发布 2+ 年 |
| 安全风险 | v4 不再接收安全补丁 |

**v4 → v5 迁移成本评估：**

v5 的 API 有变化，但 `RichText.vue` 使用的 API 很简单：

| v4 API | v5 API |
|--------|--------|
| `new WangEditor(el)` | `createEditor({ selector: el })` |
| `editor.config.uploadImgShowBase64` | `editorConfig.MENU_CONF['uploadImage'].base64LimitSize` |
| `editor.config.onchange` | `editor.on('change', callback)` |
| `editor.txt.html()` | `editor.getHtml()` |
| `editor.txt.html(html)` | `editor.setHtml(html)` |

**修改方案：**

```bash
# 卸载旧版，安装新版
npm uninstall wangeditor
npm install @wangeditor/editor @wangeditor/editor-for-vue@next
```

`RichText.vue` 组件重写为 wangeditor v5 API，改动约 40 行。

**影响文件：**
| 文件 | 操作 |
|------|------|
| `frontend/package.json` | `wangeditor` → `@wangeditor/editor` + `@wangeditor/editor-for-vue` |
| `frontend/src/components/RichText.vue` | 重写 ~40 行 |

---

## 3. P2 — 建议改善

### 3.1 路由名称不一致

**现状排查结果：**

| 来源 | 路径 | 不一致 |
|------|------|--------|
| `router/index.js:72` | `/knowledge-graph` | — |
| `README.md:292` | `/kg` | 文档与实际不符 |

**修改方案：**
- 将路由改为 `/kg`（更短，与 README 一致）
- 或保持 `/knowledge-graph` 并更新 README
- **推荐方案**：两者都支持 —— 路由注册 `/kg`，并添加 `/knowledge-graph` → `/kg` 的重定向

```js
// router/index.js
{ path: '/kg', name: 'KnowledgeGraph', component: ... }
{ path: '/knowledge-graph', redirect: '/kg' }  // 兼容旧链接
```

**影响文件：**
| 文件 | 操作 |
|------|------|
| `frontend/src/router/index.js` | 修改 2 行 |

---

### 3.2 `/manual` 路由权限错误

**现状排查结果：**

| 来源 | 内容 | 冲突 |
|------|------|------|
| `router/index.js:82` | `meta: { requiresAuth: true }` | 要求登录 |
| `README.md:296` | `登录要求：否` | 不要求登录 |

**排查确认：** `UserManual.vue` 确实是纯静态帮助文档，不使用任何用户数据，不需要登录即可查看合理。这应该是配置遗漏。

**修改方案：**
```js
// router/index.js:82
meta: { requiresAuth: true, transition: 'fade' }
// 改为
meta: { requiresAuth: false, transition: 'fade' }
```

**影响文件：**
| 文件 | 操作 |
|------|------|
| `frontend/src/router/index.js` | 修改 1 行（`true` → `false`） |

---

### 3.3 知识图谱全量加载无分页

**现状排查结果：**

| 函数 | 查询方式 | 风险 |
|------|----------|------|
| `build_knowledge_graph()` (L197) | `select(NoteDB)...scalars().all()` | 🔴 全量 |
| `get_kg_from_db()` (L388-401) | 3 次 `scalars().all()` (concepts + relations + notes) | 🔴 全量 |
| `_extract_concepts_with_llm()` | 每次调用 1 次 LLM API | 🔴 N 次 LLM 调用 |
| `_compute_tfidf()` | O(N²) 相似度计算（双重循环 L205-220） | 🟡 二阶复杂度 |

**100 篇笔记时的影响：**
- 100 次 LLM 概念提取（每次 ~1-3 秒）
- 100×99/2 = 4950 次余弦相似度计算
- 可能超时

**修改方案（渐进式）：**

```
步骤 1（最小改动）：添加笔记数量硬限制
  build_knowledge_graph() 在最前面加:
  if len(notes) > 100:
      notes = notes[:100]  # 只处理最新的 100 篇

步骤 2（中期改善）：添加 LIMIT 到 SQL 查询
  select(NoteDB)...limit(100)

步骤 3（长期方案）：真正的分页 + 增量构建
  - 后端提供分页 API
  - 前端按需加载节点展开后的关联
```

**影响文件：**
| 文件 | 操作 |
|------|------|
| `backend/app/services/knowledge_graph_service.py` | 添加数量限制（+3 行） |

---

### 3.4 桌面端无 CI

**现状排查结果：**

- Web 端有 `.github/workflows/ci.yml` —— 覆盖前端构建/测试 + 后端 pytest
- Desktop-note 项目：**0 个 CI 文件**
- 测试代码：**0 个**（grep `[Test]`/`[Fact]`/`[TestMethod]` 返回空）
- 结构正确：`SmartNote.App`（UI）、`SmartNote.Core`（业务）、`SmartNote.Data`（EF Core 数据访问）

**修改方案（最小化）：**

```yaml
# .github/workflows/desktop-ci.yml
name: Desktop CI
on:
  push:
    branches: [main, master]
    paths:
      - 'Desktop-note/**'
  pull_request:
    branches: [main, master]

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
        with:
          dotnet-version: 8.0.x
      - run: dotnet restore Desktop-note/SmartNote.sln
      - run: dotnet build Desktop-note/SmartNote.sln --configuration Release --no-restore
```

**影响文件：**
| 文件 | 操作 |
|------|------|
| `.github/workflows/desktop-ci.yml` | 新增 |

---

### 3.5 Nginx HTTP 配置缺少 gzip

**现状排查结果：**

| 配置 | gzip | 使用场景 |
|------|------|----------|
| `nginx.http.conf` | ❌ 无 | 首次部署、证书未就绪 |
| `nginx.https.conf` | ✅ 有（L51-56） | 证书就绪后 |

**影响：** 首次部署时 (HTTP 模式)，静态资源无压缩，首屏加载慢。`entrypoint.sh` 在证书存在时自动切换到 HTTPS 配置，所以这是**临时阶段**的问题，但 Nginx 镜像体积小，启用 gzip 几乎零成本。

**修改方案：** 将 `nginx.https.conf` 中的 gzip 块复制到 `nginx.http.conf` 的 server 块中。

```
在 nginx.http.conf 的 server 块中添加（L40 server 闭合前）:
    # gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json application/javascript application/xml font/truetype font/opentype application/vnd.ms-fontobject image/svg+xml;
```

**影响文件：**
| 文件 | 操作 |
|------|------|
| `frontend/nginx.http.conf` | 添加 gzip 配置块（+7 行） |

---

## 4. P3 — 改进空间

### 4.1 Net6.0 包在 Net8.0 项目中

**结论：这是有意为之，不是需要修复的问题。**

`WinUiBuildFix.targets` 解释了原因：WinUI XAML Compiler 工具链（`net472` 和 `net6.0` 目录）运行在 .NET Framework / .NET 6 运行时上，但引用了 `System.Security.Permissions` 和 `System.Configuration.ConfigurationManager`。需要将这些 DLL 从 NuGet 缓存复制到工具目录才能完成编译。

这两个包仅用于**构建时**，不影响运行时。目前 .NET 8 兼容的 8.0.x 版本**不存在**这些包（它们是 .NET 6 时代的 polyfill）。

**建议：** 在 `WinUiBuildFix.targets` 中添加注释说明，避免未来误读。

---

### 4.2 无测试覆盖率度量

**修改方案：**

```yaml
# CI 中替换:
- run: python -m pytest -q
# 为:
- run: python -m pytest -q --cov=app --cov-report=term-missing
```

```json
// frontend/package.json 中 vitest 配置添加:
"test": "vitest run --coverage"
```

需要安装 `pytest-cov` 到 `requirements-dev.txt`。

**影响文件：**
| 文件 | 操作 |
|------|------|
| `backend/requirements-dev.txt` | 添加 `pytest-cov>=5.0.0` |
| `.github/workflows/ci.yml` | 修改 pytest 命令 |

---

### 4.3 根目录脚本整理

| 文件 | 位置 | 类型 | 建议 |
|------|------|------|------|
| `inspect_db.py` | `backend/` | 运维工具 | → 移入 `backend/scripts/` |
| `migrate_add_token_gen.py` | `backend/` | 迁移脚本 | → 删除（被 startup_migrations 覆盖） |

---

### 4.4 `ai_service.py` 兼容层标记

`backend/app/services/ai_service.py` 明确标注为"兼容层"，全部委托给：
- `note_generator.py`
- `note_analyzer.py`
- `chat_service.py`

**建议：** 如果 API 路由层已全部迁移到新模块，本次可删除此文件（仅 39 行）。否则保留并添加 `@deprecated` 注释。

---

### 4.5 前端路由规范

`/kg` 和 `/knowledge-graph` 的问题上面已解决。同样需要检查的知识图谱相关命名：

| 路由 | 前端路径 | API 前缀 | 一致性 |
|------|--=--------|----------|--------|
| KnowledgeGraph | `/kg` | `/api/v1/kg` | ✅ 一致 |

---

## 5. 按文件列出的修改清单

### 需要修改的文件

| 文件 | 问题编号 | 改动类型 | 改动量 |
|------|----------|----------|--------|
| `backend/requirements.txt` | 2.3 | 删除 2 行 | -2 行 |
| `backend/requirements-dev.txt` | 2.3, 4.2 | 添加 2 行 | +2 行 |
| `backend/Dockerfile` | 2.3 | 删除 1 个 apt 包 | -1 行 |
| `frontend/nginx.http.conf` | 3.5 | 添加 gzip 块 | +7 行 |
| `frontend/src/router/index.js` | 3.1, 3.2 | 路由名称 + 权限 | 修改 3 行 |
| `backend/app/services/knowledge_graph_service.py` | 3.3 | 添加数量限制 | +3 行 |
| `frontend/package.json` | 2.4 | wangeditor 替换 | 修改 2 行 |
| `frontend/src/components/RichText.vue` | 2.4 | wangeditor v5 API | ~40 行 |
| `.github/workflows/ci.yml` | 4.2 | pytest --cov | 修改 1 行 |

### 需要新增的文件

| 文件 | 问题编号 | 用途 |
|------|----------|------|
| `.github/workflows/desktop-ci.yml` | 3.4 | 桌面端 CI |
| `backend/alembic/` + `backend/alembic.ini` | 2.1 | 迁移管理 |
| `frontend/src/views/user/UserProfileCard.vue` | 2.2 | UserCenter 拆分 |
| `frontend/src/views/user/UserStatsCard.vue` | 2.2 | UserCenter 拆分 |
| `frontend/src/views/user/UserLlmSettings.vue` | 2.2 | UserCenter 拆分 |
| `frontend/src/views/user/UserAboutCard.vue` | 2.2 | UserCenter 拆分 |
| `frontend/src/views/user/UserPasswordForm.vue` | 2.2 | UserCenter 拆分 |
| `frontend/src/views/user/UserBindingsPanel.vue` | 2.2 | UserCenter 拆分 |
| `frontend/src/views/user/UserLegalDialogs.vue` | 2.2 | UserCenter 拆分 |

### 需要删除的文件

| 文件 | 问题编号 | 原因 |
|------|----------|------|
| `backend/migrate_add_token_gen.py` | 2.1 | 与 startup_migrations 重复 |
| `backend/migrations/add_user_llm_settings.py` | 2.1 | 仅委托 startup_migrations，无独立价值 |

---

## 6. 修改顺序建议

```
第 1 批（低风险，可独立完成）：
  1. 删除死依赖 (2.3)            ← 改 3 个文件，10 分钟
  2. Nginx HTTP 添加 gzip (3.5)   ← 改 1 个文件，5 分钟
  3. 路由名称不一致 (3.1)         ← 改 1 个文件，5 分钟
  4. /manual 权限修复 (3.2)       ← 改 1 个文件，1 分钟
  5. 知识图谱数量限制 (3.3)       ← 改 1 个文件，5 分钟
  6. 桌面端 CI (3.4)              ← 新增 1 个文件，15 分钟
  7. pytest-cov (4.2)             ← 改 2 个文件，10 分钟

第 2 批（中等风险，需验证）：
  8. wangeditor v4 → v5 (2.4)     ← 改 2 个文件，需验证富文本功能
  9. 迁移 to Alembic (2.1)        ← 改/增/删 5+ 文件，需验证数据库

第 3 批（重构，需充分测试）：
  10. UserCenter 组件拆分 (2.2)   ← 9 个文件，需完整回归测试
  11. 其他大组件拆分（KnowledgeGraph, NoteTranslate 等）
```

---

## ═══════════════════════════════════════════
## 以下为第 2 轮待执行任务（Trae 请继续）
## ═══════════════════════════════════════════

---

## 任务 A：引入 Alembic 迁移管理（来源 2.1）

### 背景

项目中存在 `startup_migrations.py` 做启动时自动 DDL，但它没有版本追踪，无法回滚。已有 2 个冗余脚本已删除。现在需要正式引入 Alembic。

### 执行步骤

**步骤 1：安装 alembic**

在 `backend/requirements.txt` 末尾添加一行：
```
alembic>=1.13.0
```

**步骤 2：初始化 Alembic**

```bash
cd backend
pip install alembic
alembic init alembic
```

**步骤 3：配置 alembic.ini**

编辑 `backend/alembic.ini`，找到 `sqlalchemy.url` 行，替换为：
```ini
sqlalchemy.url = mysql+aiomysql://root:root@127.0.0.1:3306/note_db
```
（开发环境默认值即可，生产通过环境变量覆盖）

**步骤 4：配置 alembic/env.py**

编辑 `backend/alembic/env.py`，需要让它能 import 项目的 SQLAlchemy `Base`。在文件顶部附近添加：

```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.config import settings
from app.core.database import Base
from app.models.user import UserDB, OAuthAccountDB
from app.models.note import NoteDB
from app.models.ai_usage import AIUsageLog
from app.models.kg import KGConceptDB, KGRelationDB, KGStatusDB

target_metadata = Base.metadata
```

并把 `target_metadata = None` 改为上面的 `target_metadata = Base.metadata`。

同时修改 `run_migrations_online` 中的 `connectable` 创建逻辑，使其使用异步引擎（因为项目是 async SQLAlchemy）。关键是替换 `connectable = engine_from_config(...)` 为：

```python
from sqlalchemy.ext.asyncio import create_async_engine
connectable = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
)
```

并添加 `do_run_migrations` 的 async 版本：

```python
def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations():
    connectable = create_async_engine(settings.DATABASE_URL)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

# 替换 run_migrations_online 函数体为：
asyncio.run(run_async_migrations())
```

`asyncio` 需要在文件顶部 import。

**步骤 5：生成初始 migration**

```bash
cd backend
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

**步骤 6：简化 startup_migrations.py**

保留 `startup_migrations.py`，但将其职责缩减为：**仅在 Alembic 尚未运行时做 light idempotent 检测**。具体做法：

- 先检查 `alembic_version` 表是否存在
- 若存在 → 跳过所有 DDL（Alembic 已接管）
- 若不存在 → 执行现有 idempotent DDL（向后兼容老部署）

添加检测逻辑：

```python
async def _alembic_applied(conn):
    """Return True if alembic_version table exists, meaning Alembic has taken over."""
    r = await conn.scalar(
        text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name='alembic_version'")
    )
    return (r or 0) > 0

# 在 ensure_user_llm_columns 和 ensure_user_oauth_columns 开头各加：
# if await _alembic_applied(db): return
```

### 影响文件

| 文件 | 操作 |
|------|------|
| `backend/requirements.txt` | 添加 `alembic>=1.13.0` |
| `backend/alembic/` | 新增目录（`alembic init` 自动生成） |
| `backend/alembic.ini` | 新增（修改 sqlalchemy.url） |
| `backend/alembic/env.py` | 修改配置异步引擎 + target_metadata |
| `backend/app/core/startup_migrations.py` | 添加 Alembic 检测，跳过已接管表 |

### 验证方法

```bash
cd backend
alembic current        # 应显示当前 revision
alembic upgrade head   # 应无错误
pytest -q              # 测试仍通过
```

---

## 任务 B：拆分 UserCenter.vue（来源 2.2）

### 背景

`frontend/src/views/user/UserCenter.vue` 有 **1806 行**，包含了 6 张卡片、5 个对话框。需要拆分为独立子组件。

### 拆分策略

当前 UserCenter.vue 模板结构：
```
个人信息卡片（头像 + 昵称 + 邮箱）
统计数据卡片（笔记数 + AI次数 + 活跃天数）
AI/BYOK 设置卡片
关于与本机卡片
安全设置卡片（修改密码）
账号绑定卡片（昵称 + GitHub + 邮箱）
退出登录按钮
5 个对话框（改昵称 / 绑定邮箱 / 换绑邮箱 / 解除邮箱 / 法律文档）
```

拆分为 7 个子组件 + 1 个主容器：

| 新文件 | 内容 | 预计行数 |
|--------|------|----------|
| `UserProfileCard.vue` | 头像上传 + 昵称 + 邮箱 + 注册日期 | ~180 |
| `UserStatsCard.vue` | 笔记数量/AI次数/活跃天数 三个统计项 | ~120 |
| `UserLlmSettings.vue` | API基址/模型/密钥 表单 + 保存 | ~200 |
| `UserAboutCard.vue` | 应用信息 + UA + 法律文档链接 | ~140 |
| `UserPasswordForm.vue` | 密码修改表单 + 强度指示器 | ~180 |
| `UserBindingsPanel.vue` | 昵称修改 + GitHub绑定 + 邮箱绑定 | ~350 |
| `UserLegalDialogs.vue` | 用户协议 + 隐私政策对话框 | ~80 |
| `UserCenter.vue` | 容器：布局 + 数据加载 + 事件协调 | ~200 |

### 拆分规则

1. 每个子组件用 `<script setup>` + `defineProps` + `defineEmits`
2. 主容器 `UserCenter.vue` 负责：`onMounted` 数据加载、共享状态管理、子组件事件处理
3. 子组件通过 props 接收数据，通过 emits 通知父组件刷新
4. 共享的样式（卡片折叠动画等）提取到 `src/assets/styles/user-center-shared.css`
5. 共享的工具函数（`formatDate`, `formatDays`, `buildAvatarUrl` 等）保留在主容器或提取到 `src/composables/useUserCenter.js`

### 影响文件

| 文件 | 操作 |
|------|------|
| `frontend/src/views/user/UserCenter.vue` | 重写（1806→~200行） |
| `frontend/src/views/user/UserProfileCard.vue` | 新增 |
| `frontend/src/views/user/UserStatsCard.vue` | 新增 |
| `frontend/src/views/user/UserLlmSettings.vue` | 新增 |
| `frontend/src/views/user/UserAboutCard.vue` | 新增 |
| `frontend/src/views/user/UserPasswordForm.vue` | 新增 |
| `frontend/src/views/user/UserBindingsPanel.vue` | 新增 |
| `frontend/src/views/user/UserLegalDialogs.vue` | 新增 |

### 验证方法

```bash
cd frontend
npm run build     # 构建无报错
npm run test      # 29 tests 继续通过
```

启动 dev server 后手动检查：
- 个人信息展示正常
- 头像上传正常
- AI 设置保存正常
- 密码修改正常
- GitHub/邮箱绑定正常
- 折叠面板动画正常

---

## 任务 C：清理 ai_service.py 兼容层（来源 4.4）

### 背景

`backend/app/services/ai_service.py`（39 行）明确标注为"兼容层"，全部委托给 `note_generator.py`、`note_analyzer.py`、`chat_service.py`。需要确认无调用方后删除或标记 deprecated。

### 步骤

**步骤 1：确认调用方**

```bash
cd backend
grep -rn "ai_service\|ai_generate_note\|ai_summarize_note\|ai_chat" app/ --include="*.py" | grep -v "ai_service.py" | grep -v __pycache__
```

如果 `app/api/` 中已全部改用新模块（`generate_note_stream`, `analyze_note`, `chat_with_ai`），则可以安全删除。

**步骤 2a：若安全 → 删除**

删除 `backend/app/services/ai_service.py`，同时修改 `backend/app/services/__init__.py`，移除对 `ai_service` 的 re-export。

**步骤 2b：若仍有旧调用 → 标记 deprecated**

在 `ai_service.py` 的每个函数上方添加 Python `DeprecationWarning`：

```python
import warnings

def ai_generate_note(**kwargs):
    warnings.warn("ai_generate_note is deprecated, use generate_note_stream from note_generator", DeprecationWarning, stacklevel=2)
    ...
```

### 影响文件

| 文件 | 操作 |
|------|------|
| `backend/app/services/ai_service.py` | 删除或标记 deprecated |
| `backend/app/services/__init__.py` | 可能需移除旧 import（若删除） |

---

## 额外：修复 npm 安全漏洞

### 背景

`npm install` 后报告 8 个漏洞。应及时排查。

### 步骤

```bash
cd frontend
npm audit                           # 查看详情
npm audit fix                       # 尝试自动修复（非破坏性）
```

如果 `npm audit fix --force` 是唯一选项，请先列出破坏性变更再决定是否执行。

---

## 执行汇总

| 任务 | 来源 | 优先级 | 预计工作量 |
|------|------|--------|-----------|
| A | 2.1 迁移碎片化 | P1 | ~30 分钟 |
| B | 2.2 大组件拆分 | P1 | ~2 小时 |
| C | 4.4 兼容层清理 | P3 | ~10 分钟 |
| D | npm 漏洞 | 额外发现 | ~15 分钟 |

**建议执行顺序**：C → D → A → B（先简单后复杂）

---

> **审查人：** Claude (Opus 4.8)  
> **第 1 轮完成：** 2026-06-29（10/13 项，77%）  
> **第 2 轮待执行：** 以上 A/B/C/D 四项
