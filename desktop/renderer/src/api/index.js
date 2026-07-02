import axios from 'axios'
import { useUserStore } from '@/store'
import router from '@/router'
import { DESKTOP_DEFAULT_API_BASE } from '@/config/desktop'

let resolvedBaseUrl = null

async function resolveBaseUrl() {
  if (resolvedBaseUrl !== null) return resolvedBaseUrl

  const isDesktop = typeof window !== 'undefined' && window.electronAPI?.isDesktop === true

  if (isDesktop) {
    resolvedBaseUrl = DESKTOP_DEFAULT_API_BASE
  } else {
    resolvedBaseUrl = '/api'
  }

  return resolvedBaseUrl
}

function getSyncBaseUrl() {
  if (resolvedBaseUrl !== null) return resolvedBaseUrl
  const isDesktop = typeof window !== 'undefined' && window.electronAPI?.isDesktop === true
  return isDesktop ? DESKTOP_DEFAULT_API_BASE : '/api'
}

function updateBaseUrl(url) {
  if (url) {
    resolvedBaseUrl = url.replace(/\/+$/, '')
    api.defaults.baseURL = resolvedBaseUrl
  }
}

function defaultRequestTimeoutMs() {
  const raw = import.meta.env.VITE_DEFAULT_REQUEST_TIMEOUT_MS
  if (raw === '' || raw === undefined) {
    return 180_000
  }
  const n = Number(raw)
  return Number.isNaN(n) ? 180_000 : n
}

const api = axios.create({
  baseURL: getSyncBaseUrl(),
  timeout: defaultRequestTimeoutMs()
})

let baseUrlResolved = false
const baseUrlPromise = resolveBaseUrl().then(url => {
  if (url && url !== api.defaults.baseURL) {
    api.defaults.baseURL = url
  }
  baseUrlResolved = true
})

api.interceptors.request.use(
  async (config) => {
    if (!baseUrlResolved) {
      await baseUrlPromise
      if (api.defaults.baseURL && !config.baseURL) {
        config.baseURL = api.defaults.baseURL
      }
    }
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    if (error.response?.status === 401) {
      const isLogoutRequest = error.config?.url?.includes('/user/logout')
      if (isLogoutRequest) {
        return Promise.reject(error)
      }

      const userStore = useUserStore()

      if (userStore.token) {
        console.warn('Token 失效，自动登出')

        import('element-plus').then(({ ElMessage }) => {
          ElMessage.warning('登录已过期，请重新登录')
        })

        void userStore.logout().then(() => {
          if (router.currentRoute.value.path !== '/') {
            router.replace({ path: '/' })
          }
        })
      }
    }
    return Promise.reject(error)
  }
)

export { updateBaseUrl, resolveBaseUrl, DESKTOP_DEFAULT_API_BASE }

export function getApiBaseUrl() {
  return api.defaults.baseURL || getSyncBaseUrl()
}

export default api
