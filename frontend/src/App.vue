<template>
  <div id="app-container">
  <!-- 已登录业务页：导航栏常驻，只切换主内容区 -->
    <Layout v-if="useMainLayout">
      <router-view v-slot="{ Component, route: childRoute }">
        <transition name="page-content-fade">
          <keep-alive :include="KEEP_ALIVE_PAGES">
            <component :is="Component" :key="childRoute.name" class="page-wrapper page-wrapper--app" />
          </keep-alive>
        </transition>
      </router-view>
    </Layout>

    <!-- 欢迎页 / 登录 / 注册 -->
    <router-view v-else v-slot="{ Component, route: childRoute }">
      <transition :name="getTransitionName(childRoute)" mode="out-in" appear>
        <component
          :is="Component"
          :key="childRoute.path"
          :class="['page-wrapper', { 'page-wrapper--landing': childRoute.meta.guestLanding }]"
        />
      </transition>
    </router-view>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Layout from '@/components/Layout.vue'

const route = useRoute()
const router = useRouter()

/** 与 keep-alive 的 include 一致（组件 name） */
const KEEP_ALIVE_PAGES =
  'Home,AiGenerate,AiSummarize,NoteEdit,NoteList,HistoryNotes,NoteTranslate,UserManual,Mindmap,UserCenter'

const useMainLayout = computed(() => Boolean(route.meta.requiresAuth))

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
})
</script>

<style>
/* ═══════════════════════════════════════════
   App Container — Hand-Drawn Paper Theme
   ═══════════════════════════════════════════ */

#app-container {
  min-height: 100vh;
  background: var(--color-paper);

  /* Notebook dot grid */
  background-image: radial-gradient(var(--color-muted) 1px, transparent 1px);
  background-size: 24px 24px;

  overflow-x: hidden;
  overflow-y: visible;
}

/* Page wrapper — torn paper edge feel */
.page-wrapper {
  min-height: 100vh;
  background: rgba(255, 255, 255, 0.85);
  padding: 0 2px;
  border-left: 3px dashed var(--color-muted);
  border-right: 3px dashed var(--color-muted);
}

.page-wrapper--app {
  min-height: calc(100vh - 60px);
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
