<template>
  <div id="app-container">
    <!-- 独立布局页面（如笔记编辑页，自己有完整布局） -->
    <div v-if="useStandaloneLayout" class="standalone-layout-wrapper">
      <TitleBar />
      <router-view v-slot="{ Component, route: childRoute }">
        <transition name="page-content-fade">
          <component :is="Component" :key="childRoute.name" class="standalone-page" />
        </transition>
      </router-view>
    </div>

    <!-- 登录后页面：桌面端布局 -->
    <DesktopLayout v-else-if="useMainLayout">
      <router-view v-slot="{ Component, route: childRoute }">
        <transition name="page-content-fade">
          <keep-alive :include="KEEP_ALIVE_PAGES">
            <component :is="Component" :key="childRoute.name" class="desktop-page-wrapper" />
          </keep-alive>
        </transition>
      </router-view>
    </DesktopLayout>

    <!-- 登录/注册页 -->
    <div v-if="!useMainLayout && !useStandaloneLayout" class="guest-page-wrapper">
      <TitleBar />
      <router-view v-slot="{ Component, route: childRoute }">
        <transition :name="getTransitionName(childRoute)" mode="out-in" appear>
          <component
            :is="Component"
            :key="childRoute.path"
            :class="['page-wrapper', 'page-wrapper--desktop-guest']"
          />
        </transition>
      </router-view>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import DesktopLayout from '@/layouts/DesktopLayout.vue'
import TitleBar from '@/components/desktop/TitleBar.vue'
import { useDesktop } from '@/composables/useDesktop'

const route = useRoute()
const router = useRouter()
const { onMenuEvent } = useDesktop()

const menuCleanupFns = ref([])

/** 与 keep-alive 的 include 一致（组件 name） */
const KEEP_ALIVE_PAGES =
  'HomeDesktop,AiGenerate,AiSummarize,NoteEditDesktop,NoteList,HistoryNotes,NoteTranslate,UserManual,Mindmap,UserCenter,AiAssistant'

const useMainLayout = computed(() => Boolean(route.meta.requiresAuth))
const useStandaloneLayout = computed(() => Boolean(route.meta.standaloneLayout))

function getTransitionName(childRoute) {
  const transition = childRoute.meta.transition || 'fade'
  return `page-${transition}`
}

/** 空闲时预加载常用页面 chunk，减轻首次点击等待 */
function prefetchMainRoutes() {
  const names = [
    'Home',
    'NoteList',
    'AiGenerate',
    'AiSummarize',
    'NoteTranslate',
    'Mindmap',
    'UserManual'
  ]
  for (const name of names) {
    try {
      const resolved = router.resolve({ name })
      const record = resolved.matched[resolved.matched.length - 1]
      const loader = record?.components?.default
      if (typeof loader === 'function') {
        loader()
      }
    } catch {
      /* ignore */
    }
  }
}

onMounted(() => {
  if (typeof requestIdleCallback === 'function') {
    requestIdleCallback(() => prefetchMainRoutes(), { timeout: 4000 })
  } else {
    setTimeout(prefetchMainRoutes, 1500)
  }

  const unbindNavigate = onMenuEvent('menu:navigate', (path) => {
    router.push(path)
  })
  const unbindNewNote = onMenuEvent('menu:new-note', () => {
    router.push('/notes/new')
  })
  const unbindSearch = onMenuEvent('menu:search', () => {
    ElMessage.info('搜索功能开发中...')
  })
  const unbindImport = onMenuEvent('menu:import-note', () => {
    if (route.name === 'NoteEdit' || route.name === 'NoteList') {
      window.dispatchEvent(new CustomEvent('desktop:import-note'))
    } else {
      router.push('/notes').then(() => {
        setTimeout(() => window.dispatchEvent(new CustomEvent('desktop:import-note')), 300)
      })
    }
  })
  const unbindExport = onMenuEvent('menu:export-note', () => {
    if (route.name === 'NoteEdit') {
      window.dispatchEvent(new CustomEvent('desktop:export-note'))
    } else {
      ElMessage.info('请先打开一篇笔记再导出')
    }
  })
  menuCleanupFns.value = [unbindNavigate, unbindNewNote, unbindSearch, unbindImport, unbindExport]
})

onUnmounted(() => {
  menuCleanupFns.value.forEach(fn => fn())
})
</script>

<style>
/* ═══════════════════════════════════════════
   App Container — Hand-Drawn Paper Theme
   ═══════════════════════════════════════════ */

#app-container {
  width: 100vw;
  height: 100vh;
  background: var(--color-paper);
  background-image: radial-gradient(var(--color-muted) 1px, transparent 1px);
  background-size: 24px 24px;
  overflow: hidden;
}

/* Guest page wrapper */
.guest-page-wrapper {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Standalone layout wrapper (for pages with their own layout) */
.standalone-layout-wrapper {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.standalone-page {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

/* Page wrapper — torn paper edge feel */
.page-wrapper {
  min-height: 100vh;
  background: var(--color-content-bg);
  padding: 0 2px;
  border-left: 3px dashed var(--color-muted);
  border-right: 3px dashed var(--color-muted);
}

.page-wrapper--app {
  min-height: calc(100vh - 60px);
}

/* 桌面端guest页面：占满高度，有滚动条时在内部滚动 */
.page-wrapper--desktop-guest {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
}

/* 欢迎页：去掉两侧虚线框，与全宽 Hero 连成一体 */
.page-wrapper--landing {
  min-height: 100vh;
  background: transparent;
  padding: 0;
  border: none;
}

/* 主内容区：短淡入，不与 out-in 叠加等待 */
.page-content-fade-enter-active {
  transition: opacity 0.12s ease;
}
.page-content-fade-enter-from {
  opacity: 0.6;
}
.page-content-fade-leave-active {
  transition: none;
}

/* ── Guest Page Transitions ── */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.2s ease;
}
.page-fade-enter-from,
.page-fade-leave-to {
  opacity: 0;
}

.page-slide-enter-active,
.page-slide-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.page-slide-enter-from {
  opacity: 0;
  transform: translateX(4px);
}
.page-slide-leave-to {
  opacity: 0;
  transform: translateX(-4px);
}

body {
  overflow-x: hidden;
  margin: 0;
}

.page-fade-enter-active,
.page-fade-leave-active,
.page-slide-enter-active,
.page-slide-leave-active {
  will-change: opacity, transform;
  backface-visibility: hidden;
}
</style>
