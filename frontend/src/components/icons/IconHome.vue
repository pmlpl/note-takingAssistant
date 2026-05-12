<template>
  <BaseIcon :size="size" :color="color">
    <!-- 房子主体 -->
    <path d="M3 12L12 4L21 12V20C21 20.5304 20.7893 21.0391 20.4142 21.4142C20.0391 21.7893 19.5304 22 19 22H5C4.46957 22 3.96086 21.7893 3.58579 21.4142C3.21071 21.0391 3 20.5304 3 20V12Z" 
      fill="currentColor" 
      stroke="currentColor" 
      stroke-width="1.5" 
      stroke-linejoin="round"/>
    
    <!-- 门 -->
    <rect x="9" y="14" width="6" height="8" rx="1" fill="white" opacity="0.3"/>
    
    <!-- 窗户 -->
    <rect x="5.5" y="11" width="3" height="3" rx="0.5" fill="white" opacity="0.4"/>
    <rect x="15.5" y="11" width="3" height="3" rx="0.5" fill="white" opacity="0.4"/>
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
