<template>
  <div ref="rootEl" class="markdown-content" v-bind="$attrs" v-html="safeHtml"></div>
</template>

<script setup>
import { computed, ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { renderContentToSafeHtml, hydrateMermaidBlocks } from '@/utils/htmlSanitize'

defineOptions({
  name: 'MarkdownContent',
  inheritAttrs: false
})

const props = defineProps({
  /** 原始内容（HTML 或 Markdown），由统一渲染管线判断并安全渲染 */
  content: {
    type: String,
    default: ''
  }
})

const rootEl = ref(null)
const safeHtml = computed(() => renderContentToSafeHtml(props.content))

// 流式输出时每个 delta 都会重渲染，mermaid 水合防抖到内容稳定后执行
const HYDRATE_DELAY = 300
let mermaidTimer = null

function scheduleMermaidHydrate() {
  clearTimeout(mermaidTimer)
  mermaidTimer = setTimeout(() => {
    const el = rootEl.value
    if (el) void hydrateMermaidBlocks(el)
  }, HYDRATE_DELAY)
}

watch(safeHtml, scheduleMermaidHydrate)
onMounted(scheduleMermaidHydrate)
onBeforeUnmount(() => {
  clearTimeout(mermaidTimer)
})
</script>
