<template>
  <div class="title-bar" @mousedown="handleMouseDown">
    <!-- 左侧：应用图标 + 名称 -->
    <div class="title-bar-left">
      <AppLogo :size="24" />
      <span class="app-name">NoteMind</span>
    </div>

    <!-- 中间：可拖拽区域（已由父级 mousedown 处理） -->
    <div class="title-bar-center">
      <span class="window-title">{{ currentTitle }}</span>
    </div>

    <!-- 右侧：窗口控制按钮 -->
    <div class="title-bar-right">
      <button class="window-btn minimize-btn" @click.stop="handleMinimize" title="最小化">
        <svg width="12" height="12" viewBox="0 0 12 12">
          <rect x="1" y="5.5" width="10" height="1" fill="currentColor"/>
        </svg>
      </button>
      <button class="window-btn maximize-btn" @click.stop="handleToggleMaximize" :title="isMaximized ? '还原' : '最大化'">
        <svg v-if="isMaximized" width="12" height="12" viewBox="0 0 12 12">
          <rect x="2" y="2" width="8" height="8" fill="none" stroke="currentColor" stroke-width="1.5"/>
          <rect x="4" y="0" width="8" height="8" fill="none" stroke="currentColor" stroke-width="1.5" transform="translate(-2, 2)"/>
        </svg>
        <svg v-else width="12" height="12" viewBox="0 0 12 12">
          <rect x="1" y="1" width="10" height="10" fill="none" stroke="currentColor" stroke-width="1.5"/>
        </svg>
      </button>
      <button class="window-btn close-btn" @click.stop="handleClose" title="关闭">
        <svg width="12" height="12" viewBox="0 0 12 12">
          <line x1="1" y1="1" x2="11" y2="11" stroke="currentColor" stroke-width="1.5"/>
          <line x1="11" y1="1" x2="1" y2="11" stroke="currentColor" stroke-width="1.5"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { AppLogo } from '@/components/icons'

const route = useRoute()
const isMaximized = ref(false)
const currentTitle = ref('NoteMind - 智能笔记助手')

// 路由到标题的映射
const routeTitleMap = {
  '/home': '首页',
  '/notes': '我的笔记',
  '/notes/edit': '笔记编辑',
  '/notes/history': '历史笔记',
  '/ai/generate': 'AI 生成',
  '/ai/summarize': 'AI 摘要',
  '/ai/translate': '翻译',
  '/mindmap': '思维导图',
  '/kg': '知识图谱',
  '/manual': '使用手册',
  '/user': '个人中心',
  '/login': '登录',
  '/register': '注册'
}

// 根据路由更新标题
function updateTitle() {
  const path = route.path
  let pageName = routeTitleMap[path]

  // 处理动态路由
  if (path.startsWith('/notes/edit')) {
    pageName = '笔记编辑'
  }

  if (pageName) {
    currentTitle.value = `${pageName} - NoteMind`
  } else {
    currentTitle.value = 'NoteMind - 智能笔记助手'
  }

  // 同步更新系统窗口标题
  if (window.electronAPI?.window?.setTitle) {
    window.electronAPI.window.setTitle(currentTitle.value)
  }
}

// 检查窗口最大化状态
async function checkMaximized() {
  if (window.electronAPI?.window?.isMaximized) {
    const result = await window.electronAPI.window.isMaximized()
    isMaximized.value = result
  }
}

// 窗口控制
async function handleMinimize() {
  if (window.electronAPI?.window?.minimize) {
    await window.electronAPI.window.minimize()
  }
}

async function handleToggleMaximize() {
  if (window.electronAPI?.window?.toggleMaximize) {
    await window.electronAPI.window.toggleMaximize()
    await checkMaximized()
  }
}

async function handleClose() {
  if (window.electronAPI?.window?.close) {
    await window.electronAPI.window.close()
  }
}

// 标题栏拖拽
function handleMouseDown(e) {
  // 只在标题栏区域（不包括按钮）响应拖拽
  if (e.target.closest('.window-btn')) return

  // 双击切换最大化
  if (e.detail === 2) {
    handleToggleMaximize()
  }
}

onMounted(() => {
  updateTitle()
  checkMaximized()

  // 监听路由变化更新标题
  const unwatch = watch(
    () => route.path,
    updateTitle
  )

  // 监听窗口最大化状态变化
  window.addEventListener('resize', checkMaximized)

  onUnmounted(() => {
    if (unwatch) unwatch()
    window.removeEventListener('resize', checkMaximized)
  })
})
</script>

<style scoped>
.title-bar {
  position: relative;
  flex-shrink: 0;
  height: 36px;
  background: var(--color-sidebar-bg);
  border-bottom: 1px solid var(--color-sidebar-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  z-index: 10;
  user-select: none;
  -webkit-app-region: drag; /* Electron 拖拽区域标记 */
}

.title-bar-left {
  display: flex;
  align-items: center;
  gap: 8px;
  -webkit-app-region: no-drag; /* 左侧图标区域不参与拖拽 */
}

.app-name {
  font-family: var(--font-heading);
  font-size: 16px;
  font-weight: 700;
  color: var(--color-sidebar-text-hover);
  letter-spacing: 0.5px;
}

.title-bar-center {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.window-title {
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-sidebar-text);
  opacity: 0.8;
}

.title-bar-right {
  display: flex;
  align-items: center;
  gap: 8px;
  -webkit-app-region: no-drag; /* 右侧按钮区域不参与拖拽 */
}

.window-btn {
  width: 32px;
  height: 28px;
  border: none;
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.15s ease;
  color: var(--color-sidebar-icon);
}

.window-btn:hover {
  background: var(--color-sidebar-hover);
  color: var(--color-sidebar-text-hover);
}

.window-btn:active {
  background: rgba(0, 0, 0, 0.12);
  transform: scale(0.95);
}

.close-btn:hover {
  background: #ff4d4d;
  color: #ffffff;
}

.close-btn:active {
  background: #ff3333;
}

/* 深色模式通过 CSS 变量自动适配，无需额外覆盖 */

</style>