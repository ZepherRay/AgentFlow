<template>
  <div class="login-container">
    <canvas ref="starCanvas" class="star-canvas"></canvas>
    <div class="login-card">
      <div class="brand-panel">
        <div class="brand-content">
          <div class="logo">
            <svg viewBox="0 0 40 40" width="48" height="48" fill="none">
              <path d="M20 4L36 12V28L20 36L4 28V12L20 4Z" stroke="#fff" stroke-width="2" fill="rgba(255,255,255,0.1)"/>
              <path d="M20 10L30 16V26L20 32L10 26V16L20 10Z" stroke="#60a5fa" stroke-width="2" fill="rgba(96,165,250,0.15)"/>
              <circle cx="20" cy="20" r="4" fill="#60a5fa"/>
            </svg>
            <span class="logo-text">AgentFlow</span>
          </div>
          <h2 class="brand-title">企业级AI智能体开发平台</h2>
          <p class="brand-desc">连接智能体、工作流与知识库<br/>的一站式开发平台</p>
        </div>
        <div class="brand-footer">© 2025 AgentFlow</div>
      </div>
      <div class="form-panel">
        <div class="form-content">
          <h3 class="form-title">账号注册</h3>
          <el-form ref="formRef" :model="form" :rules="rules" label-width="0">
            <el-form-item prop="username">
              <el-input v-model="form.username" placeholder="账号" size="large" prefix-icon="User" />
            </el-form-item>
            <el-form-item prop="email">
              <el-input v-model="form.email" placeholder="邮箱" size="large" prefix-icon="Message" />
            </el-form-item>
            <el-form-item prop="password">
              <el-input v-model="form.password" type="password" placeholder="密码" size="large" prefix-icon="Lock" show-password />
            </el-form-item>
            <el-form-item prop="confirmPassword">
              <el-input v-model="form.confirmPassword" type="password" placeholder="确认密码" size="large" prefix-icon="Lock" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" size="large" :loading="loading" class="login-btn" @click="handleRegister">注册</el-button>
            </el-form-item>
          </el-form>
          <div class="form-footer">
            <router-link to="/login" class="register-link">已有账号？去登录</router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api'
import { useRouter } from 'vue-router'

const router = useRouter()
const formRef = ref(null)
const starCanvas = ref(null)
const loading = ref(false)
const form = reactive({ username: '', email: '', password: '', confirmPassword: '' })

const validateConfirm = (rule, value, cb) => {
  value !== form.password ? cb(new Error('两次密码不一致')) : cb()
}

const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  email: [{ required: true, message: '请输入邮箱', trigger: 'blur' }, { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }, { min: 6, message: '密码不少于6位', trigger: 'blur' }],
  confirmPassword: [{ required: true, message: '请确认密码', trigger: 'blur' }, { validator: validateConfirm, trigger: 'blur' }]
}

async function handleRegister() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await api.auth.register(form.username, form.password, form.email, '')
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch (error) {
    ElMessage.error(error.message || '注册失败')
  } finally {
    loading.value = false
  }
}

let animId = null
const particles = []
function initStars() {
  const canvas = starCanvas.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  let w = (canvas.width = window.innerWidth)
  let h = (canvas.height = window.innerHeight)
  particles.length = 0
  for (let i = 0; i < 120; i++) {
    particles.push({ x: Math.random() * w, y: Math.random() * h, vx: (Math.random() - 0.5) * 0.6, vy: (Math.random() - 0.5) * 0.6, r: Math.random() * 2 + 1, alpha: Math.random() * 0.5 + 0.3 })
  }
  function draw() {
    ctx.clearRect(0, 0, w, h)
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x, dy = particles[i].y - particles[j].y, dist = Math.sqrt(dx * dx + dy * dy)
        if (dist < 150) { ctx.strokeStyle = `rgba(96,165,250,${(1 - dist / 150) * 0.35})`; ctx.lineWidth = 0.6; ctx.beginPath(); ctx.moveTo(particles[i].x, particles[i].y); ctx.lineTo(particles[j].x, particles[j].y); ctx.stroke() }
      }
    }
    for (const p of particles) {
      p.x += p.vx; p.y += p.vy
      if (p.x < 0 || p.x > w) p.vx *= -1; if (p.y < 0 || p.y > h) p.vy *= -1
      ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2); ctx.fillStyle = `rgba(148,190,255,${p.alpha})`; ctx.fill()
    }
    animId = requestAnimationFrame(draw)
  }
  draw()
}
onMounted(() => initStars())
onUnmounted(() => { if (animId) cancelAnimationFrame(animId) })
</script>

<style scoped>
.login-container { position: relative; display: flex; align-items: center; justify-content: center; width: 100vw; height: 100vh; background: #0a0e27; overflow: hidden; }
.star-canvas { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 0; }
.login-card { position: relative; z-index: 1; display: flex; width: 90%; max-width: 840px; height: 480px; border-radius: 16px; overflow: hidden; box-shadow: 0 20px 80px rgba(0,0,0,0.5); }
@media (max-width: 768px) { .login-card { flex-direction: column; height: auto; max-width: 420px; } }
.brand-panel { width: 420px; min-width: 280px; background: linear-gradient(135deg, rgba(30,64,175,0.85) 0%, rgba(88,28,135,0.85) 100%); backdrop-filter: blur(10px); display: flex; flex-direction: column; justify-content: space-between; padding: 48px 40px 28px; color: #fff; }
@media (max-width: 768px) { .brand-panel { width: 100%; padding: 32px 24px 20px; } }
.brand-content { flex: 1; }
.logo { display: flex; align-items: center; gap: 12px; margin-bottom: 40px; }
.logo-text { font-size: 28px; font-weight: 700; letter-spacing: 1px; }
.brand-title { font-size: 26px; font-weight: 700; margin: 0 0 16px 0; line-height: 1.4; }
.brand-desc { font-size: 15px; color: rgba(255,255,255,0.75); line-height: 1.8; margin: 0; }
.brand-footer { font-size: 13px; color: rgba(255,255,255,0.45); }
.form-panel { width: 420px; min-width: 280px; background: #fff; display: flex; align-items: center; justify-content: center; }
@media (max-width: 768px) { .form-panel { width: 100%; padding: 32px 20px; } }
.form-content { width: 300px; max-width: 100%; }
.form-title { font-size: 24px; font-weight: 700; color: #1a1a2e; margin: 0 0 36px 0; }
.login-btn { width: 100%; height: 44px; font-size: 16px; border-radius: 8px; margin-top: 4px; }
.form-footer { text-align: center; margin-top: 16px; }
.register-link { font-size: 14px; color: #409eff; text-decoration: none; }
.register-link:hover { text-decoration: underline; }
</style>
