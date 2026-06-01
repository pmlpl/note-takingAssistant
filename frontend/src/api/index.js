import axios from 'axios'
import { useUserStore } from '@/store'
import router from '@/router'

/**
 * 普通接口默认超时（毫秒）。
 * 本地 LM Studio 在弱机器上首包可能远超 30s；默认 3 分钟。
 * 环境变量 VITE_DEFAULT_REQUEST_TIMEOUT_MS 设为 0 表示不限制（与旧版一致）。
 */
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
    // 只有在访问受保护资源时才处理 401
    if (error.response?.status === 401) {
      // 排除 logout 接口本身，防止死循环
      const isLogoutRequest = error.config?.url?.includes('/user/logout')
      if (isLogoutRequest) {
        return Promise.reject(error)
      }

      const userStore = useUserStore()

      // 检查是否已经登录（有 token）
      if (userStore.token) {
        // token 失效，清除登录状态
        console.warn('Token 失效，自动登出')

        // 显示友好提示
        import('element-plus').then(({ ElMessage }) => {
          ElMessage.warning('登录已过期，请重新登录')
        })

        void userStore.logout().then(() => {
          if (router.currentRoute.value.path !== '/') {
            router.replace({ path: '/' })
          }
        })
      }
      // 如果没有 token，说明用户本来就没登录，不需要处理
    }
    return Promise.reject(error)
  }
)

export default api
