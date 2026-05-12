<template>
  <div ref="editorRef" class="rich-text-editor"></div>
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
  editor.config.height = 400
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
.rich-text-editor {
  border: 1px solid #e4e7ed;
  border-radius: 4px;
}

.rich-text-editor :deep(.w-e-toolbar) {
  border-bottom: 1px solid #e4e7ed;
  flex-wrap: wrap;
}

.rich-text-editor :deep(.w-e-text-container) {
  height: 400px;
}
</style>