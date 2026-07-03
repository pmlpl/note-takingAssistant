const { contextBridge, ipcRenderer } = require('electron')

const VALID_CHANNELS = [
  'menu:new-note',
  'menu:import-note',
  'menu:export-note',
  'menu:navigate',
  'menu:search'
]

contextBridge.exposeInMainWorld('electronAPI', {
  get platform() { return process.platform },
  isDesktop: true,

  app: {
    getVersion: () => ipcRenderer.invoke('app:get-version'),
    getPath: (name) => ipcRenderer.invoke('app:get-path', name),
    openExternal: (url) => {
      try {
        const parsed = new URL(url)
        if (!['http:', 'https:', 'mailto:'].includes(parsed.protocol)) {
          return Promise.resolve(false)
        }
      } catch { return Promise.resolve(false) }
      return ipcRenderer.invoke('app:open-external', url)
    }
  },

  window: {
    minimize: () => ipcRenderer.invoke('window:minimize'),
    maximize: () => ipcRenderer.invoke('window:maximize'),
    unmaximize: () => ipcRenderer.invoke('window:unmaximize'),
    toggleMaximize: () => ipcRenderer.invoke('window:toggle-maximize'),
    close: () => ipcRenderer.invoke('window:close'),
    isMaximized: () => ipcRenderer.invoke('window:is-maximized'),
    setTitle: (title) => ipcRenderer.invoke('window:set-title', title)
  },

  dialog: {
    showOpenDialog: (options) => ipcRenderer.invoke('dialog:show-open', options),
    showSaveDialog: (options) => ipcRenderer.invoke('dialog:show-save', options),
    showMessageBox: (options) => ipcRenderer.invoke('dialog:show-message', options)
  },

  fs: {
    readFile: (filePath, encoding) => ipcRenderer.invoke('fs:read-file', filePath, encoding),
    writeFile: (filePath, content, encoding) => ipcRenderer.invoke('fs:write-file', filePath, content, encoding),
    readDir: (dirPath) => ipcRenderer.invoke('fs:read-dir', dirPath),
    stat: (filePath) => ipcRenderer.invoke('fs:stat', filePath),
    exists: (filePath) => ipcRenderer.invoke('fs:exists', filePath)
  },

  store: {
    get: async (key, defaultValue) => {
      if (!['local_llm_settings', 'desktop_api_base_url', 'close_behavior'].includes(key)) {
        console.warn(`[preload] store.get blocked: key "${key}" not allowed`)
        return defaultValue
      }
      const result = await ipcRenderer.invoke('store:get', key, defaultValue)
      return result.success ? result.data : defaultValue
    },
    set: async (key, value) => {
      if (!['local_llm_settings', 'desktop_api_base_url', 'close_behavior'].includes(key)) {
        console.warn(`[preload] store.set blocked: key "${key}" not allowed`)
        return
      }
      const result = await ipcRenderer.invoke('store:set', key, value)
      return result.success
    },
    delete: async (key) => {
      if (!['local_llm_settings', 'desktop_api_base_url', 'close_behavior'].includes(key)) {
        console.warn(`[preload] store.delete blocked: key "${key}" not allowed`)
        return
      }
      const result = await ipcRenderer.invoke('store:delete', key)
      return result.success
    },
    clear: () => {
      console.warn('[preload] store.clear blocked: not allowed')
      return Promise.resolve()
    }
  },

  shell: {
    openPath: (path) => ipcRenderer.invoke('shell:open-path', path),
    showItemInFolder: (path) => ipcRenderer.invoke('shell:show-item-in-folder', path)
  },

  clipboard: {
    writeText: (text) => ipcRenderer.invoke('clipboard:write-text', text),
    readText: () => ipcRenderer.invoke('clipboard:read-text')
  },

  notification: {
    show: (title, body) => ipcRenderer.invoke('notification:show', title, body)
  },

  autoLaunch: {
    isEnabled: () => ipcRenderer.invoke('auto-launch:is-enabled'),
    setEnabled: (enabled) => ipcRenderer.invoke('auto-launch:set-enabled', enabled)
  },

  oauth: {
    startGithub: (authorizeUrl) =>
      ipcRenderer.invoke('oauth:start-github', authorizeUrl)
  },

  on: (channel, callback) => {
    if (VALID_CHANNELS.includes(channel)) {
      const subscription = (_event, ...args) => callback(...args)
      ipcRenderer.on(channel, subscription)
      return () => ipcRenderer.removeListener(channel, subscription)
    }
    console.warn(`[preload] Ignored unknown channel: "${channel}"`)
    return () => {}
  },

  once: (channel, callback) => {
    if (VALID_CHANNELS.includes(channel)) {
      ipcRenderer.once(channel, (_event, ...args) => callback(...args))
    } else {
      console.warn(`[preload] Ignored unknown channel: "${channel}"`)
    }
  }
})
