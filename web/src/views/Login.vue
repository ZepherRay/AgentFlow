<template>
  <div class="login-container">
    <!-- 动态星空背景 canvas -->
    <canvas ref="starCanvas" class="star-canvas"></canvas>

    <!-- 登录卡片 -->
    <div class="login-card">
      <!-- 左侧品牌区 -->
      <div class="brand-panel">
        <div class="brand-content">
          <div class="logo">
            <svg viewBox="0 0 40 40" width="48" height="48" fill="none" xmlns="http://www.w3.org/2000/svg">
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

      <!-- 右侧登录区 -->
      <div class="form-panel">
        <div class="form-content">
          <h3 class="form-title">账号登录</h3>
          <el-form
            ref="loginFormRef"
            :model="loginForm"
            :rules="loginRules"
            label-width="0"
            @keyup.enter="handleLogin"
          >
            <el-form-item prop="username">
              <el-input
                v-model="loginForm.username"
                placeholder="账号"
                size="large"
                prefix-icon="User"
              />
            </el-form-item>
            <el-form-item prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="密码"
                size="large"
                prefix-icon="Lock"
                show-password
              />
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                :loading="loading"
                class="login-btn"
                @click="handleLogin"
              >
                登录
              </el-button>
            </el-form-item>
          </el-form>
          <div class="form-footer">
            <router-link to="/register" class="register-link">注册账号</router-link>
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

const loginFormRef = ref(null)
const starCanvas = ref(null)
const loading = ref(false)

const loginForm = reactive({ username: '', password: '' })

const loginRules = {
  username: [
    { required: true, message: '请输入账号', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码不少于6位', trigger: 'blur' }
  ]
}

async function handleLogin() {
  const valid = await loginFormRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    const res = await api.auth.login(loginForm.username, loginForm.password)
    api.setToken(res.data.access_token)
    ElMessage.success('登录成功')
    window.location.href = '/home'
  } catch (error) {
    ElMessage.error(error.message || '登录失败')
  } finally {
    loading.value = false
  }
}

/* ========== 星空粒子动画 ========== */
let animId = null
const particles = []
const PARTICLE_COUNT = 120
const MAX_DIST = 150

function initStars() {
  const canvas = starCanvas.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  let w = (canvas.width = window.innerWidth)
  let h = (canvas.height = window.innerHeight)

  particles.length = 0
  for (let i = 0; i < PARTICLE_COUNT; i++) {
    particles.push({
      x: Math.random() * w,
      y: Math.random() * h,
      vx: (Math.random() - 0.5) * 0.6,
      vy: (Math.random() - 0.5) * 0.6,
      r: Math.random() * 2 + 1,
      alpha: Math.random() * 0.5 + 0.3,
    })
  }

  function draw() {
    ctx.clearRect(0, 0, w, h)
    // 连线
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x
        const dy = particles[i].y - particles[j].y
        const dist = Math.sqrt(dx * dx + dy * dy)
        if (dist < MAX_DIST) {
          const lineAlpha = (1 - dist / MAX_DIST) * 0.35
          ctx.strokeStyle = `rgba(96,165,250,${lineAlpha})`
          ctx.lineWidth = 0.6
          ctx.beginPath()
          ctx.moveTo(particles[i].x, particles[i].y)
          ctx.lineTo(particles[j].x, particles[j].y)
          ctx.stroke()
        }
      }
    }
    // 粒子
    for (const p of particles) {
      p.x += p.vx
      p.y += p.vy
      if (p.x < 0 || p.x > w) p.vx *= -1
      if (p.y < 0 || p.y > h) p.vy *= -1
      ctx.beginPath()
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(148,190,255,${p.alpha})`
      ctx.fill()
    }
    animId = requestAnimationFrame(draw)
  }
  draw()

  const onResize = () => {
    w = canvas.width = window.innerWidth
    h = canvas.height = window.innerHeight
  }
  window.addEventListener('resize', onResize)
}

onMounted(() => initStars())
onUnmounted(() => {
  if (animId) cancelAnimationFrame(animId)
})
</script>

<style scoped>
.login-container {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100vw;
  height: 100vh;
  background: #0a0e27;
  overflow: hidden;
}

.star-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
}

/* 登录卡片 */
.login-card {
  position: relative;
  z-index: 1;
  display: flex;
  width: 840px;
  height: 480px;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 20px 80px rgba(0, 0, 0, 0.5);
}

/* 左侧品牌 */
.brand-panel {
  width: 420px;
  background: linear-gradient(135deg, rgba(30, 64, 175, 0.85) 0%, rgba(88, 28, 135, 0.85) 100%);
  backdrop-filter: blur(10px);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 48px 40px 28px;
  color: #fff;
}

.brand-content {
  flex: 1;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 40px;
}

.logo-text {
  font-size: 28px;
  font-weight: 700;
  letter-spacing: 1px;
}

.brand-title {
  font-size: 26px;
  font-weight: 700;
  margin: 0 0 16px 0;
  line-height: 1.4;
}

.brand-desc {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.75);
  line-height: 1.8;
  margin: 0;
}

.brand-footer {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.45);
}

/* 右侧表单 */
.form-panel {
  width: 420px;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.form-content {
  width: 300px;
}

.form-title {
  font-size: 24px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0 0 36px 0;
}

.login-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
  border-radius: 8px;
  margin-top: 4px;
}

.form-footer {
  text-align: center;
  margin-top: 16px;
}

.register-link {
  font-size: 14px;
  color: #409eff;
  text-decoration: none;
}

.register-link:hover {
  text-decoration: underline;
}
</style>
