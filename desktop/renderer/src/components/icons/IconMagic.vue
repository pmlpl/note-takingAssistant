<template>
  <BaseIcon :size="size" :color="color" viewBox="0 0 24 24">
    <!-- 魔法棒主体（从左下到右上倾斜） -->
    <rect
      x="4"
      y="14.5"
      width="14"
      height="3"
      rx="1.5"
      transform="rotate(-45 11 17.5)"
      fill="currentColor"
    />

    <!-- 魔法棒头部星星 -->
    <path
      d="M17 5L18.2 7.8L21 9L18.2 10.2L17 13L15.8 10.2L13 9L15.8 7.8L17 5Z"
      fill="currentColor"
    />

    <!-- 魔法粒子/星光 -->
    <circle cx="6" cy="6" r="1" fill="currentColor" opacity="0.6"/>
    <circle cx="20" cy="4" r="0.8" fill="currentColor" opacity="0.5"/>
    <circle cx="21" cy="14" r="0.6" fill="currentColor" opacity="0.4"/>
    <circle cx="4" cy="18" r="0.7" fill="currentColor" opacity="0.5"/>

    <!-- 小光点 -->
    <circle cx="19" cy="7" r="0.5" fill="currentColor" opacity="0.7"/>
    <circle cx="8" cy="19" r="0.5" fill="currentColor" opacity="0.6"/>
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

