import axios from 'axios'
import { useUserStore } from '@/store'
import router from '@/router'

function defaultRequestTimeoutMs() {
  const raw = import.meta.env.VITE_DEFAULT_REQUEST_TIMEOUT_MS
  if (raw === '' || raw === undefined) {
    return 180_000
  }
  const n = Number(raw)
  return Number.isNaN(n) ? 180_000 : n
}

const api = axios.create({
  baseURL: '/api',
  timeout: defaultRequestTimeoutMs()
})

api.interceptors.request.use(
  (config) => {
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

export default api
