import api from './index'

/** 导入/解析 Word 等可能超过默认 30s */
const NOTE_IMPORT_TIMEOUT_MS = 120_000

export const noteApi = {
  getNotes() {
    return api.get('/v1/note/')
  },
  
  getNote(id) {
    return api.get(`/v1/note/${id}`)
  },
  
  createNote(data) {
    return api.post('/v1/note/', data)
  },
  
  updateNote(id, data) {
    return api.put(`/v1/note/${id}`, data)
  },
  
  deleteNote(id) {
    return api.delete(`/v1/note/${id}`)
  },
  
  /**
   * 导入笔记文件
   * @param {File} file - 要导入的文件对象
   * @param {{ overwrite?: boolean }} [options] - overwrite=true 时覆盖同名标题笔记（后端 409 后重试用）
   * @returns {Promise} 返回创建的笔记
   */
  importNote(file, options = {}) {
    const formData = new FormData()
    formData.append('file', file)
    if (options.overwrite) {
      formData.append('overwrite', 'true')
    }
    return api.post('/v1/note/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: NOTE_IMPORT_TIMEOUT_MS
    })
  },
  
  /**
   * 获取最近笔记（从Redis缓存）
   * @returns {Promise} 返回最多5个最近笔记
   */
  getRecentNotes() {
    return api.get('/v1/note/recent')
  },
  
  /**
   * 更新最近笔记顺序
   * @param {Array<number>} noteIds - 笔记ID列表（按最新到最旧的顺序）
   * @returns {Promise} 返回更新结果
   */
  updateRecentNotesOrder(noteIds) {
    return api.post('/v1/note/recent/update', noteIds)
  }
}