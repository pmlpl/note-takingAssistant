<template>
  <BaseIcon :size="size" :color="color">
    <!-- 圆形背景 -->
    <circle
      cx="12" cy="12" r="10" 
      fill="currentColor" 
      opacity="0.9"
    />
    
    <!-- 加号 -->
    <line
      x1="12" y1="7" x2="12" y2="17" 
      stroke="white" 
      stroke-width="2.5" 
      stroke-linecap="round"
    />
    <line
      x1="7" y1="12" x2="17" y2="12" 
      stroke="white" 
      stroke-width="2.5" 
      stroke-linecap="round"
    />
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
