<template>
  <div class="login-page">
    <StarryBackground />
    <div class="login-wrapper">
      <div class="brand-section">
        <div class="brand-logo">
          <svg viewBox="0 0 48 48" fill="none">
            <path d="M24 4L40 20V28L24 44L8 28V20L24 4Z" fill="url(#gradient)" />
            <path d="M24 12L36 22V26L24 36L12 26V22L24 12Z" fill="white" opacity="0.9" />
            <defs>
              <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#409eff" />
                <stop offset="100%" style="stop-color:#7c3aed" />
              </linearGradient>
            </defs>
          </svg>
        </div>
        <h1 class="brand-name">AgentFlow</h1>
        <h2 class="brand-title">企业级AI智能体开发平台</h2>
        <p class="brand-desc">企业级智能体、工作流与知识库</p>
        <p class="brand-sub">连接智能体、工作流与知识库的一站式开发平台</p>
        <div class="brand-features">
          <div class="feature-item">
            <el-icon :size="20"><Cpu /></el-icon>
            <span>智能体开发</span>
          </div>
          <div class="feature-item">
            <el-icon :size="20"><GitBranch /></el-icon>
            <span>工作流编排</span>
          </div>
          <div class="feature-item">
            <el-icon :size="20"><Database /></el-icon>
            <span>知识库管理</span>
          </div>
        </div>
      </div>
      <div class="form-section">
        <div class="form-card">
          <div class="form-header">
            <h3>账号登录</h3>
          </div>
          <div class="tab-switch">
            <span :class="{ active: mode === 'login' }" @click="switchMode('login')">登录</span>
            <span :class="{ active: mode === 'register' }" @click="switchMode('register')">注册</span>
          </div>
          <el-form v-if="mode === 'login'" ref="loginFormRef" :model="loginForm" :rules="loginRules" label-width="0">
            <el-form-item prop="username">
              <el-input v-model="loginForm.username" placeholder="账号" size="large" prefix-icon="User" />
            </el-form-item>
            <el-form-item prop="password">
              <el-input v-model="loginForm.password" type="password" placeholder="密码" size="large" prefix-icon="Lock" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" size="large" :loading="loading" @click="handleLogin" style="width: 100%">登 录</el-button>
            </el-form-item>
          </el-form>
          <el-form v-else ref="registerFormRef" :model="registerForm" :rules="registerRules" label-width="0">
            <el-form-item prop="username">
              <el-input v-model="registerForm.username" placeholder="用户名" size="large" prefix-icon="User" />
            </el-form-item>
            <el-form-item prop="email">
              <el-input v-model="registerForm.email" placeholder="邮箱" size="large" prefix-icon="Message" />
            </el-form-item>
            <el-form-item prop="nickname">
              <el-input v-model="registerForm.nickname" placeholder="昵称（选填）" size="large" prefix-icon="Avatar" />
            </el-form-item>
            <el-form-item prop="password">
              <el-input v-model="registerForm.password" type="password" placeholder="密码" size="large" prefix-icon="Lock" show-password />
            </el-form-item>
            <el-form-item prop="confirmPassword">
              <el-input v-model="registerForm.confirmPassword" type="password" placeholder="确认密码" size="large" prefix-icon="Lock" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" size="large" :loading="loading" @click="handleRegister" style="width: 100%">注 册</el-button>
            </el-form-item>
          </el-form>
          <div class="other-login">
            <span>其它登录:</span>
            <el-button type="text" size="small" disabled><el-icon><Message /></el-icon>短信登录</el-button>
          </div>
          <div class="copyright">
            © 2025 AgentFlow
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Cpu, GitBranch, Database, Message } from '@element-plus/icons-vue'
import { api } from '../api'
import StarryBackground from '../components/StarryBackground.vue'

const mode = ref('login')
const loading = ref(false)
const loginFormRef = ref(null)
const registerFormRef = ref(null)

const loginForm = reactive({ username: '', password: '' })
const registerForm = reactive({
  username: '',
  email: '',
  nickname: '',
  password: '',
  confirmPassword: ''
})

const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在3-50之间', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 100, message: '密码长度在6-100之间', trigger: 'blur' }
  ]
}

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== registerForm.password) {
    callback(new Error('两次密码不一致'))
  } else {
    callback()
  }
}

const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在3-50之间', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 100, message: '密码长度在6-100之间', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

function switchMode(m) {
  mode.value = m
  loading.value = false
}

async function handleLogin() {
  await loginFormRef.value.validate()
  loading.value = true
  try {
    const res = await api.auth.login(loginForm.username, loginForm.password)
    api.setToken(res.data.access_token)
    ElMessage.success('登录成功')
    window.location.href = '/'
  } catch (error) {
    ElMessage.error(error.message || '登录失败')
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  await registerFormRef.value.validate()
  loading.value = true
  try {
    await api.auth.register(
      registerForm.username,
      registerForm.password,
      registerForm.email,
      registerForm.nickname || ''
    )
    ElMessage.success('注册成功，请登录')
    switchMode('login')
    loginForm.username = registerForm.username
    loginForm.password = ''
  } catch (error) {
    ElMessage.error(error.message || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  position: relative;
  width: 100%;
  height: 100vh;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-wrapper {
  position: relative;
  width: 900px;
  height: 500px;
  display: flex;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 25px 80px rgba(0, 0, 0, 0.4);
  z-index: 10;
}

.brand-section {
  flex: 1;
  background: linear-gradient(135deg, #409eff 0%, #7c3aed 50%, #06b6d4 100%);
  padding: 60px 40px;
  display: flex;
  flex-direction: column;
  color: #fff;
  position: relative;
  overflow: hidden;
}

.brand-section::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -50%;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, transparent 60%);
}

.brand-logo {
  width: 56px;
  height: 56px;
  margin-bottom: 20px;
}

.brand-name {
  font-size: 32px;
  font-weight: 700;
  margin: 0 0 8px 0;
  letter-spacing: 2px;
}

.brand-title {
  font-size: 18px;
  font-weight: 500;
  margin: 0 0 12px 0;
  opacity: 0.95;
}

.brand-desc {
  font-size: 14px;
  opacity: 0.85;
  margin: 0 0 8px 0;
}

.brand-sub {
  font-size: 13px;
  opacity: 0.75;
  margin: 0 0 32px 0;
  line-height: 1.6;
}

.brand-features {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  opacity: 0.9;
}

.form-section {
  flex: 1;
  background: #fff;
  padding: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.form-card {
  width: 100%;
  max-width: 320px;
}

.form-header {
  margin-bottom: 20px;
}

.form-header h3 {
  font-size: 22px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.tab-switch {
  display: flex;
  margin-bottom: 24px;
  border-bottom: 2px solid #f0f0f0;
}

.tab-switch span {
  flex: 1;
  text-align: center;
  padding: 10px 0;
  font-size: 15px;
  color: #909399;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: all 0.2s;
}

.tab-switch span.active {
  color: #409eff;
  border-bottom-color: #409eff;
  font-weight: 500;
}

.other-login {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  font-size: 13px;
  color: #909399;
}

.copyright {
  text-align: center;
  margin-top: 24px;
  font-size: 12px;
  color: #c0c4cc;
}
</style>