<template>
  <BaseIcon :size="size" :color="color">
    <!-- 网络节点 - 左上 -->
    <circle cx="5" cy="5" r="2" fill="currentColor" />
    <!-- 网络节点 - 右上 -->
    <circle cx="19" cy="5" r="2" fill="currentColor" />
    <!-- 网络节点 - 左下 -->
    <circle cx="5" cy="19" r="2" fill="currentColor" />
    <!-- 网络节点 - 右下 -->
    <circle cx="19" cy="19" r="2" fill="currentColor" />
    <!-- 中心节点 -->
    <circle cx="12" cy="12" r="2.5" fill="currentColor" />
    <!-- 连接线 - 中心到四角 -->
    <line
      x1="12"
      y1="12"
      x2="5"
      y2="5"
      stroke="currentColor"
      stroke-width="1.5"
      stroke-linecap="round"
      opacity="0.7"
    />
    <line
      x1="12"
      y1="12"
      x2="19"
      y2="5"
      stroke="currentColor"
      stroke-width="1.5"
      stroke-linecap="round"
      opacity="0.7"
    />
    <line
      x1="12"
      y1="12"
      x2="5"
      y2="19"
      stroke="currentColor"
      stroke-width="1.5"
      stroke-linecap="round"
      opacity="0.7"
    />
    <line
      x1="12"
      y1="12"
      x2="19"
      y2="19"
      stroke="currentColor"
      stroke-width="1.5"
      stroke-linecap="round"
      opacity="0.7"
    />
    <!-- 横向连接 -->
    <line
      x1="5"
      y1="5"
      x2="19"
      y2="5"
      stroke="currentColor"
      stroke-width="1.2"
      stroke-linecap="round"
      opacity="0.5"
    />
    <line
      x1="5"
      y1="19"
      x2="19"
      y2="19"
      stroke="currentColor"
      stroke-width="1.2"
      stroke-linecap="round"
      opacity="0.5"
    />
    <!-- 纵向连接 -->
    <line
      x1="5"
      y1="5"
      x2="5"
      y2="19"
      stroke="currentColor"
      stroke-width="1.2"
      stroke-linecap="round"
      opacity="0.5"
    />
    <line
      x1="19"
      y1="5"
      x2="19"
      y2="19"
      stroke="currentColor"
      stroke-width="1.2"
      stroke-linecap="round"
      opacity="0.5"
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