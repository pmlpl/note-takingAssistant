import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/store'

const routes = [
  {
    path: '/',
    name: 'Welcome',
    component: () => import('@/views/auth/Welcome.vue'),
    meta: { transition: 'slide', guestLanding: true }
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
    path: '/ai/translate',
    name: 'NoteTranslate',
    component: () => import('@/views/ai/NoteTranslate.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/mindmap',
    name: 'Mindmap',
    component: () => import('@/views/mindmap/Mindmap.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/kg',
    name: 'KnowledgeGraph',
    component: () => import('@/views/kg/KnowledgeGraph.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/knowledge-graph',
    redirect: '/kg'
  },
  {
    path: '/manual',
    name: 'UserManual',
    component: () => import('@/views/help/UserManual.vue'),
    meta: { requiresAuth: false, transition: 'fade' }
  },
  {
    path: '/user',
    name: 'UserCenter',
    component: () => import('@/views/user/UserCenter.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/oauth-callback',
    name: 'OAuthCallback',
    component: () => import('@/views/auth/OAuthCallback.vue'),
    meta: { transition: 'fade' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  try {
    const userStore = useUserStore()

    if (to.path === '/') {
      if (userStore.isLoggedIn) {
        next('/home')
      } else {
        next()
      }
      return
    }

    if (userStore.isLoggedIn && (to.path === '/login' || to.path === '/register')) {
      next('/home')
      return
    }

    if (to.meta.requiresAuth && !userStore.isLoggedIn) {
      next('/')
      return
    }

    next()
  } catch (error) {
    console.error('Route guard error:', error)
    next('/')
  }
})

export default router