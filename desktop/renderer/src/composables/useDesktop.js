import { ref } from 'vue'

const isDesktop = ref(typeof window !== 'undefined' && window.electronAPI?.isDesktop === true)

export function useDesktop() {
  function openExternal(url) {
    if (isDesktop.value && window.electronAPI?.app?.openExternal) {
      return window.electronAPI.app.openExternal(url)
    }
    window.open(url, '_blank')
  }

  async function showOpenDialog(options) {
    if (isDesktop.value && window.electronAPI?.dialog?.showOpenDialog) {
      return window.electronAPI.dialog.showOpenDialog(options)
    }
    return { canceled: true, filePaths: [] }
  }

  async function showSaveDialog(options) {
    if (isDesktop.value && window.electronAPI?.dialog?.showSaveDialog) {
      return window.electronAPI.dialog.showSaveDialog(options)
    }
    return { canceled: true, filePath: null }
  }

  async function readFile(filePath, encoding) {
    if (isDesktop.value && window.electronAPI?.fs?.readFile) {
      return window.electronAPI.fs.readFile(filePath, encoding)
    }
    return { success: false, error: 'not available' }
  }

  async function writeFile(filePath, content, encoding) {
    if (isDesktop.value && window.electronAPI?.fs?.writeFile) {
      return window.electronAPI.fs.writeFile(filePath, content, encoding)
    }
    return { success: false, error: 'not available' }
  }

  async function storeGet(key, defaultValue) {
    if (isDesktop.value && window.electronAPI?.store?.get) {
      return window.electronAPI.store.get(key, defaultValue)
    }
    return { success: true, data: defaultValue }
  }

  async function storeSet(key, value) {
    if (isDesktop.value && window.electronAPI?.store?.set) {
      return window.electronAPI.store.set(key, value)
    }
    return { success: false, error: 'not available' }
  }

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

  function onMenuEvent(channel, callback) {
    if (isDesktop.value && window.electronAPI?.on) {
      return window.electronAPI.on(channel, callback)
    }
    return () => {}
  }

  async function windowMinimize() {
    if (isDesktop.value && window.electronAPI?.window?.minimize) {
      return window.electronAPI.window.minimize()
    }
    return { success: false, error: 'not available' }
  }

  async function windowMaximize() {
    if (isDesktop.value && window.electronAPI?.window?.maximize) {
      return window.electronAPI.window.maximize()
    }
    return { success: false, error: 'not available' }
  }

  async function windowToggleMaximize() {
    if (isDesktop.value && window.electronAPI?.window?.toggleMaximize) {
      return window.electronAPI.window.toggleMaximize()
    }
    return { success: false, error: 'not available' }
  }

  async function windowClose() {
    if (isDesktop.value && window.electronAPI?.window?.close) {
      return window.electronAPI.window.close()
    }
    return { success: false, error: 'not available' }
  }

  async function windowIsMaximized() {
    if (isDesktop.value && window.electronAPI?.window?.isMaximized) {
      return window.electronAPI.window.isMaximized()
    }
    return false
  }

  return {
    isDesktop,
    platform: isDesktop.value ? window.electronAPI?.platform : 'web',
    openExternal,
    showOpenDialog,
    showSaveDialog,
    showOpenDirectory,
    readFile,
    writeFile,
    storeGet,
    storeSet,
    onMenuEvent,
    showNotification,
    getAutoLaunch,
    setAutoLaunch,
    windowMinimize,
    windowMaximize,
    windowToggleMaximize,
    windowClose,
    windowIsMaximized
  }
}
