/**
 * 桌面端系统通知封装
 * 用于在AI生成完成等场景发送系统通知
 */
import { ref } from 'vue'
import { useDesktop } from './useDesktop'

export function useNotification() {
  const { isDesktop, showNotification } = useDesktop()
  const lastNotification = ref(null)

  /**
   * 发送系统通知
   * @param {string} title - 通知标题
   * @param {string} body - 通知内容
   * @returns {Promise<{success: boolean, error?: string}>}
   */
  async function notify(title, body) {
    if (!isDesktop.value) {
      console.log('[Notification] Web端不支持系统通知，使用console输出:', title, body)
      return { success: false, error: 'Web端不支持系统通知' }
    }

    const result = await showNotification(title, body)
    if (result.success) {
      lastNotification.value = { title, body, timestamp: Date.now() }
      console.log('[Notification] 系统通知发送成功:', title)
    } else {
      console.error('[Notification] 系统通知发送失败:', result.error)
    }
    return result
  }

  /**
   * AI生成完成通知
   * @param {string} noteTitle - 笔记标题
   */
  async function notifyAIComplete(noteTitle) {
    return notify(
      'AI生成完成',
      `笔记 "${noteTitle}" 已生成完毕，点击查看`
    )
  }

  /**
   * AI摘要完成通知
   * @param {string} noteTitle - 笔记标题
   */
  async function notifySummaryComplete(noteTitle) {
    return notify(
      'AI摘要完成',
      `笔记 "${noteTitle}" 的摘要已生成`
    )
  }

  /**
   * AI翻译完成通知
   * @param {string} noteTitle - 笔记标题
   * @param {string} targetLang - 目标语言
   */
  async function notifyTranslationComplete(noteTitle, targetLang = '英文') {
    return notify(
      '翻译完成',
      `笔记 "${noteTitle}" 已翻译为${targetLang}`
    )
  }

  /**
   * 笔记导入成功通知
   * @param {string} fileName - 文件名
   */
  async function notifyImportSuccess(fileName) {
    return notify(
      '导入成功',
      `文件 "${fileName}" 已成功导入为笔记`
    )
  }

  /**
   * 笔记导出成功通知
   * @param {string} fileName - 文件名
   */
  async function notifyExportSuccess(fileName) {
    return notify(
      '导出成功',
      `笔记已成功导出为 "${fileName}"`
    )
  }

  /**
   * 自动更新可用通知
   * @param {string} version - 新版本号
   */
  async function notifyUpdateAvailable(version) {
    return notify(
      '发现新版本',
      `NoteMind ${version} 已发布，建议更新以获得最新功能`
    )
  }

  return {
    isDesktop,
    lastNotification,
    notify,
    notifyAIComplete,
    notifySummaryComplete,
    notifyTranslationComplete,
    notifyImportSuccess,
    notifyExportSuccess,
    notifyUpdateAvailable
  }
}