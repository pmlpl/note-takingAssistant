import api from './index'

export const publicApi = {
  getWelcomeStats() {
    return api.get('/v1/public/welcome-stats')
  },
}
