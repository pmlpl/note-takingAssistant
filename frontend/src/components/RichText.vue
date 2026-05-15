<template>
  <div class="rich-text-shell">
    <div ref="editorRef" class="rich-text-editor"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import WangEditor from 'wangeditor'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue'])

const editorRef = ref(null)
let editor = null

onMounted(() => {
  editor = new WangEditor(editorRef.value)
  
  editor.config.uploadImgShowBase64 = true
  editor.config.onchange = (html) => {
    emit('update:modelValue', html)
  }
  
  editor.create()
  
  if (props.modelValue) {
    editor.txt.html(props.modelValue)
  }
})

watch(() => props.modelValue, (newVal) => {
  if (editor && newVal !== editor.txt.html()) {
    editor.txt.html(newVal)
  }
})

defineExpose({
  getContent: () => editor?.txt.html(),
  setContent: (content) => editor?.txt.html(content)
})
</script>

<style scoped>
/* Flex 子项默认 min-width:auto，会被 Word 宽表格撑开导致整页横向滚动 */
.rich-text-shell {
  width: 100%;
  max-width: 100%;
  min-width: 0;
}

.rich-text-editor {
  width: 100%;
  max-width: 100%;
  min-width: 0;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  overflow: hidden;
  box-sizing: border-box;
}

.rich-text-editor :deep(.w-e-toolbar) {
  border-bottom: 1px solid #e4e7ed;
  flex-wrap: wrap;
}

/* 编辑区：仅纵向滚动，文档宽度跟随容器 */
.rich-text-editor :deep(.w-e-text-container) {
  height: min(70vh, 720px) !important;
  overflow-x: hidden !important;
  overflow-y: auto !important;
}

.rich-text-editor :deep(.w-e-scroll) {
  overflow-x: hidden !important;
  overflow-y: auto !important;
}

.rich-text-editor :deep(.w-e-text) {
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.rich-text-editor :deep(.w-e-text img),
.rich-text-editor :deep(.w-e-text video) {
  max-width: 100% !important;
  height: auto !important;
}

.rich-text-editor :deep(.w-e-text table) {
  width: 100% !important;
  max-width: 100% !important;
  table-layout: fixed;
}

.rich-text-editor :deep(.w-e-text td),
.rich-text-editor :deep(.w-e-text th) {
  word-break: break-word;
}
</style>