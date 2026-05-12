<template>
  <div class="login-container">
    <div class="login-wrapper">
      <el-card class="login-card">
        <div class="login-header">
          <IconNotebook :size="48" color="#409eff" />
          <h2>AI笔记助手</h2>
          <p>登录您的账号</p>
        </div>
        <el-form :model="form" ref="formRef" label-width="80px">
          <el-form-item label="用户名" prop="username" :rules="[{ required: true, message: '请输入用户名' }]">
            <el-input v-model="form.username" placeholder="请输入用户名" />
          </el-form-item>
          <el-form-item label="密码" prop="password" :rules="[{ required: true, message: '请输入密码' }]">
            <el-input v-model="form.password" type="password" placeholder="请输入密码" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleLogin" :loading="loading" class="login-btn">
              {{ loading ? '登录中...' : '登录' }}
            </el-button>
          </el-form-item>
        </el-form>
        <div class="login-footer">
          <span>还没有账号？</span>
          <el-button link @click="navigate('/register')">立即注册</el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store'
import { userApi } from '@/api/user'
import { IconNotebook } from '@/components/icons'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref(null)
const loading = ref(false)

const form = ref({
  username: '',
  password: ''
})

async function handleLogin() {
  if (!form.value.username || !form.value.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const response = await userApi.login(form.value)
    // 后端返回格式: { access_token, token_type, user }
    userStore.login(response.access_token, response.user)
    ElMessage.success('登录成功！')
    router.push('/home')
  } catch (error) {

    // 根据错误类型显示不同的提示
    if (error.response?.status === 401) {
      ElMessage.error('用户名或密码错误，请重试')
    } else if (error.response?.status === 404) {
      ElMessage.error('用户不存在，请先注册')
    } else if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('登录失败，请检查网络连接')
    }
  } finally {
    loading.value = false
  }
}

function navigate(path) {
  router.push(path)
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
  position: relative;
  overflow: hidden;
  padding: 40px 20px;
}

.login-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    radial-gradient(circle at 20% 50%, rgba(120, 119, 198, 0.15) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(78, 205, 196, 0.15) 0%, transparent 50%),
    radial-gradient(circle at 40% 20%, rgba(69, 183, 209, 0.1) 0%, transparent 50%);
  pointer-events: none;
}

.login-wrapper {
  width: 100%;
  max-width: 1200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 50px;
  position: relative;
  z-index: 1;
}

.login-card {
  width: 100%;
  max-width: 450px;
  padding: 40px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.98);
  border-radius: 80px;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h2 {
  margin: 15px 0 5px 0;
  font-size: 24px;
  color: #303133;
}

.login-header p {
  color: #909399;
  margin: 0;
}

.login-btn {
  width: 100%;
}

.login-footer {
  text-align: center;
  margin-top: 20px;
  color: #909399;
}

</style>