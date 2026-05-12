NEW_FILE_CODE
<template>
  <BaseIcon :size="size" :color="color" viewBox="0 0 48 48">
    <!-- AI Logo - 智能大脑与科技元素结合 -->
    <defs>
      <linearGradient id="aiGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
        <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
      </linearGradient>
    </defs>
    
    <!-- 外圈圆环 -->
    <circle cx="24" cy="24" r="20" stroke="url(#aiGradient)" stroke-width="2.5" fill="none" opacity="0.3"/>
    
    <!-- 大脑轮廓 -->
    <path 
      d="M24 8 C18 8, 14 12, 14 17 C14 19, 15 21, 16 22 C14 23, 13 25, 13 27 C13 31, 16 34, 20 34 L28 34 C32 34, 35 31, 35 27 C35 25, 34 23, 32 22 C33 21, 34 19, 34 17 C34 12, 30 8, 24 8 Z" 
      fill="url(#aiGradient)"
      opacity="0.9"
    />
    
    <!-- 神经网络节点 -->
    <circle cx="20" cy="18" r="2" fill="white"/>
    <circle cx="28" cy="18" r="2" fill="white"/>
    <circle cx="24" cy="24" r="2.5" fill="white"/>
    <circle cx="19" cy="28" r="2" fill="white"/>
    <circle cx="29" cy="28" r="2" fill="white"/>
    
    <!-- 神经连接线 -->
    <line x1="20" y1="18" x2="28" y2="18" stroke="white" stroke-width="1.5" opacity="0.8"/>
    <line x1="20" y1="18" x2="24" y2="24" stroke="white" stroke-width="1.5" opacity="0.8"/>
    <line x1="28" y1="18" x2="24" y2="24" stroke="white" stroke-width="1.5" opacity="0.8"/>
    <line x1="24" y1="24" x2="19" y2="28" stroke="white" stroke-width="1.5" opacity="0.8"/>
    <line x1="24" y1="24" x2="29" y2="28" stroke="white" stroke-width="1.5" opacity="0.8"/>
    <line x1="19" y1="28" x2="29" y2="28" stroke="white" stroke-width="1.5" opacity="0.8"/>
    
    <!-- 闪烁的光点 -->
    <circle cx="24" cy="14" r="1" fill="white" opacity="0.9">
      <animate attributeName="opacity" values="0.9;0.3;0.9" dur="2s" repeatCount="indefinite"/>
    </circle>
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
    default: '#667eea'
  }
})
</script>
