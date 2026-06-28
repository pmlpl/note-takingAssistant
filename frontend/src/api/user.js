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
  },

  // 账号绑定相关
  getBindings() {
    return api.get('/v1/user/me/bindings')
  },

  updateNickname(nickname) {
    return api.put('/v1/user/me/nickname', { nickname })
  },

  unbindEmail(password) {
    return api.delete('/v1/user/me/bindings/email', { data: { password } })
  },

  unbindGithub() {
    return api.delete('/v1/user/me/bindings/github')
  }
}

export const oauthApi = {
  githubConfig() {
    return api.get('/v1/oauth/github/config')
  },

  githubAuthorize() {
    return api.post('/v1/oauth/github/authorize')
  },

  sendEmailCode(data) {
    return api.post('/v1/oauth/email/send-code', data)
  },

  verifyEmailCode(data) {
    return api.post('/v1/oauth/email/verify', data)
  },

  // 账号绑定相关
  sendBindCode(data) {
    return api.post('/v1/oauth/email/bind-code', data)
  },

  bindEmail(data) {
    return api.post('/v1/oauth/email/bind', data)
  }
}