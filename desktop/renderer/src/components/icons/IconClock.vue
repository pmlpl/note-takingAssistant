<template>
  <BaseIcon :size="size" :color="color">
    <!-- 时钟外圆 -->
    <circle cx="12" cy="12" r="10" 
      fill="none" 
      stroke="currentColor" 
      stroke-width="2"/>
    
    <!-- 时针 -->
    <line x1="12" y1="12" x2="12" y2="7" 
      stroke="currentColor" 
      stroke-width="2.5" 
      stroke-linecap="round"/>
    
    <!-- 分针 -->
    <line x1="12" y1="12" x2="16" y2="12" 
      stroke="currentColor" 
      stroke-width="2" 
      stroke-linecap="round"/>
    
    <!-- 中心点 -->
    <circle cx="12" cy="12" r="1" fill="currentColor"/>
    
    <!-- 刻度标记 -->
    <line x1="12" y1="3" x2="12" y2="4" stroke="currentColor" stroke-width="1.5" opacity="0.5"/>
    <line x1="12" y1="20" x2="12" y2="21" stroke="currentColor" stroke-width="1.5" opacity="0.5"/>
    <line x1="3" y1="12" x2="4" y2="12" stroke="currentColor" stroke-width="1.5" opacity="0.5"/>
    <line x1="20" y1="12" x2="21" y2="12" stroke="currentColor" stroke-width="1.5" opacity="0.5"/>
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
