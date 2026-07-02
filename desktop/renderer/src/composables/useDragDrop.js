/**
 * 桌面端拖拽导入功能封装
 * 支持拖拽文件到窗口进行导入
 */
import { ref } from 'vue'
import { useDesktop } from './useDesktop'
import { useNotification } from './useNotification'

// 支持的文件类型
const SUPPORTED_EXTENSIONS = ['.txt', '.md', '.docx', '.pdf', '.jpg', '.jpeg', '.png']
const MAX_FILE_SIZE = 10 * 1024 * 1024 // 10MB

export function useDragDrop() {
  const { isDesktop, readFile } = useDesktop()
  const { notifyImportSuccess } = useNotification()

  const isDragging = ref(false)
  const dragFiles = ref([])
  const dragError = ref(null)

  /**
   * 检查文件是否支持
   * @param {string} fileName - 文件名
   * @returns {boolean}
   */
  function isSupportedFile(fileName) {
    const ext = fileName.toLowerCase().slice(fileName.lastIndexOf('.'))
    return SUPPORTED_EXTENSIONS.includes(ext)
  }

  /**
   * 处理拖拽进入
   * @param {DragEvent} e
   */
  function handleDragEnter(e) {
    if (!isDesktop.value) return

    e.preventDefault()
    e.stopPropagation()

    isDragging.value = true
    dragError.value = null

    // 获取拖拽的文件列表
    const files = Array.from(e.dataTransfer.files)
    dragFiles.value = files.map(f => ({
      name: f.name,
      path: f.path,
      size: f.size,
      type: f.type
    }))

    // 检查文件类型
    const unsupportedFiles = files.filter(f => !isSupportedFile(f.name))
    if (unsupportedFiles.length > 0) {
      dragError.value = `不支持以下文件类型: ${unsupportedFiles.map(f => f.name).join(', ')}`
    }

    // 检查文件大小
    const oversizedFiles = files.filter(f => f.size > MAX_FILE_SIZE)
    if (oversizedFiles.length > 0) {
      dragError.value = `文件过大: ${oversizedFiles.map(f => f.name).join(', ')} (最大10MB)`
    }
  }

  /**
   * 处理拖拽悬停
   * @param {DragEvent} e
   */
  function handleDragOver(e) {
    if (!isDesktop.value) return

    e.preventDefault()
    e.stopPropagation()
  }

  /**
   * 处理拖拽离开
   * @param {DragEvent} e
   */
  function handleDragLeave(e) {
    if (!isDesktop.value) return

    e.preventDefault()
    e.stopPropagation()

    // 确保真正离开了窗口
    const rect = e.currentTarget.getBoundingClientRect()
    const x = e.clientX
    const y = e.clientY
    if (x < rect.left || x > rect.right || y < rect.top || y > rect.bottom) {
      isDragging.value = false
      dragFiles.value = []
      dragError.value = null
    }
  }

  /**
   * 处理拖拽释放
   * @param {DragEvent} e
   * @param {Function} onImport - 导入回调函数
   */
  async function handleDrop(e, onImport) {
    if (!isDesktop.value) return

    e.preventDefault()
    e.stopPropagation()

    isDragging.value = false

    const files = Array.from(e.dataTransfer.files)
    const validFiles = files.filter(f => isSupportedFile(f.name) && f.size <= MAX_FILE_SIZE)

    if (validFiles.length === 0) {
      dragError.value = '没有有效的文件可导入'
      return
    }

    // 读取文件内容
    const results = []
    for (const file of validFiles) {
      try {
        const ext = file.name.toLowerCase().slice(file.name.lastIndexOf('.'))

        // 图片文件直接返回路径
        if (['.jpg', '.jpeg', '.png'].includes(ext)) {
          results.push({
            fileName: file.name,
            filePath: file.path,
            fileType: 'image',
            success: true
          })
        } else {
          // 文本文件读取内容
          const result = await readFile(file.path, 'utf-8')
          if (result.success) {
            results.push({
              fileName: file.name,
              filePath: file.path,
              fileType: 'text',
              content: result.data,
              success: true
            })
          } else {
            results.push({
              fileName: file.name,
              filePath: file.path,
              fileType: 'text',
              success: false,
              error: result.error
            })
          }
        }
      } catch (err) {
        results.push({
          fileName: file.name,
          filePath: file.path,
          success: false,
          error: err.message
        })
      }
    }

    // 调用导入回调
    if (onImport && typeof onImport === 'function') {
      await onImport(results)
    }

    // 发送成功通知
    const successCount = results.filter(r => r.success).length
    if (successCount > 0) {
      await notifyImportSuccess(`${successCount}个文件`)
    }

    dragFiles.value = []
    dragError.value = null
  }

  /**
   * 注册全局拖拽事件监听
   * @param {HTMLElement} target - 目标元素
   * @param {Function} onImport - 导入回调
   * @returns {Function} 清理函数
   */
  function registerDragDrop(target, onImport) {
    if (!isDesktop.value || !target) return () => {}

    const enterHandler = (e) => handleDragEnter(e)
    const overHandler = (e) => handleDragOver(e)
    const leaveHandler = (e) => handleDragLeave(e)
    const dropHandler = (e) => handleDrop(e, onImport)

    target.addEventListener('dragenter', enterHandler)
    target.addEventListener('dragover', overHandler)
    target.addEventListener('dragleave', leaveHandler)
    target.addEventListener('drop', dropHandler)

    return () => {
      target.removeEventListener('dragenter', enterHandler)
      target.removeEventListener('dragover', overHandler)
      target.removeEventListener('dragleave', leaveHandler)
      target.removeEventListener('drop', dropHandler)
    }
  }

  return {
    isDesktop,
    isDragging,
    dragFiles,
    dragError,
    handleDragEnter,
    handleDragOver,
    handleDragLeave,
    handleDrop,
    registerDragDrop,
    isSupportedFile,
    SUPPORTED_EXTENSIONS
  }
}