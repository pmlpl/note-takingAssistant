<template>
  <div id="app-container">
    <router-view v-slot="{ Component, route }">
      <transition :name="getTransitionName(route)" mode="out-in" appear>
        <keep-alive include="Home,AiGenerate,AiSummarize,NoteEdit,NoteList,HistoryNotes">
          <component :is="Component" class="page-wrapper" />
        </keep-alive>
      </transition>
    </router-view>
  </div>
</template>

<script setup>
function getTransitionName(route) {
  // 根据路由元信息决定过渡效果
  const transition = route.meta.transition || 'fade'
  return `page-${transition}`
}
</script>

<style>
/* @vue-use-transition-styles */

/* 应用容器 - 统一背景色，防止闪白 */
#app-container {
  min-height: 100vh;
  background: rgb(104 104 104 / 0.45);
  border-radius: 12px;
  overflow: hidden;
}

/* 页面包装器 - 确保背景色一致 */
.page-wrapper {
  min-height: 100vh;
  background: white;
  padding:0 2px;
}

/* 淡入淡出过渡 - 用于普通页面 */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.2s ease;
}

.page-fade-enter-from {
  opacity: 0;
}

.page-fade-leave-to {
  opacity: 0;
}

/* 滑动过渡 - 用于登录注册等认证页面 */
.page-slide-enter-active,
.page-slide-leave-active {
  transition: opacity 0.2s ease,
              transform 0.2s ease;
}

.page-slide-enter-from {
  opacity: 0;
  transform: translateX(4px);
}

.page-slide-leave-to {
  opacity: 0;
  transform: translateX(-4px);
}

/* 确保过渡期间不会出现滚动条闪烁 */
body {
  overflow-x: hidden;
  margin: 0;
}

/* 提升过渡性能 */
.page-fade-enter-active,
.page-fade-leave-active,
.page-slide-enter-active,
.page-slide-leave-active {
  will-change: opacity, transform;
  backface-visibility: hidden;
  perspective: 1000px;
}
</style>