const fs = require('fs')
const path = require('path')
const { clipboard, Notification } = require('electron')

const VALID_ROOTS = ['home', 'desktop', 'documents', 'downloads', 'temp', 'appData', 'userData']

function buildPathWhitelist(app) {
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

const MAX_READ_SIZE = 10 * 1024 * 1024
const MAX_WRITE_SIZE = 50 * 1024 * 1024

module.exports = function registerIpc(ipcMain, getMainWindow, store, dialog, shell, app) {
  function getWindow() {
    return getMainWindow ? getMainWindow() : null
  }

  ipcMain.handle('app:get-version', () => {
    return app.getVersion()
  })

  ipcMain.handle('app:get-path', (_, name) => {
    const validNames = ['home', 'appData', 'userData', 'temp', 'downloads', 'documents', 'desktop']
    if (validNames.includes(name)) {
      return app.getPath(name)
    }
    return null
  })

  ipcMain.handle('app:open-external', (_, url) => {
    try {
      const parsed = new URL(url)
      if (!['http:', 'https:', 'mailto:'].includes(parsed.protocol)) {
        return false
      }
      return shell.openExternal(url)
    } catch {
      return false
    }
  })

  ipcMain.handle('window:minimize', () => {
    const win = getWindow()
    if (win) win.minimize()
  })

  ipcMain.handle('window:maximize', () => {
    const win = getWindow()
    if (win) win.maximize()
  })

  ipcMain.handle('window:unmaximize', () => {
    const win = getWindow()
    if (win) win.unmaximize()
  })

  ipcMain.handle('window:close', () => {
    const win = getWindow()
    if (win) win.close()
  })

  ipcMain.handle('window:is-maximized', () => {
    const win = getWindow()
    return win ? win.isMaximized() : false
  })

  ipcMain.handle('window:toggle-maximize', () => {
    const win = getWindow()
    if (win) {
      if (win.isMaximized()) {
        win.unmaximize()
      } else {
        win.maximize()
      }
    }
  })

  ipcMain.handle('window:set-title', (_, title) => {
    const win = getWindow()
    if (win) win.setTitle(title)
  })

  ipcMain.handle('dialog:show-open', (_, options) => {
    const win = getWindow()
    return dialog.showOpenDialog(win, options || {})
  })

  ipcMain.handle('dialog:show-save', (_, options) => {
    const win = getWindow()
    return dialog.showSaveDialog(win, options || {})
  })

  ipcMain.handle('dialog:show-message', (_, options) => {
    const win = getWindow()
    return dialog.showMessageBox(win, options || {})
  })

  ipcMain.handle('fs:read-file', (_, filePath, encoding = 'utf-8') => {
    try {
      const allowedRoots = buildPathWhitelist(app)
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

  ipcMain.handle('fs:write-file', (_, filePath, content, encoding = 'utf-8') => {
    try {
      const allowedRoots = buildPathWhitelist(app)
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

  ipcMain.handle('fs:read-dir', (_, dirPath) => {
    try {
      const allowedRoots = buildPathWhitelist(app)
      if (!isPathAllowed(dirPath, allowedRoots)) {
        return { success: false, error: 'Permission denied: path not in allowed directories' }
      }
      const files = fs.readdirSync(dirPath)
      return { success: true, data: files }
    } catch (err) {
      return { success: false, error: err.message }
    }
  })

  ipcMain.handle('fs:stat', (_, filePath) => {
    try {
      const allowedRoots = buildPathWhitelist(app)
      if (!isPathAllowed(filePath, allowedRoots)) {
        return { success: false, error: 'Permission denied: path not in allowed directories' }
      }
      const stats = fs.statSync(filePath)
      return {
        success: true,
        data: {
          size: stats.size,
          isFile: stats.isFile(),
          isDirectory: stats.isDirectory(),
          mtime: stats.mtime.toISOString(),
          birthtime: stats.birthtime.toISOString()
        }
      }
    } catch (err) {
      return { success: false, error: err.message }
    }
  })

  ipcMain.handle('fs:exists', (_, filePath) => {
    try {
      return { success: true, exists: fs.existsSync(filePath) }
    } catch (err) {
      return { success: false, error: err.message }
    }
  })

  ipcMain.handle('store:get', (_, key, defaultValue) => {
    try {
      return { success: true, data: store.get(key, defaultValue) }
    } catch (err) {
      return { success: false, error: err.message }
    }
  })

  ipcMain.handle('store:set', (_, key, value) => {
    try {
      store.set(key, value)
      return { success: true }
    } catch (err) {
      return { success: false, error: err.message }
    }
  })

  ipcMain.handle('store:delete', (_, key) => {
    try {
      store.delete(key)
      return { success: true }
    } catch (err) {
      return { success: false, error: err.message }
    }
  })

  ipcMain.handle('store:clear', () => {
    try {
      store.clear()
      return { success: true }
    } catch (err) {
      return { success: false, error: err.message }
    }
  })

  ipcMain.handle('shell:open-path', async (_, filePath) => {
    const error = await shell.openPath(filePath)
    return { success: !error, error: error || null }
  })

  ipcMain.handle('shell:show-item-in-folder', (_, filePath) => {
    shell.showItemInFolder(filePath)
  })

  ipcMain.handle('clipboard:write-text', (_, text) => {
    clipboard.writeText(text)
    return { success: true }
  })

  ipcMain.handle('clipboard:read-text', () => {
    return { success: true, data: clipboard.readText() }
  })

  ipcMain.handle('notification:show', (_, title, body) => {
    if (Notification.isSupported()) {
      new Notification({ title, body }).show()
      return { success: true }
    }
    return { success: false, error: 'Notifications not supported' }
  })

  ipcMain.handle('auto-launch:is-enabled', () => {
    return app.getLoginItemSettings().openAtLogin
  })

  ipcMain.handle('auto-launch:set-enabled', (_, enabled) => {
    app.setLoginItemSettings({ openAtLogin: enabled })
    return { success: true }
  })

  ipcMain.handle('oauth:start-github', async (_, authorizeUrl) => {
    const { BrowserWindow } = require('electron')
    const mainWin = getWindow()
    return new Promise((resolve) => {
      const authWin = new BrowserWindow({
        width: 800,
        height: 600,
        parent: mainWin,
        modal: true,
        title: 'GitHub 登录',
        webPreferences: {
          nodeIntegration: false,
          contextIsolation: true,
          sandbox: true
        }
      })

      authWin.setMenuBarVisibility(false)
      authWin.loadURL(authorizeUrl)

      let completed = false

      function handleCallback(url) {
        if (completed) return
        try {
          const urlObj = new URL(url)
          const hasToken = urlObj.searchParams.get('token')
          const hasError = urlObj.searchParams.get('error')
          // 后端最终重定向到 /login?token=xxx 或 /login?error=xxx
          if (hasToken || hasError) {
            completed = true
            authWin.close()
            resolve({ success: true, url })
          }
        } catch {}
      }

      authWin.webContents.on('will-navigate', (event, url) => {
        handleCallback(url)
      })

      authWin.webContents.on('did-redirect-navigation', (event, url) => {
        handleCallback(url)
      })

      authWin.on('closed', () => {
        if (!completed) {
          resolve({ success: false, error: '用户取消了登录' })
        }
      })
    })
  })
}
