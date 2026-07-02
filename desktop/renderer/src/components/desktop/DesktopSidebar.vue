<template>
  <div
    class="desktop-sidebar"
    :class="{ 'sidebar-expanded': isExpanded }"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
  >
    <!-- 导航项 -->
    <nav class="sidebar-nav">
      <div
        v-for="item in navItems"
        :key="item.path"
        class="nav-item"
        :class="{ 'nav-item-active': isActive(item.path) }"
        @click="handleNavigate(item.path)"
      >
        <div class="nav-icon">
          <component :is="item.icon" :size="24" :color="NAV_ICON_COLOR" />
        </div>
        <span v-if="isExpanded" class="nav-label">{{ item.label }}</span>
      </div>
    </nav>

    <!-- 底部操作 -->
    <div class="sidebar-bottom">
      <div class="nav-item" @click="handleNavigate('/user')">
        <div class="nav-icon">
          <IconUser :size="24" :color="NAV_ICON_COLOR" />
        </div>
        <span v-if="isExpanded" class="nav-label">个人中心</span>
      </div>
      <div class="nav-item" @click="handleLogout">
        <div class="nav-icon">
          <IconLogout :size="24" :color="NAV_ICON_COLOR" />
        </div>
        <span v-if="isExpanded" class="nav-label">退出登录</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store'
import {
  IconHome,
  IconDocument,
  IconAI,
  IconMagic,
  IconTrend,
  IconTranslate,
  IconMindmap,
  IconKnowledgeGraph,
  IconUser,
  IconLogout
} from '@/components/icons'

const NAV_ICON_COLOR = 'var(--color-sidebar-icon)'

const router = useRouter()
const userStore = useUserStore()

const isExpanded = ref(false)

const navItems = [
  { path: '/home', label: '首页', icon: IconHome },
  { path: '/notes', label: '我的笔记', icon: IconDocument },
  { path: '/ai/assistant', label: 'AI 助手', icon: IconAI },
  { path: '/ai/generate', label: 'AI 生成', icon: IconMagic },
  { path: '/ai/summarize', label: 'AI 摘要', icon: IconTrend },
  { path: '/ai/translate', label: '翻译', icon: IconTranslate },
  { path: '/mindmap', label: '思维导图', icon: IconMindmap },
  { path: '/kg', label: '知识图谱', icon: IconKnowledgeGraph }
]

function isActive(path) {
  const currentPath = router.currentRoute.value.path
  if (path === '/notes') {
    return currentPath.startsWith('/notes')
  }
  return currentPath === path
}

function handleNavigate(path) {
  if (router.currentRoute.value.path === path) return
  router.push(path)
}

async function handleLogout() {
  await userStore.logout()
  await router.replace('/')
}

function handleMouseEnter() {
  isExpanded.value = true
}

function handleMouseLeave() {
  isExpanded.value = false
}
</script>

<style scoped>
.desktop-sidebar {
  width: 64px;
  height: calc(100vh - 36px);
  background: var(--color-sidebar-bg);
  border-right: 1px solid var(--color-sidebar-border);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 12px 8px;
  transition: width 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.05);
}

.sidebar-expanded {
  width: 200px;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-top: 8px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 10px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.15s ease;
  color: var(--color-sidebar-text);
  min-height: 44px;
  font-family: var(--font-body);
}

.nav-item:hover {
  background: var(--color-sidebar-hover);
  transform: translateX(2px);
  color: var(--color-sidebar-text-hover);
}

.nav-item-active {
  background: var(--color-sidebar-active-bg);
  color: var(--color-sidebar-active-text);
  font-weight: 700;
  box-shadow: var(--shadow-hard-sm);
  border: 1.5px solid var(--color-sidebar-active-border);
}

.nav-item-active:hover {
  background: var(--color-sidebar-active-bg);
  transform: translateX(2px);
}

.nav-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 28px;
  height: 28px;
}

.nav-label {
  font-family: var(--font-body);
  font-size: 15px;
  white-space: nowrap;
  opacity: 0;
  transition: opacity 0.2s ease 0.05s;
  font-weight: 500;
}

.sidebar-expanded .nav-label {
  opacity: 1;
}

.sidebar-bottom {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: auto;
  padding-top: 12px;
  border-top: 1px solid var(--color-sidebar-border);
  padding-bottom: 8px;
}

/* 响应系统主题 */
@media (prefers-color-scheme: dark) {
  .desktop-sidebar {
    box-shadow: 2px 0 12px rgba(0, 0, 0, 0.3);
  }
}
</style>