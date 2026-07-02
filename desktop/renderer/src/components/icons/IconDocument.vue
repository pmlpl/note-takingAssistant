<template>
  <BaseIcon :size="size" :color="color">
    <!-- 文档主体 -->
    <path d="M6 2C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2H6Z" 
      fill="currentColor" 
      stroke="currentColor" 
      stroke-width="1.5" 
      stroke-linejoin="round"/>
    
    <!-- 折叠角 -->
    <path d="M14 2V8H20" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    
    <!-- 文本行 -->
    <line x1="8" y1="12" x2="16" y2="12" stroke="white" stroke-width="1.5" stroke-linecap="round" opacity="0.6"/>
    <line x1="8" y1="15" x2="16" y2="15" stroke="white" stroke-width="1.5" stroke-linecap="round" opacity="0.6"/>
    <line x1="8" y1="18" x2="13" y2="18" stroke="white" stroke-width="1.5" stroke-linecap="round" opacity="0.6"/>
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
