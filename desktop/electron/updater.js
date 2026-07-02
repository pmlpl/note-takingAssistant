function setupAutoUpdater(getMainWindow) {
  try {
    const { autoUpdater } = require('electron-updater')
    const { dialog } = require('electron')

    autoUpdater.autoDownload = false
    autoUpdater.autoInstallOnAppQuit = true

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

    setTimeout(() => {
      autoUpdater.checkForUpdates().catch(() => {})
    }, 5000)
  } catch (err) {
    console.warn('Auto updater not available:', err.message)
  }
}

module.exports = { setupAutoUpdater }

