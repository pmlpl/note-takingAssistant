<template>
  <BaseIcon :size="size" :color="color">
    <!-- 中心节点 -->
    <circle cx="12" cy="12" r="2.5" fill="currentColor" />
    <!-- 主干连线 -->
    <line
      x1="12"
      y1="12"
      x2="12"
      y2="4.5"
      stroke="currentColor"
      stroke-width="1.6"
      stroke-linecap="round"
    />
    <line
      x1="12"
      y1="12"
      x2="12"
      y2="19.5"
      stroke="currentColor"
      stroke-width="1.6"
      stroke-linecap="round"
    />
    <line
      x1="12"
      y1="12"
      x2="4.5"
      y2="12"
      stroke="currentColor"
      stroke-width="1.6"
      stroke-linecap="round"
    />
    <line
      x1="12"
      y1="12"
      x2="19.5"
      y2="12"
      stroke="currentColor"
      stroke-width="1.6"
      stroke-linecap="round"
    />
    <!-- 四向端点 -->
    <circle cx="12" cy="4.5" r="1.8" fill="currentColor" opacity="0.9" />
    <circle cx="12" cy="19.5" r="1.8" fill="currentColor" opacity="0.9" />
    <circle cx="4.5" cy="12" r="1.8" fill="currentColor" opacity="0.9" />
    <circle cx="19.5" cy="12" r="1.8" fill="currentColor" opacity="0.9" />
    <!-- 斜向分支 -->
    <line
      x1="12"
      y1="12"
      x2="5.5"
      y2="5.5"
      stroke="currentColor"
      stroke-width="1.35"
      stroke-linecap="round"
      opacity="0.75"
    />
    <line
      x1="12"
      y1="12"
      x2="18.5"
      y2="5.5"
      stroke="currentColor"
      stroke-width="1.35"
      stroke-linecap="round"
      opacity="0.75"
    />
    <circle cx="5.5" cy="5.5" r="1.45" fill="currentColor" opacity="0.75" />
    <circle cx="18.5" cy="5.5" r="1.45" fill="currentColor" opacity="0.75" />
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
