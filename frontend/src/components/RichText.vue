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
import { useUserStore } from '@/store'
import { UPLOAD_IMAGE_URL, IMAGE_BASE_URL } from '@/config/api'

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
      server: UPLOAD_IMAGE_URL,
      fieldName: 'file',
      maxFileSize: 5 * 1024 * 1024,
      base64LimitSize: 100 * 1024,
      customUpload(file, insertFn) {
        const userStore = useUserStore()
        const formData = new FormData()
        formData.append('file', file)

        fetch(UPLOAD_IMAGE_URL, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${userStore.token}`
          },
          body: formData
        })
          .then(res => res.json())
          .then(res => {
            if (res.url) {
              const url = res.url.startsWith('http') ? res.url : `${IMAGE_BASE_URL}${res.url}`
              insertFn(url, file.name, url)
            } else {
              console.error('上传失败:', res.detail || '未知错误')
            }
          })
          .catch(err => {
            console.error('上传图片失败:', err)
          })
      }
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
  border: 1px solid var(--el-border-color-light);
  border-radius: 4px;
  overflow: hidden;
  box-sizing: border-box;
}

.rich-text-toolbar {
  border-bottom: 1px solid var(--el-border-color-light);
  flex-wrap: wrap;
}

.rich-text-editor {
  width: 100%;
  max-width: 100%;
  min-width: 0;
  height: min(120vh, 800px);
  /* P3 评审 #14：矮视口下 120vh 可能 <300px，触发 wangEditor hoverbar 定位警告，保证下限 */
  min-height: 400px;
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
