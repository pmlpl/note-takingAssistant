<template>
  <BaseIcon :size="size" :color="color" viewBox="0 0 48 48">
    <!-- AI 助手：实心圆底 + 白色双环（∞ 形） -->
    <circle cx="24" cy="24" r="22" fill="currentColor" />
    <path
      fill="white"
      fill-rule="evenodd"
      clip-rule="evenodd"
      d="M16.8 24a7.2 9 0 1 1 14.4 0 7.2 9 0 1 1-14.4 0zm14.4 0a7.2 9 0 1 1 14.4 0 7.2 9 0 1 1-14.4 0z"
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
