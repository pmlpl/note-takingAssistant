import api from './index'

export const userApi = {
  login(data) {
    return api.post('/v1/user/login', data)
  },
  
  register(data) {
    return api.post('/v1/user/register', data)
  },

  logout() {
    return api.post('/v1/user/logout')
  },
  
  changePassword(data) {
    return api.put('/v1/user/password', data)
  },
  
  getUserInfo() {
    return api.get('/v1/user/me')
  },
  
  uploadAvatar(file) {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/v1/user/avatar', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  getUserStats() {
    return api.get('/v1/user/stats')
  },

  getLLMSettings() {
    return api.get('/v1/user/me/llm-settings')
  },

  putLLMSettings(data) {
    return api.put('/v1/user/me/llm-settings', data)
  }
}