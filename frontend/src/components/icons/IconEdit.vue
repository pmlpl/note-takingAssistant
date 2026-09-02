<template>
  <BaseIcon :size="size" :color="color">
    <!-- 铅笔主体 -->
    <path
      d="M14.5 3.5L18.5 7.5L7 19H3V15L14.5 3.5Z" 
      fill="currentColor" 
      stroke="currentColor" 
      stroke-width="1.5" 
      stroke-linejoin="round"
    />
    
    <!-- 铅笔尖 -->
    <path d="M14.5 3.5L18.5 7.5" stroke="white" stroke-width="1" opacity="0.5" />
    
    <!-- 橡皮擦部分 -->
    <rect x="16" y="2" width="3" height="2" rx="0.5" fill="currentColor" opacity="0.7" />
    
    <!-- 高光 -->
    <line x1="6" y1="16" x2="8" y2="18" stroke="white" stroke-width="1" opacity="0.4" />
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
