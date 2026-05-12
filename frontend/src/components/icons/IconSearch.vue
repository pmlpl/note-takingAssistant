<template>
  <BaseIcon :size="size" :color="color">
    <!-- 放大镜圆形 -->
    <circle cx="10" cy="10" r="7" 
      fill="none" 
      stroke="currentColor" 
      stroke-width="2"/>
    
    <!-- 放大镜手柄 -->
    <line x1="15" y1="15" x2="20" y2="20" 
      stroke="currentColor" 
      stroke-width="2.5" 
      stroke-linecap="round"/>
    
    <!-- 镜片高光 -->
    <path d="M8 7C8 7 9 6 11 6" 
      stroke="white" 
      stroke-width="1" 
      stroke-linecap="round" 
      opacity="0.4"/>
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
