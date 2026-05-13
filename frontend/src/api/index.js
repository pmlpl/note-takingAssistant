import axios from 'axios'
import { useUserStore } from '@/store'

/** 普通接口默认超时（毫秒）；AI 等长请求在各自 api 模块里单独覆盖 */
const DEFAULT_REQUEST_TIMEOUT_MS = 30_000

const api = axios.create({
  baseURL: '/api',
  timeout: DEFAULT_REQUEST_TIMEOUT_MS
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
      const userStore = useUserStore()
      
      // 检查是否已经登录（有 token）
      if (userStore.token) {
        // token 失效，清除登录状态
        console.warn('Token 失效，自动登出')
        
        // 显示友好提示
        import('element-plus').then(({ ElMessage }) => {
          ElMessage.warning('登录已过期，请重新登录')
        })
        
        userStore.logout()
        
        // 只在当前不在登录页时才重定向
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
      }
      // 如果没有 token，说明用户本来就没登录，不需要处理
    }
    return Promise.reject(error)
  }
)

export default api