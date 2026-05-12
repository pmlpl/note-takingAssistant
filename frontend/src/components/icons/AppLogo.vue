<template>
  <BaseIcon :size="size" viewBox="0 0 100 100">
    <defs>
      <linearGradient id="appLogoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" style="stop-color:#667eea"/>
        <stop offset="100%" style="stop-color:#764ba2"/>
      </linearGradient>
    </defs>
    <!-- 圆角矩形背景 -->
    <rect width="100" height="100" rx="20" fill="url(#appLogoGradient)"/>
    <!-- AI 符号 - 类似闪电的形状 -->
    <path d="M30 70 L50 30 L70 70" stroke="white" stroke-width="8" fill="none" stroke-linecap="round"/>
    <!-- 中心圆点 -->
    <circle cx="50" cy="55" r="8" fill="white"/>
  </BaseIcon>
</template>

<script setup>
import BaseIcon from './BaseIcon.vue'

defineProps({
  size: {
    type: [String, Number],
    default: 32
  }
})
</script>

