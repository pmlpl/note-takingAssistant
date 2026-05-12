<template>
  <BaseIcon :size="size" :color="color" viewBox="0 0 64 64">
    <!-- 笔记本主体 -->
    <rect x="12" y="8" width="40" height="48" rx="3" fill="currentColor" opacity="0.9"/>
    
    <!-- 笔记本左侧装订线 -->
    <rect x="12" y="8" width="4" height="48" rx="2" fill="currentColor" opacity="0.6"/>
    
    <!-- 横线 - 模拟笔记纸张 -->
    <line x1="20" y1="18" x2="48" y2="18" stroke="white" stroke-width="1.5" opacity="0.8"/>
    <line x1="20" y1="24" x2="48" y2="24" stroke="white" stroke-width="1.5" opacity="0.8"/>
    <line x1="20" y1="30" x2="48" y2="30" stroke="white" stroke-width="1.5" opacity="0.8"/>
    <line x1="20" y1="36" x2="44" y2="36" stroke="white" stroke-width="1.5" opacity="0.8"/>
    
    <!-- AI 魔法元素 - 星星 -->
    <circle cx="46" cy="14" r="2" fill="white" opacity="0.9"/>
    <circle cx="50" cy="18" r="1.5" fill="white" opacity="0.7"/>
    <circle cx="44" cy="20" r="1" fill="white" opacity="0.6"/>
    
    <!-- AI 光晕效果 -->
    <circle cx="48" cy="16" r="4" fill="none" stroke="white" stroke-width="1" opacity="0.4"/>
  </BaseIcon>
</template>

<script setup>
import BaseIcon from './BaseIcon.vue'

defineProps({
  size: {
    type: [String, Number],
    default: 32
  },
  color: {
    type: String,
    default: '#409eff'
  }
})
</script>
