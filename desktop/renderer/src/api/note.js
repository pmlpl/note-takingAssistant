import api from './index'

/** 导入/解析 Word 等可能超过默认 30s */
const NOTE_IMPORT_TIMEOUT_MS = 120_000

export const noteApi = {
  getNotes(skip = 0, limit = 100) {
    return api.get('/v1/note/', { params: { skip, limit } })
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

  searchNotes({ keyword = '', page = 1, pageSize = 20, isFavorite = undefined } = {}) {
    const params = { keyword, page, page_size: pageSize }
    if (isFavorite !== undefined) params.is_favorite = isFavorite
    return api.get('/v1/note/search', { params })
  },

  importNote(file, options = {}) {
    const formData = new FormData()
    formData.append('file', file)
    if (options.overwrite) {
      formData.append('overwrite', 'true')
    }
    return api.post('/v1/note/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: NOTE_IMPORT_TIMEOUT_MS,
    })
  },

  getRecentNotes() {
    return api.get('/v1/note/recent')
  },

  updateRecentNotesOrder(noteIds) {
    return api.post('/v1/note/recent/update', noteIds)
  },
}