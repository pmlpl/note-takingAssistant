<template>
  <BaseIcon :size="size" :color="color">
    <!-- 坐标轴 -->
    <line x1="4" y1="20" x2="20" y2="20" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
    <line x1="4" y1="20" x2="4" y2="6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
    
    <!-- 上升折线 -->
    <polyline 
      points="6,16 9,13 12,14 15,9 18,7" 
      fill="none" 
      stroke="currentColor" 
      stroke-width="2" 
      stroke-linecap="round" 
      stroke-linejoin="round"
    />
    
    <!-- 数据点 -->
    <circle cx="6" cy="16" r="1.5" fill="white" opacity="0.8" />
    <circle cx="9" cy="13" r="1.5" fill="white" opacity="0.8" />
    <circle cx="12" cy="14" r="1.5" fill="white" opacity="0.8" />
    <circle cx="15" cy="9" r="1.5" fill="white" opacity="0.8" />
    <circle cx="18" cy="7" r="1.5" fill="white" opacity="0.8" />
    
    <!-- 箭头指示上升趋势 -->
    <path d="M17 7L19 5M19 5L18.5 7.5M19 5L16.5 5.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
  </BaseIcon>
</template>

<script setup>
import BaseIcon from './BaseIcon.vue'

defineProps({
  size: {
    type: [String, Number],
    default: 24
  },
  color: {
    type: String,
    default: 'currentColor'
  }
})
</script>
