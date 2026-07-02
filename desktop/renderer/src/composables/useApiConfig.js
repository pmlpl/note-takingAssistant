import { ref } from 'vue'
import { DESKTOP_STORAGE_KEY, DESKTOP_DEFAULT_API_BASE } from '@/config/desktop'

const apiBaseUrl = ref('')
let initialized = false

async function initApiBase() {
  if (initialized) return
  initialized = true

  if (typeof window === 'undefined') return

  if (window.electronAPI?.store?.get) {
    const result = await window.electronAPI.store.get(DESKTOP_STORAGE_KEY, DESKTOP_DEFAULT_API_BASE)
    apiBaseUrl.value = (result?.data) || DESKTOP_DEFAULT_API_BASE
  } else {
    const envBase = import.meta.env.VITE_API_BASE_URL
    apiBaseUrl.value = envBase || ''
  }
}

async function setApiBase(url) {
  if (!url) return
  const cleanUrl = url.replace(/\/+$/, '')
  apiBaseUrl.value = cleanUrl

  if (window.electronAPI?.store?.set) {
    await window.electronAPI.store.set(DESKTOP_STORAGE_KEY, cleanUrl)
  }
}

function isDesktop() {
  return typeof window !== 'undefined' && window.electronAPI?.isDesktop === true
}

export function useApiConfig() {
  if (!initialized) {
    void initApiBase()
  }

  return {
    apiBaseUrl,
    setApiBase,
    isDesktop,
    defaultApiBase: DESKTOP_DEFAULT_API_BASE,
    initApiBase
  }
}
