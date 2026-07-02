<template>
  <svg 
    :width="size" 
    :height="size" 
    :viewBox="viewBox" 
    fill="none" 
    xmlns="http://www.w3.org/2000/svg"
    :style="{ color: color }"
  >
    <slot></slot>
  </svg>
</template>

<script setup>
defineProps({
  size: {
    type: [String, Number],
    default: 24
  },
  viewBox: {
    type: String,
    default: '0 0 24 24'
  },
  color: {
    type: String,
    default: 'currentColor'
  }
})
</script>

<style scoped>
svg {
  display: inline-block;
  vertical-align: middle;
}
</style>
