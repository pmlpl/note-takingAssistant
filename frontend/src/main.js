import { createApp } from 'vue'
import { createPinia } from 'pinia'
import 'element-plus/es/components/message/style/css'
import 'element-plus/es/components/message-box/style/css'
import '@/assets/style.css'
import router from './router'
import App from './App.vue'

if (typeof window !== 'undefined' && !window.dragEvent) {
  window.dragEvent = function (event) {
    return event || window.event
  }
}

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

app.config.errorHandler = (err, instance, info) => {
  console.error('Global error handler:', err, instance, info)
}

app.mount('#app')
