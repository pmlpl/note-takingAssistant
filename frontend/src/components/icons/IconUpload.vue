<template>
  <BaseIcon :size="size" :color="color">
    <!-- 云朵主体 -->
    <path
      d="M18 10H16.74C16.32 8.09 14.76 6.56 12.84 6.13C10.92 5.7 8.93 6.45 7.71 7.91C6.49 9.37 6.18 11.37 6.87 13.11C5.09 13.42 3.66 14.72 3.22 16.45C2.78 18.18 3.42 20 4.88 21.09C6.34 22.18 8.32 22.23 9.83 21.22H18C19.66 21.22 21 19.88 21 18.22C21 16.56 19.66 15.22 18 15.22V10Z" 
      fill="currentColor" 
      stroke="currentColor" 
      stroke-width="1.5" 
      stroke-linejoin="round"
    />
    
    <!-- 向上箭头 -->
    <path
      d="M12 14V8M12 8L9 11M12 8L15 11" 
      stroke="white" 
      stroke-width="2" 
      stroke-linecap="round" 
      stroke-linejoin="round"
      opacity="0.9"
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
