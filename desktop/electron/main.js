const { app, BrowserWindow, Menu, Tray, nativeImage, shell, ipcMain, dialog, protocol, net } = require('electron')
const path = require('path')
const fs = require('fs')
const crypto = require('crypto')
const Store = require('electron-store')

process.env.ELECTRON_DISABLE_SECURITY_WARNINGS = 'true'

protocol.registerSchemesAsPrivileged([
  { scheme: 'app', privileges: { standard: true, secure: true, supportFetchAPI: true, corsEnabled: true, stream: true } }
])

function getEncryptionKey() {
  const key = crypto.createHash('sha256').update('notemind-desktop-store-v1').digest('hex')
  return key.slice(0, 32)
}

const store = new Store({
  encryptionKey: getEncryptionKey()
})

let mainWindow = null
let tray = null
let isQuitting = false

const isDev = !app.isPackaged

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

  function getFrontendDir() {
    const distPath = path.join(__dirname, '..', 'dist')
    if (fs.existsSync(path.join(distPath, 'index.html'))) {
      return distPath
    }
    return path.join(process.resourcesPath, 'frontend-dist')
  }

  function registerAppProtocol() {
    const frontendDir = getFrontendDir()

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
        if (!path.extname(pathname)) {
          return net.fetch('file://' + path.join(frontendDir, 'index.html'))
        }
        return new Response('Not Found', { status: 404 })
      } catch (err) {
        console.error('Protocol handler error:', err)
        return new Response('Internal Error', { status: 500 })
      }
    })
  }

  function getFrontendPath() {
    return { type: 'url', path: 'app://localhost/index.html' }
  }

  function getIconPath() {
    const platforms = {
      win32: 'icon.ico',
      darwin: 'icon.icns',
      linux: 'icon.png'
    }
    const iconFile = platforms[process.platform] || 'icon.png'

    const pathsToTry = [
      path.join(__dirname, '..', 'build', iconFile),
      path.join(process.resourcesPath, 'build', iconFile),
      path.join(app.getAppPath(), 'build', iconFile),
      path.join(__dirname, 'build', iconFile)
    ]

    for (const iconPath of pathsToTry) {
      if (fs.existsSync(iconPath)) {
        return iconPath
      }
    }

    const pngPaths = [
      path.join(__dirname, '..', 'build', 'icon.png'),
      path.join(process.resourcesPath, 'build', 'icon.png'),
      path.join(app.getAppPath(), 'build', 'icon.png'),
      path.join(__dirname, 'build', 'icon.png')
    ]

    for (const pngPath of pngPaths) {
      if (fs.existsSync(pngPath)) {
        return pngPath
      }
    }

    return null
  }

  function createWindow() {
    const iconPath = getIconPath()
    mainWindow = new BrowserWindow({
      width: 1280,
      height: 800,
      minWidth: 960,
      minHeight: 640,
      title: 'NoteMind - 智能笔记助手',
      backgroundColor: '#faf8f5',
      frame: false, // 无边框窗口,使用自定义标题栏
      webPreferences: {
        preload: path.join(__dirname, 'preload.js'),
        contextIsolation: true,
        nodeIntegration: false,
        sandbox: true,
        webSecurity: false
      },
      ...(iconPath ? { icon: iconPath } : {})
    })

    mainWindow.webContents.session.webRequest.onHeadersReceived((details, callback) => {
      const newHeaders = { ...details.responseHeaders }

      newHeaders['Content-Security-Policy'] = [
        "default-src 'self' app:; " +
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; " +
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; " +
        "font-src 'self' data: https://fonts.gstatic.com; " +
        "img-src 'self' data: blob: https:; " +
        "connect-src *; " +
        "media-src 'self'"
      ].join('')

      if (details.url && /^https?:\/\//.test(details.url)) {
        const origin = details.requestHeaders?.Origin || '*'
        delete newHeaders['access-control-allow-origin']
        delete newHeaders['Access-Control-Allow-Origin']
        delete newHeaders['access-control-allow-methods']
        delete newHeaders['Access-Control-Allow-Methods']
        delete newHeaders['access-control-allow-headers']
        delete newHeaders['Access-Control-Allow-Headers']
        delete newHeaders['access-control-allow-credentials']
        delete newHeaders['Access-Control-Allow-Credentials']
        delete newHeaders['access-control-expose-headers']
        delete newHeaders['Access-Control-Expose-Headers']
        delete newHeaders['access-control-max-age']
        delete newHeaders['Access-Control-Max-Age']

        newHeaders['Access-Control-Allow-Origin'] = [origin]
        newHeaders['Access-Control-Allow-Methods'] = ['GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD']
        newHeaders['Access-Control-Allow-Headers'] = ['Content-Type, Authorization, Accept, X-Requested-With, X-Request-Id']
        newHeaders['Access-Control-Allow-Credentials'] = ['true']
        newHeaders['Access-Control-Expose-Headers'] = ['Content-Length, Content-Type, Authorization']
        newHeaders['Access-Control-Max-Age'] = ['86400']
      }

      callback({ responseHeaders: newHeaders })
    })

    mainWindow.webContents.session.webRequest.onBeforeSendHeaders((details, callback) => {
      const requestHeaders = { ...details.requestHeaders }
      // 删除 Origin 头，避免 CORS 预检
      if (details.url && details.url.includes('/api/')) {
        delete requestHeaders['Origin']
        delete requestHeaders['origin']
      }
      callback({ requestHeaders })
    })

    // 拦截 OPTIONS 预检请求，直接返回 204，避免服务器不支持 OPTIONS 的问题
    mainWindow.webContents.session.webRequest.onBeforeRequest((details, callback) => {
      if (details.method === 'OPTIONS' && details.url.includes('/api/')) {
        callback({
          response: {
            statusCode: 204,
            headers: {
              'Access-Control-Allow-Origin': '*',
              'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD',
              'Access-Control-Allow-Headers': 'Content-Type, Authorization, Accept, X-Requested-With, X-Request-Id',
              'Access-Control-Allow-Credentials': 'true',
              'Access-Control-Max-Age': '86400'
            }
          }
        })
      } else {
        callback({})
      }
    })

    mainWindow.webContents.session.webRequest.onCompleted((details) => {
      if (details.url && details.url.includes('/api/')) {
        const method = details.method.padEnd(6, ' ')
        const status = String(details.statusCode).padStart(3, ' ')
        const url = details.url.length > 80 ? details.url.substring(0, 80) + '...' : details.url
        console.log(`[API] ${method} ${status} ${url}`)
        if (details.statusCode >= 400) {
          console.log(`      Response headers:`, JSON.stringify(details.responseHeaders))
        }
      }
    })

    mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
      console.error('[PAGE LOAD FAILED]', errorCode, errorDescription)
    })

    const frontend = getFrontendPath()
    if (frontend.type === 'url') {
      mainWindow.loadURL(frontend.path)
    } else {
      mainWindow.loadFile(frontend.path)
    }

    if (isDev) {
      mainWindow.webContents.openDevTools()
    } else {
      mainWindow.webContents.on('before-input-event', (event, input) => {
        if (
          (input.control && input.shift && input.key?.toUpperCase() === 'I') ||
          (input.key === 'F12') ||
          (input.control && input.key?.toUpperCase() === 'J') ||
          (input.control && input.shift && input.key?.toUpperCase() === 'C')
        ) {
          event.preventDefault()
        }
      })
      mainWindow.webContents.on('context-menu', (e, params) => {
        const menu = Menu.buildFromTemplate([
          { role: 'cut', label: '剪切' },
          { role: 'copy', label: '复制' },
          { role: 'paste', label: '粘贴' },
          { type: 'separator' },
          { role: 'selectAll', label: '全选' }
        ])
        menu.popup({ window: mainWindow })
      })
    }

    mainWindow.on('close', (e) => {
      if (!isQuitting) {
        const closeBehavior = store.get('close_behavior', 'quit')

        if (closeBehavior === 'quit') {
          isQuitting = true
          app.quit()
          return
        }

        if (closeBehavior === 'minimize') {
          e.preventDefault()
          mainWindow.hide()
          return
        }

        e.preventDefault()
        dialog.showMessageBox(mainWindow, {
          type: 'question',
          title: '退出确认',
          message: '确定要退出 NoteMind 吗？',
          buttons: ['退出', '最小化到托盘']
        }).then((result) => {
          if (result.response === 0) {
            isQuitting = true
            app.quit()
          } else {
            mainWindow.hide()
          }
        })
      }
    })

    mainWindow.on('closed', () => {
      mainWindow = null
    })

    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
      try {
        const parsed = new URL(url)
        if (['http:', 'https:', 'mailto:'].includes(parsed.protocol)) {
          shell.openExternal(url)
        }
      } catch {}
      return { action: 'deny' }
    })
  }

  function createTray() {
    const iconPath = getIconPath()
    if (!iconPath) {
      tray = null
      return
    }

    const icon = nativeImage.createFromPath(iconPath)
    tray = new Tray(icon)

    const contextMenu = Menu.buildFromTemplate([
      {
        label: '显示主窗口',
        click: () => {
          if (mainWindow) {
            mainWindow.show()
            mainWindow.focus()
          }
        }
      },
      { type: 'separator' },
      {
        label: '退出',
        click: () => {
          isQuitting = true
          app.quit()
        }
      }
    ])

    tray.setToolTip('NoteMind - 智能笔记助手')
    tray.setContextMenu(contextMenu)

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

    if (process.platform === 'darwin') {
      tray.on('double-click', () => {
        if (mainWindow) {
          mainWindow.show()
          mainWindow.focus()
        }
      })
    }
  }

  function createMenu() {
    const template = [
      {
        label: '文件',
        submenu: [
          {
            label: '新建笔记',
            accelerator: 'CmdOrCtrl+Shift+N',
            click: () => {
              if (mainWindow) {
                mainWindow.webContents.send('menu:new-note')
              }
            }
          },
          {
            label: '搜索',
            accelerator: 'CmdOrCtrl+Shift+F',
            click: () => {
              if (mainWindow) {
                mainWindow.webContents.send('menu:search')
              }
            }
          },
          { type: 'separator' },
          {
            label: '导入笔记',
            accelerator: 'CmdOrCtrl+I',
            click: () => {
              if (mainWindow) {
                mainWindow.webContents.send('menu:import-note')
              }
            }
          },
          {
            label: '导出笔记',
            accelerator: 'CmdOrCtrl+E',
            click: () => {
              if (mainWindow) {
                mainWindow.webContents.send('menu:export-note')
              }
            }
          },
          { type: 'separator' },
          {
            label: '退出',
            accelerator: 'CmdOrCtrl+Q',
            click: () => {
              isQuitting = true
              app.quit()
            }
          }
        ]
      },
      {
        label: '编辑',
        submenu: [
          { role: 'undo', label: '撤销' },
          { role: 'redo', label: '重做' },
          { type: 'separator' },
          { role: 'cut', label: '剪切' },
          { role: 'copy', label: '复制' },
          { role: 'paste', label: '粘贴' },
          { role: 'selectall', label: '全选' }
        ]
      },
      {
        label: '视图',
        submenu: [
          { type: 'separator' },
          { role: 'resetzoom', label: '重置缩放' },
          { role: 'zoomin', label: '放大' },
          { role: 'zoomout', label: '缩小' },
          { type: 'separator' },
          { role: 'togglefullscreen', label: '全屏' }
        ]
      },
      {
        label: '导航',
        submenu: [
          {
            label: '首页',
            accelerator: 'CmdOrCtrl+1',
            click: () => {
              if (mainWindow) {
                mainWindow.webContents.send('menu:navigate', '/home')
              }
            }
          },
          {
            label: '我的笔记',
            accelerator: 'CmdOrCtrl+2',
            click: () => {
              if (mainWindow) {
                mainWindow.webContents.send('menu:navigate', '/notes')
              }
            }
          },
          {
            label: 'AI 生成',
            accelerator: 'CmdOrCtrl+3',
            click: () => {
              if (mainWindow) {
                mainWindow.webContents.send('menu:navigate', '/ai/generate')
              }
            }
          },
          {
            label: '思维导图',
            accelerator: 'CmdOrCtrl+4',
            click: () => {
              if (mainWindow) {
                mainWindow.webContents.send('menu:navigate', '/mindmap')
              }
            }
          }
        ]
      },
      {
        label: '帮助',
        submenu: [
          {
            label: '使用说明',
            click: () => {
              if (mainWindow) {
                mainWindow.webContents.send('menu:navigate', '/manual')
              }
            }
          },
          { type: 'separator' },
          {
            label: '关于 NoteMind',
            click: () => {
              dialog.showMessageBox(mainWindow, {
                type: 'info',
                title: '关于 NoteMind',
                message: 'NoteMind - 智能笔记助手',
                detail: `版本: ${app.getVersion()}\n\n基于 AI 的智能笔记管理工具\n支持笔记生成、总结、翻译和思维导图`
              })
            }
          }
        ]
      }
    ]

    if (process.platform === 'darwin') {
      template.unshift({
        label: app.name,
        submenu: [
          { role: 'about', label: '关于' },
          { type: 'separator' },
          { role: 'services', label: '服务' },
          { type: 'separator' },
          { role: 'hide', label: '隐藏' },
          { role: 'hideothers', label: '隐藏其他' },
          { role: 'unhide', label: '显示全部' },
          { type: 'separator' },
          { role: 'quit', label: '退出' }
        ]
      })
    }

    const menu = Menu.buildFromTemplate(template)
    Menu.setApplicationMenu(menu)
  }

  const registerIpc = require('./ipc')
  const { setupAutoUpdater } = require('./updater')

  app.whenReady().then(() => {
    registerAppProtocol()
    createWindow()
    createMenu()
    createTray()

    registerIpc(ipcMain, () => mainWindow, store, dialog, shell, app)
    setupAutoUpdater(() => mainWindow)

    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) {
        createWindow()
      } else if (mainWindow) {
        mainWindow.show()
      }
    })
  })
}

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('before-quit', () => {
  isQuitting = true
})
