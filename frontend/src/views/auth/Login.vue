<template>
  <div class="login-container">
    <div class="login-wrapper">
      <el-card class="login-card">
        <div class="login-header">
          <AppLogo :size="52" />
          <h2>智能笔记助手</h2>
          <p class="login-subtitle">登录您的账号</p>
        </div>

        <el-form :model="form" ref="formRef" label-width="80px">
          <el-form-item label="用户名" prop="username" :rules="[{ required: true, message: '请输入用户名' }]">
            <el-input v-model="form.username" placeholder="请输入用户名" />
          </el-form-item>
          <el-form-item label="密码" prop="password" :rules="[{ required: true, message: '请输入密码' }]">
            <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleLogin" :loading="loading" class="login-btn">
              {{ loading ? '登录中...' : '登 录' }}
            </el-button>
          </el-form-item>
        </el-form>

        <div class="login-footer">
          <span>还没有账号？</span>
          <el-button link @click="navigate('/register')">立即注册</el-button>
        </div>
      </el-card>
    </div>

    <!-- Decorative floating shapes -->
    <div class="deco deco-1"></div>
    <div class="deco deco-2"></div>
    <div class="deco deco-3"></div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store'
import { userApi } from '@/api/user'
import { AppLogo } from '@/components/icons'
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
    userStore.login(response.access_token, response.user)
    ElMessage.success('登录成功！')
    router.push('/home')
  } catch (error) {
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
/* ═══ Login Page — Hand-Drawn Theme ═══ */

.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-paper);
  background-image: radial-gradient(var(--color-muted) 1px, transparent 1px);
  background-size: 24px 24px;
  position: relative;
  overflow: hidden;
  padding: 40px 20px;
}

.login-wrapper {
  width: 100%;
  max-width: 1200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 40px;
  position: relative;
  z-index: 1;
}

/* ── Wobbly login card (was 80px, now organic) ── */
.login-card {
  width: 100%;
  max-width: 440px;
  padding: 0;
}
.login-card :deep(.el-card__body) {
  padding: 40px 36px 30px;
}

/* Thumbtack decoration at top */
.login-card::before {
  content: '';
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%) rotate(3deg);
  width: 22px;
  height: 22px;
  background: var(--color-accent);
  border-radius: 50%;
  box-shadow: 1px 1px 0px 0px rgba(0,0,0,0.3);
  z-index: 2;
  border: 3px solid #fff;
}

/* Tape strip */
.login-card::after {
  content: '';
  position: absolute;
  top: 16px;
  left: 50%;
  transform: translateX(-50%) rotate(-2deg);
  width: 90px;
  height: 18px;
  background: rgba(200, 200, 200, 0.3);
  border-radius: 2px;
  pointer-events: none;
}

.login-header {
  text-align: center;
  margin-bottom: 28px;
}

.login-header h2 {
  margin: 12px 0 4px;
  font-family: var(--font-heading);
  font-size: 28px;
  font-weight: 700;
  color: var(--color-pencil);
}

.login-subtitle {
  color: #888;
  font-family: var(--font-body);
  font-size: 15px;
  margin: 0;
}

.login-btn {
  width: 100%;
  font-size: 18px !important;
  padding: 12px 0 !important;
  height: auto !important;
}

.login-footer {
  text-align: center;
  margin-top: 20px;
  font-family: var(--font-body);
  color: #888;
}

/* ── Decorative floating blobs ── */
.deco {
  position: absolute;
  border-radius: 50%;
  border: 3px dashed var(--color-muted);
  pointer-events: none;
  opacity: 0.5;
}
.deco-1 {
  width: 180px;
  height: 180px;
  top: 12%;
  left: 8%;
  animation: floatDeco 8s ease-in-out infinite;
}
.deco-2 {
  width: 120px;
  height: 120px;
  bottom: 18%;
  right: 10%;
  background: var(--color-yellow);
  border-style: solid;
  animation: floatDeco 6s ease-in-out infinite reverse;
}
.deco-3 {
  width: 70px;
  height: 70px;
  top: 25%;
  right: 18%;
  background: var(--color-accent);
  opacity: 0.25;
  border-style: solid;
  animation: floatDeco 7s ease-in-out infinite 1s;
}

@keyframes floatDeco {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  33%  { transform: translateY(-15px) rotate(3deg); }
  66%  { transform: translateY(8px) rotate(-2deg); }
}
</style>
