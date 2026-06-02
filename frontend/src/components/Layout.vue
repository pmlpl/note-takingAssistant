<template>
  <el-container>
    <!-- ═══ Hand-Drawn Header ═══ -->
    <el-header class="header">
      <div class="logo">
        <AppLogo :size="36" />
        <span class="title">智能笔记助手</span>
      </div>

      <el-menu :default-active="activeMenu" mode="horizontal" class="nav-menu">
        <el-menu-item index="/home" @click="navigate('/home')">
          <IconHome :size="20" :color="NAV_ICON_COLOR" />
          <span>首页</span>
        </el-menu-item>
        <el-menu-item index="/notes" @click="navigate('/notes')">
          <IconDocument :size="20" :color="NAV_ICON_COLOR" />
          <span>我的笔记</span>
        </el-menu-item>
        <el-menu-item index="/ai/generate" @click="navigate('/ai/generate')">
          <IconMagic :size="20" :color="NAV_ICON_COLOR" />
          <span>AI 生成</span>
        </el-menu-item>
        <el-menu-item index="/ai/summarize" @click="navigate('/ai/summarize')">
          <IconTrend :size="20" :color="NAV_ICON_COLOR" />
          <span>AI 总结</span>
        </el-menu-item>
        <el-menu-item index="/ai/translate" @click="navigate('/ai/translate')">
          <IconTranslate :size="20" :color="NAV_ICON_COLOR" />
          <span>翻译</span>
        </el-menu-item>
        <el-menu-item index="/mindmap" @click="navigate('/mindmap')">
          <IconMindmap :size="20" :color="NAV_ICON_COLOR" />
          <span>导图</span>
        </el-menu-item>
        <el-menu-item index="/manual" @click="navigate('/manual')">
          <IconNotebook :size="20" :color="NAV_ICON_COLOR" />
          <span>手册</span>
        </el-menu-item>
      </el-menu>

      <div class="user-info">
        <el-dropdown v-if="userStore.isLoggedIn">
          <span class="user-name">
            <IconUser :size="18" :color="NAV_ICON_COLOR" />
            {{ userStore.user.username }}
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="navigate('/user')">个人中心</el-dropdown-item>
              <el-dropdown-item @click="handleLogout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <div v-else class="auth-buttons">
          <el-button link @click="navigate('/login')">登录</el-button>
          <el-button type="primary" @click="navigate('/register')">注册</el-button>
        </div>
      </div>
    </el-header>

    <el-main class="main-content">
      <slot></slot>
    </el-main>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store'
import {AppLogo, IconHome, IconDocument, IconMagic, IconTrend, IconUser, IconMindmap, IconTranslate, IconNotebook} from '@/components/icons'

const NAV_ICON_COLOR = '#2d2d2d'

const router = useRouter()
const userStore = useUserStore()

const activeMenu = computed(() => router.currentRoute.value.path)

function navigate(path) {
  if (router.currentRoute.value.path === path) return
  router.push(path)
}

async function handleLogout() {
  await userStore.logout()
  await router.replace('/')
}
</script>

<style scoped>
/* ═══ Hand-Drawn Header: paper strip with thick dashed bottom ═══ */
.header {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: #ffffff;
  color: var(--color-pencil);
  border-bottom: 4px dashed var(--color-pencil);
  border-radius: var(--radius-wobbly-md) var(--radius-wobbly-md) 0 0;
  min-height: 60px;
}

/* Subtle tape strip across top */
.header::before {
  content: '';
  position: absolute;
  top: -8px;
  left: 50%;
  transform: translateX(-50%) rotate(-1.5deg);
  width: 120px;
  height: 22px;
  background: rgba(200, 200, 200, 0.35);
  border-radius: 2px;
  pointer-events: none;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.title {
  font-family: var(--font-heading);
  font-size: 22px;
  font-weight: 700;
  color: var(--color-pencil);
  letter-spacing: 1px;
}

/* ── Nav Menu ── */
.nav-menu {
  flex: 1;
  justify-content: center;
  background: transparent !important;
  border-bottom: none !important;
  box-shadow: none !important;
}

.nav-menu :deep(.el-menu-item) {
  color: #2d2d2d;
  font-family: var(--font-body);
  font-size: 16px;
  border-bottom: none !important;
  border-radius: var(--radius-wobbly-sm);
  margin: 0 2px;
}

.nav-menu :deep(.el-menu-item svg) {
  color: #2d2d2d;
}

.nav-menu :deep(.el-menu-item:hover) {
  background: var(--color-yellow) !important;
  transform: rotate(-1deg);
  transition: transform 0.15s ease;
}

.nav-menu :deep(.el-menu-item.is-active) {
  background: var(--color-muted) !important;
  font-weight: 700;
  transform: rotate(0.5deg);
}

/* ── User Info ── */
.user-info {
  display: flex;
  align-items: center;
  margin-left: 20px;
  gap: 10px;
}

.user-name {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  color: #2d2d2d;
  font-family: var(--font-body);
  font-size: 15px;
}

.user-name svg {
  color: #2d2d2d;
}

.auth-buttons {
  display: flex;
  gap: 10px;
}

/* ── Main Content ── */
.main-content {
  background: rgba(255, 255, 255, 0.7);
  padding: 0;
  overflow-x: hidden;
  overflow-y: visible;
  border-radius: 0 0 12px 12px;
}
</style>
