<template>
  <div class="rich-text-shell">
    <Toolbar
      class="rich-text-toolbar"
      :editor="editorRef"
      :defaultConfig="toolbarConfig"
      mode="default"
    />
    <Editor
      class="rich-text-editor"
      v-model="valueHtml"
      :defaultConfig="editorConfig"
      mode="default"
      @onCreated="handleCreated"
      @onChange="handleChange"
    />
  </div>
</template>

<script setup>
import { ref, shallowRef, onBeforeUnmount, watch } from 'vue'
import { Editor, Toolbar } from '@wangeditor/editor-for-vue'
import '@wangeditor/editor/dist/css/style.css'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue'])

const editorRef = shallowRef()
const valueHtml = ref(props.modelValue)

const toolbarConfig = {}

const editorConfig = {
  placeholder: '请输入内容...',
  MENU_CONF: {
    uploadImage: {
      base64LimitSize: 10 * 1024 * 1024
    }
  }
}

const handleCreated = (editor) => {
  editorRef.value = editor
}

const handleChange = (editor) => {
  emit('update:modelValue', editor.getHtml())
}

watch(() => props.modelValue, (newVal) => {
  if (editorRef.value && newVal !== editorRef.value.getHtml()) {
    valueHtml.value = newVal
  }
})

onBeforeUnmount(() => {
  const editor = editorRef.value
  if (editor == null) return
  editor.destroy()
})

defineExpose({
  getContent: () => editorRef.value?.getHtml() || '',
  setContent: (content) => {
    if (editorRef.value) {
      editorRef.value.setHtml(content)
    }
  }
})
</script>

<style scoped>
.rich-text-shell {
  width: 100%;
  max-width: 100%;
  min-width: 0;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  overflow: hidden;
  box-sizing: border-box;
}

.rich-text-toolbar {
  border-bottom: 1px solid #e4e7ed;
  flex-wrap: wrap;
}

.rich-text-editor {
  width: 100%;
  max-width: 100%;
  min-width: 0;
  height: min(120vh, 800px);
  overflow: hidden;
  overflow-y: auto;
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
