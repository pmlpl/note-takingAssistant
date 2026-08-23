# 桌面端优化 — 验收反馈

> 海鸥验收，2026-06-30
> 给 trae 的修复清单

---

## 总体评价

Phase 1-4 的 **安全修复、Bug 修复、架构改动全做对了**。路径白名单、sandbox、CSP、单实例锁、protocol.handle 迁移、baseURL 竞态修复、共享常量抽取、菜单导入导出、全局变量清理——每一项都按 spec 实现了。

以下 6 个问题是漏的或没做干净的，按优先级排列。

---

## 🔴 问题 1：前端 dist 和桌面 dist 都是脏的（严重）

**现象**：
- `frontend/dist/assets/` 有 78 个文件（23MB），index.html 只引用约 15 个
- `desktop/dist/assets/` 有 102 个文件（25MB），同样的脏数据被复制过来
- 例如 `AiGenerate-*.js` 有 2 份，`KnowledgeGraph-*.js` 有 2 份，`NoteEdit-*.js` 有 2 份
- 三份 `AiGenerate-*.js` 全部 11244 bytes，bit-identical

**原因**：`copy-frontend.js` 改对了（先 rmSync 再复制），但**源头 `frontend/dist` 本身就是脏的**。Vite 默认 `emptyOutDir: true` 应该清理，但你改 vite.config.js 之后没有先删 dist 再 build，导致新旧 hash 文件共存。

**修法**：

```bash
# 1. 手动清空前端 dist
cd note-takingAssistant/frontend
rm -rf dist
npm run build

# 2. 重新复制到桌面端
cd ../../desktop
npm run copy:frontend
```

然后验证：
```bash
# 前端 dist 应该只有 index.html 引用的那些文件，大约 15-20 个
ls note-takingAssistant/frontend/dist/assets/*.js | wc -l
# 桌面 dist 同理
ls desktop/dist/assets/*.js | wc -l
```

---

## 🔴 问题 2：Electron 版本没升级

**spec 要求**：`electron: ^33.0.0`, `electron-builder: ^25.1.0`

**实际**：`electron: ^28.2.0`, `electron-builder: ^24.9.1`

**影响**：代码里已经用了 `protocol.handle`（Electron 25+）和 `net.fetch`，Electron 28 能跑但已经到了 EOL，缺少安全补丁。

**修法**：改 `desktop/package.json`：

```json
"devDependencies": {
  "cross-env": "^7.0.3",
  "electron": "^33.0.0",
  "electron-builder": "^25.1.0"
}
```

然后 `rm -rf node_modules package-lock.json && npm install`。

> ⚠️ Electron 33 要求 Node >= 20，确认开发机 Node 版本够。

---

## 🟡 问题 3：`开发运行.bat` 没设 NODE_ENV

**spec 要求**：第 33 行 `call npm run dev` 之前加 `set NODE_ENV=development`

**实际**：没加，文件末尾还是直接 `call npm run dev`

**影响**：`isDev` 改用 `!app.isPackaged` 了所以影响不大，但 `cross-env` 包白装了。加上更规范。

**修法**：在 `desktop/开发运行.bat` 的 `echo 启动 Electron 桌面端...` 之后、`call npm run dev` 之前加一行：

```batch
set NODE_ENV=development
```

---

## 🟡 问题 4：UserAboutCard 保存提示文案没改

**spec 要求**：`ElMessage.success('服务器地址已保存，将在下次请求时生效')` 改成 `'服务器地址已保存'`

**实际**：仍然是 `'服务器地址已保存，将在下次请求时生效'`

**原因**：`saveServerUrl` 函数调了 `updateBaseUrl(cleanUrl)`（立即生效），不是"下次请求"，提示文案误导用户。

**修法**：改 `frontend/src/views/user/UserAboutCard.vue` 第 110 行：

```js
// ❌ 旧的
ElMessage.success('服务器地址已保存，将在下次请求时生效')

// ✅ 改成
ElMessage.success('服务器地址已保存')
```

---

## 🟡 问题 5：package.json 缺 `engines` 字段

**spec 要求**：加 `"engines": { "node": ">=20.0.0" }`

**实际**：没加

**修法**：在 `desktop/package.json` 的 `"license": "MIT",` 后面加：

```json
"engines": {
  "node": ">=20.0.0"
},
```

---

## 🟢 问题 6：`electron-updater` 版本

**spec 写的是**：`"electron-updater": "^6.3.0"`

**实际安装的是**：`"electron-updater": "^6.1.8"`

**影响**：不大，6.1.x 到 6.3.x 没有 breaking change。升级 Electron 到 33 的时候顺手升一下就行：

```bash
npm install electron-updater@^6.3.0
```

---

## ✅ 做对的（逐项确认）

以下全部按 spec 正确实现，无需改动：

| 文件 | 改动 | 状态 |
|------|------|:--:|
| `electron/ipc.js` | 路径白名单 + 文件大小限制 + 协议白名单 + notification/autoLaunch handler + await shell.openPath + 删 global.mainWindow | ✅ |
| `electron/main.js` | sandbox:true + 删 CORS handler + 删重复 activate + 单实例锁 + protocol.handle + CSP + isDev 改 app.isPackaged + store 加密 + macOS 托盘 + updater 集成 + URL 白名单 | ✅ |
| `electron/preload.js` | 协议白名单 + notification/autoLaunch + channel 警告 + once + platform getter | ✅ |
| `electron/updater.js` | 新建，自动更新模块 | ✅ |
| `scripts/copy-frontend.js` | 重写，rmSync 清空 + 错误处理 + 环境变量 | ✅ |
| `frontend/src/config/desktop.js` | 新建共享常量 | ✅ |
| `frontend/src/composables/useApiConfig.js` | import 常量 + try/catch | ✅ |
| `frontend/src/composables/useDesktop.js` | showOpenDirectory + showNotification + autoLaunch | ✅ |
| `frontend/src/api/index.js` | import 常量 + baseURL 竞态修复 + 去 window.__updateApiBaseUrl | ✅ |
| `frontend/src/router/index.js` | isDesktop 提取到顶部 | ✅ |
| `frontend/src/App.vue` | 菜单导入导出真正实现 + menuCleanupFns 去全局 | ✅ |
| `frontend/vite.config.js` | chunkSizeWarningLimit 800 | ✅ |
| `frontend/index.html` | Google Fonts display=swap | ✅ |
| `desktop/package.json` | electron-updater 依赖 + publish 配置 + nsis.unicode + sign:null | ✅ |
| `desktop/build/generate-icons.js` | 保持为说明文档（没问题） | ✅ |

---

## 执行顺序

1. **先修问题 1**（清 dist 重建）—— 这是最直观的问题
2. **再修问题 2**（升级 Electron）—— 顺便修问题 6
3. **问题 3、4、5** 一把梭改完
4. 改完跑一遍 `开发运行.bat` 确认 app 正常启动

---

> 总体：代码改动质量不错，安全部分改得严实。就这几个漏的补一下，10 分钟的事。
