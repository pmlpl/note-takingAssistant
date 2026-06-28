<template>
  <div class="register-container">
    <div class="register-wrapper">
      <el-card class="register-card">
        <!-- Tape strip decoration -->
        <div class="register-header">
          <AppLogo :size="52" />
          <h2>智能笔记助手</h2>
          <p class="register-subtitle">创建新账号</p>
        </div>

        <el-form :model="form" ref="formRef" label-width="80px">
          <el-form-item label="邮箱" prop="email" :rules="[
            { required: true, message: '请输入邮箱' },
            { type: 'email', message: '请输入正确的邮箱格式' }
          ]">
            <el-input v-model="form.email" placeholder="请输入邮箱地址" />
          </el-form-item>
          <el-form-item label="昵称" prop="nickname" :rules="[
            { min: 2, max: 32, message: '昵称长度为2-32个字符' }
          ]">
            <el-input v-model="form.nickname" placeholder="请输入昵称（可选，默认邮箱前缀）" />
          </el-form-item>
          <el-form-item label="密码" prop="password" :rules="[
            { required: true, message: '请输入密码' },
            { min: 8, message: '密码至少8位' },
            { pattern: /^(?=.*[A-Za-z])(?=.*\d)/, message: '密码必须同时包含字母和数字' }
          ]">
            <el-input v-model="form.password" type="password" placeholder="请输入密码（至少8位，含字母和数字）" show-password />
          </el-form-item>
          <el-form-item label="确认密码" prop="confirmPassword" :rules="[
            { required: true, message: '请确认密码' },
            {
              validator: (rule, value, callback) => {
                if (value !== form.password) {
                  callback(new Error('两次输入的密码不一致'))
                } else {
                  callback()
                }
              },
              trigger: 'blur'
            }
          ]">
            <el-input v-model="form.confirmPassword" type="password" placeholder="请再次输入密码" show-password />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleRegister" :loading="loading" class="register-btn">
              {{ loading ? '注册中...' : '注 册' }}
            </el-button>
          </el-form-item>
        </el-form>

        <div class="register-footer">
          <span>已有账号？</span>
          <el-button link @click="navigate('/login')">立即登录</el-button>
        </div>
      </el-card>
    </div>

    <!-- Decorative shapes -->
    <div class="deco deco-1"></div>
    <div class="deco deco-2"></div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { userApi } from '@/api/user'
import { AppLogo } from '@/components/icons'
import { ElMessage } from 'element-plus'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)

const form = ref({
  email: '',
  nickname: '',
  password: '',
  confirmPassword: ''
})

async function handleRegister() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) {
    return
  }
  loading.value = true
  try {
    await userApi.register({
      email: form.value.email,
      nickname: form.value.nickname,
      password: form.value.password
    })
    ElMessage.success('注册成功！请登录')
    router.push('/login')
  } catch (error) {
    if (error.response?.status === 400) {
      const detail = error.response.data?.detail
      if (detail && detail.includes('邮箱')) {
        ElMessage.error('该邮箱已被注册')
      } else {
        ElMessage.error(detail || '注册失败，请检查输入信息')
      }
    } else {
      ElMessage.error('注册失败，请检查网络连接')
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
/* ═══ Register Page — Hand-Drawn Theme ═══ */

.register-container {
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

.register-wrapper {
  width: 100%;
  max-width: 1200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 40px;
  position: relative;
  z-index: 1;
}

.register-card {
  width: 100%;
  max-width: 460px;
  padding: 0;
}
.register-card :deep(.el-card__body) {
  padding: 40px 36px 30px;
}

/* Thumbtack */
.register-card::before {
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

.register-header {
  text-align: center;
  margin-bottom: 28px;
}

.register-header h2 {
  margin: 12px 0 4px;
  font-family: var(--font-heading);
  font-size: 28px;
  font-weight: 700;
  color: var(--color-pencil);
}

.register-subtitle {
  color: #888;
  font-family: var(--font-body);
  font-size: 15px;
  margin: 0;
}

.register-btn {
  width: 100%;
  font-size: 18px !important;
  padding: 12px 0 !important;
  height: auto !important;
}

.register-footer {
  text-align: center;
  margin-top: 20px;
  font-family: var(--font-body);
  color: #888;
}

/* ── Decorative blobs ── */
.deco {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
  opacity: 0.5;
}
.deco-1 {
  width: 160px;
  height: 160px;
  top: 15%;
  left: 10%;
  border: 3px dashed var(--color-muted);
  animation: floatDeco 8s ease-in-out infinite;
}
.deco-2 {
  width: 100px;
  height: 100px;
  bottom: 20%;
  right: 12%;
  background: var(--color-yellow);
  border: 3px solid var(--color-pencil);
  animation: floatDeco 6s ease-in-out infinite reverse;
}

@keyframes floatDeco {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  33%  { transform: translateY(-12px) rotate(3deg); }
  66%  { transform: translateY(6px) rotate(-2deg); }
}
</style>
