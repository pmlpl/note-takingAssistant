<template>
  <div id="app-container">
    <router-view v-slot="{ Component, route }">
      <transition :name="getTransitionName(route)" mode="out-in" appear>
        <keep-alive include="Home,AiGenerate,AiSummarize,NoteEdit,NoteList,HistoryNotes,NoteTranslate,UserManual">
          <component
            :is="Component"
            :class="['page-wrapper', { 'page-wrapper--landing': route.meta.guestLanding }]"
          />
        </keep-alive>
      </transition>
    </router-view>
  </div>
</template>

<script setup>
function getTransitionName(route) {
  const transition = route.meta.transition || 'fade'
  return `page-${transition}`
}
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
  backdrop-filter: blur(2px);
  padding: 0 2px;
  border-left:  3px dashed var(--color-muted);
  border-right: 3px dashed var(--color-muted);
}

/* 欢迎页：去掉两侧虚线框，与全宽 Hero 连成一体 */
.page-wrapper--landing {
  min-height: 100vh;
  background: transparent;
  backdrop-filter: none;
  padding: 0;
  border: none;
}

/* ── Page Transitions ── */
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

/* Performance hints */
.page-fade-enter-active,
.page-fade-leave-active,
.page-slide-enter-active,
.page-slide-leave-active {
  will-change: opacity, transform;
  backface-visibility: hidden;
}
</style>
