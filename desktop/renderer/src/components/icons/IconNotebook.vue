<template>
  <BaseIcon :size="size" :color="color" viewBox="0 0 64 64">
    <!-- 笔记管理：线圈本（与品牌 Logo 区分开） -->
    <rect
      x="16"
      y="10"
      width="40"
      height="48"
      rx="5"
      fill="currentColor"
      stroke="currentColor"
      stroke-width="2"
      stroke-linejoin="round"
    />

    <!-- 线圈环 -->
    <circle cx="14" cy="18" r="3" fill="none" stroke="currentColor" stroke-width="2.5" />
    <circle cx="14" cy="32" r="3" fill="none" stroke="currentColor" stroke-width="2.5" />
    <circle cx="14" cy="46" r="3" fill="none" stroke="currentColor" stroke-width="2.5" />

    <!-- 内页横线 -->
    <line x1="24" y1="22" x2="48" y2="22" stroke="white" stroke-width="2.2" stroke-linecap="round" opacity="0.9" />
    <line x1="24" y1="30" x2="48" y2="30" stroke="white" stroke-width="2.2" stroke-linecap="round" opacity="0.85" />
    <line x1="24" y1="38" x2="48" y2="38" stroke="white" stroke-width="2.2" stroke-linecap="round" opacity="0.85" />
    <line x1="24" y1="46" x2="44" y2="46" stroke="white" stroke-width="2.2" stroke-linecap="round" opacity="0.8" />

    <!-- 书签 -->
    <path
      fill="white"
      opacity="0.95"
      d="M44 10 V26 L48 22 L52 26 V10 H44 Z"
    />
  </BaseIcon>
</template>

<script setup>
import BaseIcon from './BaseIcon.vue'

defineProps({
  size: {
    type: [String, Number],
    default: 32,
  },
  color: {
    type: String,
    default: '#2d5da1',
  },
})
</script>
