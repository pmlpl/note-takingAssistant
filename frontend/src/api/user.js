import api from './index'

export const userApi = {
  login(data) {
    return api.post('/v1/user/login', data)
  },
  
  register(data) {
    return api.post('/v1/user/register', data)
  },
  
  changePassword(data) {
    return api.put('/v1/user/password', data)
  },
  
  getUserInfo() {
    return api.get('/v1/user/me')
  }
}