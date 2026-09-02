<template>
  <BaseIcon :size="size" :color="color">
    <!-- 头像圆形 -->
    <circle cx="12" cy="8" r="5" fill="currentColor" opacity="0.9" />
    
    <!-- 身体/肩膀 -->
    <path
      d="M4 20C4 16.6863 7.13401 14 11 14H13C16.866 14 20 16.6863 20 20" 
      fill="currentColor" 
      stroke="currentColor" 
      stroke-width="1.5" 
      stroke-linecap="round"
    />
    
    <!-- 高光效果 -->
    <circle cx="10.5" cy="6.5" r="1.5" fill="white" opacity="0.3" />
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
