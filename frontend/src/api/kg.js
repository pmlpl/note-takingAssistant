import api from './index'

export const kgApi = {
  getGraph() {
    return api.get('/v1/kg/graph')
  },

  refreshGraph() {
    return api.post('/v1/kg/refresh')
  },

  getStatus() {
    return api.get('/v1/kg/status')
  },
}
