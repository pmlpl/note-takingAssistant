<template>
  <div v-if="isDragging" class="drag-drop-overlay">
    <div class="drag-drop-content">
      <IconUpload :size="64" :color="ICON_COLOR" />
      <h2 class="drag-title">拖拽文件到此处导入</h2>
      <p class="drag-subtitle">支持 TXT, MD, DOCX, PDF, JPG, PNG 格式</p>

      <!-- 文件列表预览 -->
      <div v-if="dragFiles.length > 0" class="drag-files-preview">
        <div v-for="file in dragFiles" :key="file.name" class="preview-item">
          <IconDocument :size="16" :color="ICON_COLOR" />
          <span class="preview-name">{{ file.name }}</span>
          <span class="preview-size">{{ formatFileSize(file.size) }}</span>
        </div>
      </div>

      <!-- 错误提示 -->
      <div v-if="dragError" class="drag-error">
        <IconWarning :size="16" color="#ff4d4d" />
        <span>{{ dragError }}</span>
      </div>
    </div>

    <!-- 背景遮罩 -->
    <div class="drag-drop-background"></div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { IconUpload, IconDocument } from '@/components/icons'

const ICON_COLOR = 'var(--color-pencil)'

const props = defineProps({
  isDragging: Boolean,
  dragFiles: Array,
  dragError: String
})

function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
</script>

<style scoped>
.drag-drop-overlay {
  position: fixed;
  top: 36px; /* 为标题栏留出空间 */
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9998;
  display: flex;
  align-items: center;
  justify-content: center;
}

.drag-drop-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
}

.drag-drop-content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 40px 60px;
  background: var(--color-card-bg);
  border: 3px dashed var(--color-pencil);
  border-radius: var(--radius-wobbly-md);
  box-shadow: var(--shadow-hard-lg);
  animation: pulse-border 1.5s ease infinite;
}

.drag-title {
  font-family: var(--font-heading);
  font-size: 24px;
  color: var(--color-pencil);
  margin: 0;
}

.drag-subtitle {
  font-family: var(--font-body);
  font-size: 16px;
  color: var(--color-text-secondary);
  margin: 0;
}

.drag-files-preview {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 16px;
  padding: 12px 16px;
  background: var(--color-content-bg);
  border-radius: 8px;
  max-width: 400px;
}

.preview-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-text-primary);
}

.preview-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.preview-size {
  color: var(--color-text-muted);
  font-size: 12px;
}

.drag-error {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: rgba(255, 77, 77, 0.12);
  border-radius: 8px;
  color: var(--color-accent);
  font-family: var(--font-body);
  font-size: 14px;
  margin-top: 8px;
}

@keyframes pulse-border {
  0%, 100% {
    border-color: var(--color-pencil);
  }
  50% {
    border-color: var(--color-accent);
  }
}
</style>