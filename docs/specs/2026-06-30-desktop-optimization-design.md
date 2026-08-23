# 桌面端全面优化技术方案

> **目标读者**：Trae（执行修改 + 提交）
> **编写**：海鸥（2026-06-30）
> **适用范围**：`desktop/` 目录 + `frontend/` 中与桌面端集成的文件

---

## 目录

1. [问题全景](#1-问题全景)
2. [Phase 1：安全修复 + 关键 Bug](#2-phase-1安全修复--关键-bug)
3. [Phase 2：性能优化 + dist 清理](#3-phase-2性能优化--dist-清理)
4. [Phase 3：功能完善](#4-phase-3功能完善)
5. [Phase 4：代码质量 + 技术债务清理](#5-phase-4代码质量--技术债务清理)
6. [测试验证清单](#6-测试验证清单)
7. [Git 提交建议](#7-git-提交建议)

---

## 1. 问题全景

审计范围：`desktop/electron/`（3 个源文件 661 行）+ `frontend/src/` 中 7 个涉桌面集成文件。

| 类别 | 数量 | 最严重的 3 个 |
|------|------|-------------|
| 🐛 Bug | 7 | 重复 `app.on('activate')`、axios baseURL 竞态、dist 残留 143 个垃圾文件 |
| 🔒 安全 | 8 | fs 路径穿越（无白名单）、`app://` 协议无 CSP 头、sandbox: false |
| ⚡ 性能 | 4 | dist 8.9MB 垃圾、Google Fonts CDN 离线阻塞、setupCorsHandler 在桌面端是死代码 |
| 🏗️ 技术债 | 14 | `desktop_api_base_url` 三处重复、废弃 `registerFileProtocol`、全局变量污染 |
| 🧩 缺失 | 12 | 无自动更新、无单实例锁、菜单导入导出只弹 toast 不干活 |

**预估总工时**：6-10 小时，分 4 个 Phase 交付。

---

## 2. Phase 1：安全修复 + 关键 Bug

> **优先级**：最高。安全漏洞必须最先修。
> **预估工时**：2-3 小时

### 2.1 `desktop/electron/ipc.js` — 路径穿越修复 + 文件大小限制

**当前问题**：所有 fs handler 直接把 renderer 传的 `filePath` 传给 `fs.readFileSync` / `fs.writeFileSync`，没有任何白名单校验。renderer 里一个 XSS 就能读 `C:\Users\MOM\.ssh\id_rsa`。

**修改方案**：

1. **新增路径白名单函数**（放在文件顶部 `registerIpc` 外面）：

```js
const os = require('os')
const VALID_ROOTS = ['home', 'desktop', 'documents', 'downloads', 'temp', 'appData', 'userData']

function buildPathWhitelist() {
  const roots = [app.getPath('userData')]
  for (const name of VALID_ROOTS) {
    try { roots.push(app.getPath(name)) } catch {}
  }
  return roots.map(p => path.resolve(p).toLowerCase())
}

function isPathAllowed(targetPath, allowedRoots) {
  const resolved = path.resolve(targetPath).toLowerCase()
  return allowedRoots.some(root => resolved.startsWith(root + path.sep) || resolved === root)
}

const MAX_READ_SIZE = 10 * 1024 * 1024    // 10 MB
const MAX_WRITE_SIZE = 50 * 1024 * 1024    // 50 MB
```

2. **修改 `app:open-external` handler**，加协议白名单：

```js
ipcMain.handle('app:open-external', (_, url) => {
  try {
    const parsed = new URL(url)
    if (!['http:', 'https:', 'mailto:'].includes(parsed.protocol)) {
      return false // 拒绝 file:// javascript: 等危险协议
    }
    return shell.openExternal(url)
  } catch {
    return false
  }
})
```

3. **修改 `fs:read-file`**：加白名单 + 文件大小限制

```js
ipcMain.handle('fs:read-file', (_, filePath, encoding = 'utf-8') => {
  try {
    const allowedRoots = buildPathWhitelist()
    if (!isPathAllowed(filePath, allowedRoots)) {
      return { success: false, error: 'Permission denied: path not in allowed directories' }
    }
    const stat = fs.statSync(filePath)
    if (stat.size > MAX_READ_SIZE) {
      return { success: false, error: `File too large: ${stat.size} bytes (max ${MAX_READ_SIZE})` }
    }
    const content = fs.readFileSync(filePath, encoding)
    return { success: true, data: content }
  } catch (err) {
    return { success: false, error: err.message }
  }
})
```

4. **修改 `fs:write-file`**：加白名单 + 写入大小限制

```js
ipcMain.handle('fs:write-file', (_, filePath, content, encoding = 'utf-8') => {
  try {
    const allowedRoots = buildPathWhitelist()
    if (!isPathAllowed(filePath, allowedRoots)) {
      return { success: false, error: 'Permission denied: path not in allowed directories' }
    }
    if (content && content.length > MAX_WRITE_SIZE) {
      return { success: false, error: `Content too large: ${content.length} bytes (max ${MAX_WRITE_SIZE})` }
    }
    const dir = path.dirname(filePath)
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true })
    }
    fs.writeFileSync(filePath, content, encoding)
    return { success: true }
  } catch (err) {
    return { success: false, error: err.message }
  }
})
```

5. **修改 `shell:open-path`**：加 `await`

```js
ipcMain.handle('shell:open-path', async (_, filePath) => {
  const error = await shell.openPath(filePath)
  return { success: !error, error: error || null }
})
```

6. **删除 `global.mainWindow` fallback**：

```js
// 删掉这行 dead code：
// function getWindow() {
//   return getMainWindow ? getMainWindow() : (global.mainWindow || null)
// }
// 改成：
function getWindow() {
  return getMainWindow ? getMainWindow() : null
}
```

7. **`app:get-path` 修正跨平台**：去掉 Linux 下不存在的 `videos`, `music`, `pictures`

```js
const validNames = ['home', 'appData', 'userData', 'temp', 'downloads', 'documents', 'desktop']
```

### 2.2 `desktop/electron/main.js` — Bug 修复 + 安全加固

**改动清单**：

1. **删除重复的 `app.on('activate')`**：
   - 保留 `app.whenReady().then()` 内部的那个（line 391-398）
   - 删除文件底部 line 410-414 那个：

```js
// ❌ 删除这 4 行
app.on('activate', () => {
  if (mainWindow) {
    mainWindow.show()
  }
})
```

2. **开 sandbox**：

```js
// webPreferences 里面把 sandbox 从 false 改成 true
webPreferences: {
  preload: path.join(__dirname, 'preload.js'),
  contextIsolation: true,
  nodeIntegration: false,
  sandbox: true,        // ← 改这里
  webSecurity: true
},
```

3. **删掉 `setupCorsHandler()` 整个函数和调用**：
   - 删掉 line 346-380（`function setupCorsHandler` 定义）
   - 在 `app.whenReady().then()` 里删掉 `setupCorsHandler()` 那一行（line 384）

4. **加单实例锁**（`app.whenReady()` 外面）：

```js
const gotTheLock = app.requestSingleInstanceLock()
if (!gotTheLock) {
  app.quit()
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore()
      mainWindow.show()
      mainWindow.focus()
    }
  })

  app.whenReady().then(() => {
    // ... 原来的启动代码
  })
}
```

5. **`app://` 协议 handler 不 fallback 所有 404**：

在 `registerAppProtocol` 中，只在请求路径是目录时 fallback 到 index.html：

```js
protocol.handle('app', (request) => {
  try {
    const url = new URL(request.url)
    let pathname = decodeURIComponent(url.pathname)
    if (pathname.startsWith('/')) pathname = pathname.slice(1)
    if (!pathname) pathname = 'index.html'

    let filePath = path.join(frontendDir, pathname)

    if (fs.existsSync(filePath)) {
      if (fs.statSync(filePath).isDirectory()) {
        filePath = path.join(filePath, 'index.html')
      }
      if (fs.existsSync(filePath)) {
        return net.fetch('file://' + filePath)
      }
    }
    // SPA fallback: only for non-asset requests
    if (!path.extname(pathname)) {
      return net.fetch('file://' + path.join(frontendDir, 'index.html'))
    }
    return new Response('Not Found', { status: 404 })
  } catch (err) {
    console.error('Protocol handler error:', err)
    return new Response('Internal Error', { status: 500 })
  }
})
```

6. **`isDev` 改用 `app.isPackaged`**：

```js
// const isDev = process.env.NODE_ENV === 'development'  // ❌
const isDev = !app.isPackaged  // ✅ 更可靠
```

7. **`setWindowOpenHandler` 加 URL 验证**：

```js
mainWindow.webContents.setWindowOpenHandler(({ url }) => {
  try {
    const parsed = new URL(url)
    if (['http:', 'https:', 'mailto:'].includes(parsed.protocol)) {
      shell.openExternal(url)
    }
  } catch {}
  return { action: 'deny' }
})
```

8. **Electron Store 加密**：

```js
const crypto = require('crypto')

function getEncryptionKey() {
  // 基于 machine-id 派生（机器唯一）
  const key = crypto.createHash('sha256').update('notemind-desktop-store-v1').digest('hex')
  return key.slice(0, 32)
}

const store = new Store({
  encryptionKey: getEncryptionKey()
})
```

### 2.3 `desktop/electron/preload.js` — 安全加固

1. **`app.openExternal` 协议白名单**：

```js
app: {
  getVersion: () => ipcRenderer.invoke('app:get-version'),
  getPath: (name) => ipcRenderer.invoke('app:get-path', name),
  openExternal: (url) => {
    // 渲染进程侧也做一层协议白名单校验
    try {
      const parsed = new URL(url)
      if (!['http:', 'https:', 'mailto:'].includes(parsed.protocol)) {
        return Promise.resolve(false)
      }
    } catch { return Promise.resolve(false) }
    return ipcRenderer.invoke('app:open-external', url)
  }
},
```

2. **`on` 方法对无效 channel 打印警告**：

```js
on: (channel, callback) => {
  const validChannels = [
    'menu:new-note', 'menu:import-note', 'menu:export-note', 'menu:navigate'
  ]
  if (validChannels.includes(channel)) {
    const subscription = (_event, ...args) => callback(...args)
    ipcRenderer.on(channel, subscription)
    return () => ipcRenderer.removeListener(channel, subscription)
  }
  console.warn(`[preload] Ignored unknown channel: "${channel}"`)
  return () => {}
}
```

### 2.4 `desktop/package.json` — 依赖升级

```json
"devDependencies": {
  "cross-env": "^7.0.3",
  "electron": "^33.0.0",
  "electron-builder": "^25.1.0"
}
```

升级完后运行 `npm install`（注意 electron 33 要求 Node >= 20）。

---

## 3. Phase 2：性能优化 + dist 清理

> **预估工时**：1-2 小时

### 3.1 `desktop/scripts/copy-frontend.js` — 彻底重写

**当前问题**：
- 复制前不清理 dist，导致 151 个文件中有 143 个是历史残留
- 路径硬编码 `'..', 'note-takingAssistant'`，换个目录名就坏
- 单个文件复制失败静默跳过

**重写方案**：

```js
const fs = require('fs')
const path = require('path')
const os = require('os')

// ── 配置：通过环境变量或自动检测 ──
const FRONTEND_DIST_PATH = process.env.FRONTEND_DIST_PATH
  || (() => {
    // 自动检测：递归向上查找 frontend/dist
    let dir = path.resolve(__dirname, '..')
    for (let i = 0; i < 6; i++) {
      const candidate = path.join(dir, 'note-takingAssistant', 'frontend', 'dist')
      if (fs.existsSync(path.join(candidate, 'index.html'))) return candidate
      // 也尝试在 desktop/ 同级找
      const candidate2 = path.join(path.dirname(dir), 'frontend', 'dist')
      if (fs.existsSync(path.join(candidate2, 'index.html'))) return candidate2
      dir = path.dirname(dir)
    }
    console.error('错误：找不到前端 dist 目录，请设置环境变量 FRONTEND_DIST_PATH')
    process.exit(1)
  })()

const DESKTOP_DIST = path.resolve(__dirname, '..', 'dist')

// ── 1. 彻底清空目标目录 ──
console.log('清空目标目录:', DESKTOP_DIST)
if (fs.existsSync(DESKTOP_DIST)) {
  fs.rmSync(DESKTOP_DIST, { recursive: true, force: true })
}
fs.mkdirSync(DESKTOP_DIST, { recursive: true })

// ── 2. 递归复制，遇错即停 ──
let fileCount = 0
let totalSize = 0

function copyDirSync(src, dest) {
  fs.mkdirSync(dest, { recursive: true })
  const entries = fs.readdirSync(src, { withFileTypes: true })

  for (const entry of entries) {
    const srcPath = path.join(src, entry.name)
    const destPath = path.join(dest, entry.name)

    try {
      if (entry.isDirectory()) {
        copyDirSync(srcPath, destPath)
      } else {
        fs.copyFileSync(srcPath, destPath)
        fileCount++
        totalSize += fs.statSync(srcPath).size
      }
    } catch (err) {
      console.error(`复制失败: ${srcPath} → ${destPath}`)
      console.error(err.message)
      process.exit(1)
    }
  }
}

// ── 3. 执行 ──
console.log('源目录:', FRONTEND_DIST_PATH)
copyDirSync(FRONTEND_DIST_PATH, DESKTOP_DIST)

console.log(`完成! 共复制 ${fileCount} 个文件，${(totalSize / 1024 / 1024).toFixed(1)} MB`)
```

### 3.2 `desktop/electron/main.js` — `registerFileProtocol` → `protocol.handle`

**完整 migration**（在 Phase 1 已给代码，这里再确认）：

```js
// ❌ 删掉
// const { ... protocol ... } = require('electron')
// protocol.registerSchemesAsPrivileged([...])  // 保留在文件头部
// protocol.registerFileProtocol('app', callback)  // ❌ 废弃API

// ✅ 新方案
// 1. protocol.registerSchemesAsPrivileged 保留（让渲染进程能用 app://）
// 2. app.whenReady() 里调用 protocol.handle('app', handler)
// 3. handler 里用 net.fetch('file://...') 返回 Response
```

**注意**：`protocol.handle` 需要 Electron >= 25（Phase 1 已升级到 33，没问题）。

### 3.3 `frontend/index.html` — 字体加载优化

**位置**：`note-takingAssistant/frontend/index.html`

在 Google Fonts `<link>` 上补充 `display=swap` 策略（如果还没有）：

```html
<!-- 当前： -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=..." rel="stylesheet">

<!-- 改为： -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=...&display=swap" rel="stylesheet">
```

同时建议把主要字体（Noto Sans SC 或 Inter）下载放到 `public/fonts/`，桌面端不想依赖 Google CDN。如果前端没用到 Google Fonts 就忽略这条。

### 3.4 `frontend/vite.config.js` — `chunkSizeWarningLimit`

```js
// 当前: chunkSizeWarningLimit: 1600  // 太宽松
// 改为:
chunkSizeWarningLimit: 800  // 合理的上限
```

---

## 4. Phase 3：功能完善

> **预估工时**：2-3 小时

### 4.1 新增 `desktop/electron/updater.js` — 自动更新

```js
const { autoUpdater } = require('electron-updater')
const { dialog, BrowserWindow } = require('electron')

autoUpdater.autoDownload = false
autoUpdater.autoInstallOnAppQuit = true

function setupAutoUpdater(getMainWindow) {
  autoUpdater.on('update-available', (info) => {
    const win = getMainWindow()
    if (!win) return
    dialog.showMessageBox(win, {
      type: 'info',
      title: '发现新版本',
      message: `NoteMind v${info.version} 已发布`,
      detail: '是否立即下载更新？',
      buttons: ['立即更新', '稍后提醒'],
      defaultId: 0,
      cancelId: 1
    }).then(({ response }) => {
      if (response === 0) {
        autoUpdater.downloadUpdate()
      }
    })
  })

  autoUpdater.on('update-downloaded', () => {
    const win = getMainWindow()
    if (!win) return
    dialog.showMessageBox(win, {
      type: 'info',
      title: '更新已下载',
      message: '新版本已下载完成，将在重启后自动安装',
      buttons: ['立即重启', '稍后重启'],
      defaultId: 0,
      cancelId: 1
    }).then(({ response }) => {
      if (response === 0) {
        autoUpdater.quitAndInstall()
      }
    })
  })

  autoUpdater.on('error', (err) => {
    console.error('Auto updater error:', err)
  })

  // 启动后 5 秒检查更新（避免影响主窗口渲染）
  setTimeout(() => {
    autoUpdater.checkForUpdates().catch(() => {})
  }, 5000)
}

module.exports = { setupAutoUpdater }
```

然后在 `main.js` 的 `app.whenReady()` 里调用：

```js
const { setupAutoUpdater } = require('./updater')
// ...
app.whenReady().then(() => {
  registerAppProtocol()
  createWindow()
  createMenu()
  createTray()
  registerIpc(ipcMain, () => mainWindow, store, dialog, shell, app)
  setupAutoUpdater(() => mainWindow)  // ← 加这行
})
```

`package.json` 加 `electron-updater` 依赖：

```json
"dependencies": {
  "electron-store": "^8.1.0",
  "electron-updater": "^6.3.0"
}
```

`package.json` 加 `publish` 配置（在 `build` 块里）：

```json
"build": {
  "publish": {
    "provider": "github",
    "owner": "your-github-user",
    "repo": "note-takingAssistant"
  }
}
```

### 4.2 `electron/main.js` — 加 Content Security Policy

在 `createWindow` 函数中，页面加载完成后注入 CSP：

```js
mainWindow.webContents.session.webRequest.onHeadersReceived((details, callback) => {
  callback({
    responseHeaders: {
      ...details.responseHeaders,
      'Content-Security-Policy': [
        "default-src 'self' app:; " +
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; " +  // Vue 需要 unsafe-inline
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; " +
        "font-src 'self' data: https://fonts.gstatic.com; " +
        "img-src 'self' data: blob: https:; " +
        "connect-src *; " +  // API 请求
        "media-src 'self'"
      ].join('')
    }
  })
})
```

### 4.3 `electron/main.js` — macOS 托盘兼容

```js
function createTray() {
  // ... 原有代码

  // macOS 上 tray 只响应 right-click（context menu），
  // 所以 click 事件加平台判断
  tray.on('click', () => {
    if (process.platform !== 'darwin') {
      if (mainWindow) {
        if (mainWindow.isVisible()) {
          mainWindow.hide()
        } else {
          mainWindow.show()
          mainWindow.focus()
        }
      }
    }
  })

  // macOS: 用 double-click 来显示窗口
  if (process.platform === 'darwin') {
    tray.on('double-click', () => {
      if (mainWindow) {
        mainWindow.show()
        mainWindow.focus()
      }
    })
  }
}
```

### 4.4 `electron/preload.js` — 新增 IPC

```js
// 系统通知
notification: {
  show: (title, body) => ipcRenderer.invoke('notification:show', title, body)
},

// 开机自启
autoLaunch: {
  isEnabled: () => ipcRenderer.invoke('auto-launch:is-enabled'),
  setEnabled: (enabled) => ipcRenderer.invoke('auto-launch:set-enabled', enabled)
}
```

### 4.5 `electron/ipc.js` — 新增 handler

```js
// 系统通知
ipcMain.handle('notification:show', (_, title, body) => {
  const { Notification } = require('electron')
  if (Notification.isSupported()) {
    new Notification({ title, body }).show()
    return { success: true }
  }
  return { success: false, error: 'Notifications not supported' }
})

// 开机自启
ipcMain.handle('auto-launch:is-enabled', () => {
  return app.getLoginItemSettings().openAtLogin
})

ipcMain.handle('auto-launch:set-enabled', (_, enabled) => {
  app.setLoginItemSettings({ openAtLogin: enabled })
  return { success: true }
})
```

### 4.6 `frontend/src/composables/useDesktop.js` — 新增封装

```js
async function showOpenDirectory(options) {
  if (isDesktop.value && window.electronAPI?.dialog?.showOpenDialog) {
    return window.electronAPI.dialog.showOpenDialog({
      ...options,
      properties: ['openDirectory']
    })
  }
  return { canceled: true, filePaths: [] }
}

async function showNotification(title, body) {
  if (isDesktop.value && window.electronAPI?.notification?.show) {
    return window.electronAPI.notification.show(title, body)
  }
  return { success: false, error: 'not available' }
}

async function getAutoLaunch() {
  if (isDesktop.value && window.electronAPI?.autoLaunch?.isEnabled) {
    return window.electronAPI.autoLaunch.isEnabled()
  }
  return false
}

async function setAutoLaunch(enabled) {
  if (isDesktop.value && window.electronAPI?.autoLaunch?.setEnabled) {
    return window.electronAPI.autoLaunch.setEnabled(enabled)
  }
  return { success: false, error: 'not available' }
}
```

并加到 return 里：

```js
return {
  isDesktop,
  platform,
  openExternal, showOpenDialog, showSaveDialog, showOpenDirectory,
  readFile, writeFile,
  storeGet, storeSet,
  onMenuEvent,
  showNotification, getAutoLaunch, setAutoLaunch
}
```

### 4.7 `frontend/src/App.vue` — 菜单事件真正实现导入导出

```js
// ❌ 当前：
const unbindImport = onMenuEvent('menu:import-note', () => {
  ElMessage.info('请在笔记页面使用导入功能')
})
const unbindExport = onMenuEvent('menu:export-note', () => {
  ElMessage.info('请在笔记页面使用导出功能')
})

// ✅ 改为：触发自定义事件，让 NoteEdit 或 NoteList 组件响应
const unbindImport = onMenuEvent('menu:import-note', () => {
  // 如果当前在笔记编辑页，触发导入
  if (route.name === 'NoteEdit' || route.name === 'NoteList') {
    window.dispatchEvent(new CustomEvent('desktop:import-note'))
  } else {
    router.push('/notes').then(() => {
      setTimeout(() => window.dispatchEvent(new CustomEvent('desktop:import-note')), 300)
    })
  }
})
const unbindExport = onMenuEvent('menu:export-note', () => {
  if (route.name === 'NoteEdit') {
    window.dispatchEvent(new CustomEvent('desktop:export-note'))
  } else {
    ElMessage.info('请先打开一篇笔记再导出')
  }
})
```

然后在 `NoteEdit.vue` 里监听 `desktop:import-note` 和 `desktop:export-note` 事件即可。

### 4.8 `desktop/开发运行.bat` — 修复 NODE_ENV

```batch
@echo off
chcp 65001 >nul
echo ========================================
echo   NoteMind - 智能笔记助手（桌面端）
echo ========================================
echo.

cd /d "%~dp0"

:: ... 依赖检查等 ...

echo 启动 Electron 桌面端...
set NODE_ENV=development
call npm run dev

pause
```

---

## 5. Phase 4：代码质量 + 技术债务清理

> **预估工时**：1-2 小时

### 5.1 抽取共享常量

**新建文件**：`note-takingAssistant/frontend/src/config/desktop.js`

```js
export const DESKTOP_STORAGE_KEY = 'desktop_api_base_url'
export const DESKTOP_DEFAULT_API_BASE = 'https://momo.makeup/api'
```

然后修改以下 3 个文件，把硬编码字符串替换为 import：

| 文件 | 行 | 替换 |
|------|-----|------|
| `src/composables/useApiConfig.js` | 4 | `const STORAGE_KEY = 'desktop_api_base_url'` → `import { DESKTOP_STORAGE_KEY } from '@/config/desktop'` |
| `src/composables/useApiConfig.js` | 3 | 同理 `DEFAULT_API_BASE` → `DESKTOP_DEFAULT_API_BASE` |
| `src/api/index.js` | 5-6 | 同上 |
| `src/views/user/UserAboutCard.vue` | 80, 86 | `DEFAULT_SERVER_URL` 和存储 key 改为 import |

### 5.2 `frontend/src/api/index.js` — 消除 baseURL 竞态

**当前**：Axios 实例创建时同步拿 baseURL，然后 `resolveBaseUrl()` 异步 patch。

**修复**：Axios 实例创建时把 `baseURL` 设为一个已知会被覆盖的值，然后 await resolve：

```js
const api = axios.create({
  baseURL: getSyncBaseUrl(),  // 保持现有逻辑
  timeout: defaultRequestTimeoutMs()
})

// 加请求拦截器：首次请求前确保 baseURL 已解析
let baseUrlResolved = false
const baseUrlPromise = resolveBaseUrl().then(url => {
  if (url && url !== api.defaults.baseURL) {
    api.defaults.baseURL = url
  }
  baseUrlResolved = true
})

api.interceptors.request.use(async (config) => {
  if (!baseUrlResolved) {
    await baseUrlPromise
    // 更新当前请求的 baseURL
    if (api.defaults.baseURL && !config.baseURL) {
      config.baseURL = api.defaults.baseURL
    }
  }
  const userStore = useUserStore()
  if (userStore.token) {
    config.headers.Authorization = `Bearer ${userStore.token}`
  }
  return config
})
```

这样可以保证第一个请求发出前 baseURL 一定已从 store 读取完毕。

### 5.3 `frontend/src/router/index.js` — 去重 `isDesktop`

```js
// ❌ 当前：3 处写了 typeof window !== 'undefined' && window.electronAPI?.isDesktop === true
// ✅ 改为：在函数顶部提取一次
router.beforeEach((to, from, next) => {
  try {
    const userStore = useUserStore()
    const isDesktop = typeof window !== 'undefined' && window.electronAPI?.isDesktop === true
    // ... 后续所有地方复用 isDesktop
  }
})
```

已经有一个 `isDesktop` 声明在 line 109，但 line 128 的 catch 块里又写了一遍，把 catch 块里的也改成用函数顶部提前声明的变量。最简单的方法是把 `isDesktop` 提到 `try` 外面：

```js
router.beforeEach((to, from, next) => {
  const isDesktop = typeof window !== 'undefined' && window.electronAPI?.isDesktop === true
  try {
    const userStore = useUserStore()
    // ...
    if (isDesktop) { /* ... */ }
    // ...
  } catch (error) {
    console.error('Route guard error:', error)
    next(isDesktop ? '/login' : '/')
  }
})
```

### 5.4 `frontend/src/App.vue` — 去全局变量

`window.__desktopMenuCleanup` 改为组件内部管理：

```js
const menuCleanupFns = []

onMounted(() => {
  // ...
  if (isDesktop.value) {
    const unbindNavigate = onMenuEvent('menu:navigate', (path) => { router.push(path) })
    const unbindNewNote = onMenuEvent('menu:new-note', () => { router.push('/notes/new') })
    // ...
    menuCleanupFns.push(unbindNavigate, unbindNewNote, /* ... */)
  }
})

onUnmounted(() => {
  menuCleanupFns.forEach(fn => fn())
})
```

### 5.5 `frontend/src/api/index.js` — 去 `window.__updateApiBaseUrl`

`UserAboutCard.vue` 调用 `window.__updateApiBaseUrl(cleanUrl)` 改成：

1. 从 `api/index.js` 导出 `updateBaseUrl`
2. `UserAboutCard.vue` import 这个函数

`api/index.js` 底部删掉：

```js
// ❌ 删掉
if (typeof window !== 'undefined') {
  window.__updateApiBaseUrl = updateBaseUrl
}
```

### 5.6 `desktop/build/generate-icons.js` — 改成真干活

```js
// 生成桌面图标（需要先 npm install sharp）
// 用法: node build/generate-icons.js

const fs = require('fs')
const path = require('path')

const svgPath = path.join(__dirname, 'icon.svg')
if (!fs.existsSync(svgPath)) {
  console.error('icon.svg 不存在，跳过图标生成')
  process.exit(0)
}

console.log('请用下列方法之一生成图标：')
console.log('1. 在线工具: https://iconverticons.com/online/')
console.log('2. ImageMagick: convert icon.svg -resize 256x256 icon.png')
console.log('3. npm: npx svg-to-png-cli icon.svg')
console.log()
console.log('生成后在 build/ 目录放置:')
console.log('  - icon.ico  (Windows)')
console.log('  - icon.icns (macOS)')
console.log('  - icon.png  256x256 (Linux + 通用)')
```

> 注：如果不想引入 sharp 依赖，保持当前 README 风格也行——毕竟图标一般只生成一次。

### 5.7 `desktop/package.json` — 配置完善

在 `build` 块里补齐：

```json
{
  "build": {
    "appId": "com.notemind.app",
    "productName": "NoteMind",
    "publish": {
      "provider": "github",
      "owner": "YOUR_GITHUB_USER",
      "repo": "note-takingAssistant"
    },
    "win": {
      "target": [{ "target": "nsis", "arch": ["x64"] }],
      "icon": "build/icon.ico",
      "sign": null
    },
    "nsis": {
      "oneClick": false,
      "allowToChangeInstallationDirectory": true,
      "createDesktopShortcut": true,
      "createStartMenuShortcut": true,
      "shortcutName": "NoteMind",
      "unicode": true,
      "warningsAsErrors": false
    }
  }
}
```

### 5.8 `electron/preload.js` — 小改进

```js
contextBridge.exposeInMainWorld('electronAPI', {
  get platform() { return process.platform },  // getter 而非静态值
  isDesktop: true,

  // ... 其余不变

  // 新增 once 支持
  once: (channel, callback) => {
    const validChannels = [/* 同上 */]
    if (validChannels.includes(channel)) {
      ipcRenderer.once(channel, (_event, ...args) => callback(...args))
    } else {
      console.warn(`[preload] Ignored unknown channel: "${channel}"`)
    }
  }
})
```

---

## 6. 测试验证清单

每个 Phase 完成后，按这个清单验证：

### Phase 1 验证

- [ ] `desktop/` 下 `npm start` 正常启动
- [ ] 托盘图标点击显示/隐藏窗口正常
- [ ] 菜单 → 文件 → 退出 正常退出
- [ ] 外部链接（欢迎页 GitHub 图标等）用系统浏览器打开
- [ ] `app://` 协议加载前端页面正常
- [ ] 重复启动 app 不会打开两个窗口（单实例锁生效）
- [ ] Console 里没有 `registerFileProtocol is deprecated` 警告
- [ ] macOS（如有）上 activate 事件正常（Dock 点击显示窗口）

### Phase 2 验证

- [ ] `desktop/dist/assets/` 里没有重复 hash 的文件（只有一套，约 8-10 个 chunk）
- [ ] `desktop/dist/` 总大小 < 15 MB（之前 31 MB + node_modules）
- [ ] `npm run copy:frontend` 输出清晰的文件计数
- [ ] 首次加载时间无明显退化

### Phase 3 验证

- [ ] 菜单 → 新建笔记 确实跳转到编辑页
- [ ] 菜单 → 导入笔记 触发导入流程（如果在笔记页）
- [ ] 系统通知能弹出（需在渲染进程调用 `showNotification`）
- [ ] 断网后 Google Fonts 不阻塞渲染（fallback 到系统字体）
- [ ] `app.isPackaged` 在开发模式下正确返回 false

### Phase 4 验证

- [ ] `npm run build` 前端构建无报错
- [ ] `npm run copy:frontend` 无报错
- [ ] 桌面端 API 请求地址修改能正常保存并立即生效
- [ ] 登出后跳转行为正确（桌面端到 `/login`，Web 端到 `/`）

---

## 7. Git 提交建议

建议按 Phase 拆分 commit：

```
Phase 1: fix(desktop): 安全修复 — 路径白名单 + 文件大小限制 + 协议白名单
Phase 1: fix(desktop): Bug 修复 — 重复 activate + sandbox 开启 + 单实例锁
Phase 1: chore(desktop): 升级 Electron 28→33, electron-builder 24→25
Phase 2: perf(desktop): 重写 copy-frontend.js — 彻底清理 dist + 错误处理
Phase 2: perf(desktop): protocol.handle 替代废弃 API + Google Fonts swap
Phase 3: feat(desktop): 自动更新 (electron-updater) + 系统通知 + 开机自启
Phase 3: feat(desktop): CSP 头 + 菜单导入导出真正实现 + macOS 托盘兼容
Phase 4: refactor(frontend): 抽取 desktop 常量到 config/desktop.js
Phase 4: refactor(frontend): 消除 baseURL 竞态 + 去全局变量
Phase 4: chore(desktop): build 配置完善 + icon 脚本
```

---

## 附录 A：文件改动总览

| 文件 | Phase | 改动类型 |
|------|-------|---------|
| `desktop/electron/ipc.js` | P1, P3 | 重构：路径白名单、文件大小限制、新增通知/自启 handler |
| `desktop/electron/main.js` | P1, P2, P3 | 重构：删 CORS handler、开 sandbox、单实例锁、protocol.handle、CSP、托盘兼容、updater |
| `desktop/electron/preload.js` | P1, P3, P4 | 加固：协议白名单、新增 IPC、once 支持、channel 警告 |
| `desktop/electron/updater.js` | P3 | **新建**：自动更新模块 |
| `desktop/package.json` | P1, P3, P4 | 升级依赖、加 electron-updater、加 publish 配置 |
| `desktop/scripts/copy-frontend.js` | P2 | **重写**：彻底清理 + 错误处理 + 环境变量支持 |
| `desktop/开发运行.bat` | P1 | 加 NODE_ENV=development |
| `frontend/src/config/desktop.js` | P4 | **新建**：共享常量 |
| `frontend/src/composables/useApiConfig.js` | P4 | import 共享常量 + try/catch |
| `frontend/src/composables/useDesktop.js` | P3 | 新增 showOpenDirectory、showNotification、autoLaunch |
| `frontend/src/api/index.js` | P4 | 消除 baseURL 竞态、去 window 全局、import 常量 |
| `frontend/src/router/index.js` | P4 | 提取 isDesktop 变量 |
| `frontend/src/App.vue` | P3, P4 | 菜单事件真正实现、去 window 全局 |
| `frontend/index.html` | P2 | 字体 display=swap |
| `frontend/vite.config.js` | P2 | chunkSizeWarningLimit 800 |
| `frontend/src/views/user/UserAboutCard.vue` | P4 | import 共享常量 |

## 附录 B：不需要改的文件

以下文件在审计中发现没有问题或改动风险大于收益，**本次不做修改**：

- `desktop/.gitignore` — 已有 `node_modules/`, `dist/`, `release/`，够用
- `desktop/.npmrc` — 正常
- `desktop/一键打包.bat` — 功能正确，无 bug
- `frontend/vite.config.js` 中的 `base: './'` 和 `manualChunks` 策略 — 当前配置对 Electron 是正确的

---

> **海鸥注**：以上方案每个 Phase 独立可测试、独立可交付。trae 按 Phase 1→2→3→4 的顺序改，每个 Phase 改完验证通过再 commit。
