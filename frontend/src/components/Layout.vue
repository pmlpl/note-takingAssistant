<template>
  <el-container>
    <el-header class="header">
      <div class="logo">
        <AppLogo :size="32" color="#409eff" />
        <span class="title">AI笔记助手</span>
      </div>
      <el-menu :default-active="activeMenu" mode="horizontal" class="nav-menu">
        <el-menu-item index="/home" @click="navigate('/home')">
          <IconHome :size="20" />
          <span>首页</span>
        </el-menu-item>
        <el-menu-item index="/notes" @click="navigate('/notes')">
          <IconDocument :size="20" />
          <span>我的笔记</span>
        </el-menu-item>
        <el-menu-item index="/ai/generate" @click="navigate('/ai/generate')">
          <IconMagic :size="20" />
          <span>AI生成</span>
        </el-menu-item>
        <el-menu-item index="/ai/summarize" @click="navigate('/ai/summarize')">
          <IconTrend :size="20" />
          <span>AI总结</span>
        </el-menu-item>
        <el-menu-item index="/mindmap" @click="navigate('/mindmap')">
          <IconMindmap :size="20"/>
          <span>思维导图</span>
        </el-menu-item>
      </el-menu>
      <div class="user-info">
        <el-dropdown v-if="userStore.isLoggedIn">
          <span class="user-name">
            <IconUser :size="18" />
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
import {AppLogo, IconHome, IconDocument, IconMagic, IconTrend, IconUser, IconAI, IconMindmap} from '@/components/icons'

const router = useRouter()
const userStore = useUserStore()

const activeMenu = computed(() => router.currentRoute.value.path)

function navigate(path) {
  router.push(path)
}

function handleLogout() {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background: linear-gradient(135deg, #353c3c 0%, #9eb8ef 100%);
  color: white;
  border-radius: 12px 12px 0 0;
}

.logo {
  display: flex;
  margin: 0 47px 0 30px;
  gap: 10px;
}

.title {
  font-size: 20px;
  font-weight: bold;
}

.nav-menu {
  flex: 1;
  justify-content: center;
}

.nav-menu :deep(.el-menu-item) {
  color: #aaaaaa;
}

.nav-menu :deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.1);
}

.nav-menu :deep(.el-menu-item.is-active) {
  background: rgba(255, 255, 255, 0.2);
}

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
  color: #405305;
}

.auth-buttons {
  display: flex;
  gap: 10px;
}

.main-content {
  background: white;
  padding: 0;
  overflow: hidden;
  border-radius: 0 0 12px 12px;
}
</style>