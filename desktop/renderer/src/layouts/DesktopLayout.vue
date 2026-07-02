<template>
  <div class="desktop-layout" ref="layoutRef">
    <!-- 自定义标题栏 -->
    <TitleBar />

    <!-- 主容器：侧边栏 + 内容区 -->
    <div class="desktop-main-container">
      <!-- 常驻侧边栏 -->
      <DesktopSidebar />

      <!-- 主内容区 -->
      <main class="desktop-content">
        <slot />
      </main>
    </div>

    <!-- 拖拽导入遮罩层 -->
    <DragDropOverlay
      :is-dragging="isDragging"
      :drag-files="dragFiles"
      :drag-error="dragError"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import TitleBar from '@/components/desktop/TitleBar.vue'
import DesktopSidebar from '@/components/desktop/DesktopSidebar.vue'
import DragDropOverlay from '@/components/desktop/DragDropOverlay.vue'
import { useDragDrop } from '@/composables/useDragDrop'
import { ElMessage } from 'element-plus'

const router = useRouter()
const layoutRef = ref(null)

const {
  isDragging,
  dragFiles,
  dragError,
  registerDragDrop
} = useDragDrop()

// 处理拖拽导入的文件
async function handleDragImport(results) {
  const successfulFiles = results.filter(r => r.success)
  const failedFiles = results.filter(r => !r.success)

  // 显示失败文件错误信息
  if (failedFiles.length > 0) {
    const errors = failedFiles.map(f => `${f.fileName}: ${f.error}`).join('\n')
    ElMessage.error(`导入失败:\n${errors}`)
  }

  // 处理成功导入的文件
  if (successfulFiles.length > 0) {
    // 跳转到笔记列表或新建笔记页面
    const textFiles = successfulFiles.filter(f => f.fileType === 'text')
    const imageFiles = successfulFiles.filter(f => f.fileType === 'image')

    if (textFiles.length > 0) {
      // 如果只有一个文本文件,直接跳转到新建笔记
      if (textFiles.length === 1) {
        // 将文件内容存储到sessionStorage,供新建笔记页面读取
        sessionStorage.setItem('dragImportContent', textFiles[0].content)
        sessionStorage.setItem('dragImportFileName', textFiles[0].fileName)
        router.push('/notes/new')
      } else {
        // 多个文件跳转到笔记列表
        ElMessage.success(`成功导入 ${successfulFiles.length} 个文件，请到笔记列表查看`)
        router.push('/notes')
      }
    } else if (imageFiles.length > 0) {
      ElMessage.info('图片文件需要在笔记编辑页导入')
      router.push('/notes')
    }
  }
}

let cleanupDragDrop = null

onMounted(() => {
  if (layoutRef.value) {
    cleanupDragDrop = registerDragDrop(layoutRef.value, handleDragImport)
  }
})

onUnmounted(() => {
  if (cleanupDragDrop) {
    cleanupDragDrop()
  }
})
</script>

<style scoped>
.desktop-layout {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-paper);
  background-image: radial-gradient(var(--color-muted) 1px, transparent 1px);
  background-size: 24px 24px;
  overflow: hidden;
}

.desktop-main-container {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.desktop-content {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  background: var(--color-content-bg);
}

/* 桌面端页面包装器：占满整个内容区，自己管理滚动 */
.desktop-content :deep(.desktop-page-wrapper) {
  width: 100%;
  height: 100%;
  overflow: auto;
}

/* 响应系统主题 */
@media (prefers-color-scheme: dark) {
  .desktop-content {
    background: var(--color-content-bg);
  }
}
</style>