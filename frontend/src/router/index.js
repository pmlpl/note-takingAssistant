import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/store'

const routes = [
  {
    path: '/',
    name: 'Welcome',
    component: () => import('@/views/auth/Welcome.vue'),
    meta: { transition: 'slide' }
  },
  {
    path: '/home',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { requiresAuth: true, transition: 'fade' }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: { transition: 'slide' }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/Register.vue'),
    meta: { transition: 'slide' }
  },
  {
    path: '/notes',
    name: 'NoteList',
    component: () => import('@/views/notes/NoteList.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/notes/edit/:id?',
    name: 'NoteEdit',
    component: () => import('@/views/notes/NoteEdit.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/notes/history',
    name: 'HistoryNotes',
    component: () => import('@/views/notes/HistoryNotes.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/ai/generate',
    name: 'AiGenerate',
    component: () => import('@/views/ai/AiGenerate.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/ai/summarize',
    name: 'AiSummarize',
    component: () => import('@/views/ai/AiSummarize.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/mindmap',
    name: 'Mindmap',
    component: () => import('@/views/mindmap/Mindmap.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/user',
    name: 'UserCenter',
    component: () => import('@/views/user/UserCenter.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  try {
    const userStore = useUserStore()
    
    // 如果访问根路径，根据登录状态决定跳转
    if (to.path === '/') {
      if (userStore.isLoggedIn) {
        // 已登录，跳转到首页
        next('/home')
      } else {
        // 未登录，显示欢迎页
        next()
      }
      return
    }
    
    // 如果已登录但访问登录/注册页，跳转到首页
    if (userStore.isLoggedIn && (to.path === '/login' || to.path === '/register')) {
      next('/home')
      return
    }
    
    // 如果需要认证但未登录，跳转到登录页
    if (to.meta.requiresAuth && !userStore.isLoggedIn) {
      next('/login')
    } else {
      next()
    }
  } catch (error) {
    console.error('Route guard error:', error)
    // 发生错误时重定向到登录页
    next('/login')
  }
})

export default router