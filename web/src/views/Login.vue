<template>
  <div class="sci-fi-login">
    <!-- Background layers -->
    <div class="nebula nebula-1"></div>
    <div class="nebula nebula-2"></div>
    <div class="nebula nebula-3"></div>
    <canvas ref="particleCanvas" class="bg-layer" id="particleCanvas"></canvas>
    <canvas ref="gridCanvas" class="bg-layer" id="gridCanvas"></canvas>
    <div class="vignette"></div>
    <div class="scanlines"></div>

    <!-- HUD Corners -->
    <div class="hud-corner tl"></div>
    <div class="hud-corner tr"></div>
    <div class="hud-corner bl"></div>
    <div class="hud-corner br"></div>

    <!-- Top Status Bar -->
    <div class="status-bar">
      <span class="status-dot"></span>
      <span>SYSTEM ONLINE</span>
      <span class="status-divider"></span>
      <span>NEURAL LINK: <span id="latency">12ms</span></span>
      <span class="status-divider"></span>
      <span id="clock">{{ clock }}</span>
    </div>

    <!-- Main Auth Card -->
    <div class="auth-wrapper">
      <div class="auth-card">

        <!-- LEFT: Brand Panel -->
        <div class="brand-panel">
          <div class="brand-top">
            <div class="logo-wrap">
              <div class="logo-orb">
                <svg class="ring-1" viewBox="0 0 52 52" fill="none">
                  <circle cx="26" cy="26" r="24" stroke="rgba(0,240,255,0.3)" stroke-width="1" stroke-dasharray="3 6"/>
                  <circle cx="26" cy="2" r="2" fill="#00f0ff"/>
                </svg>
                <svg class="ring-2" viewBox="0 0 52 52" fill="none">
                  <ellipse cx="26" cy="26" rx="22" ry="10" stroke="rgba(177,78,255,0.25)" stroke-width="1" transform="rotate(45 26 26)"/>
                  <ellipse cx="26" cy="26" rx="22" ry="10" stroke="rgba(0,240,255,0.15)" stroke-width="1" transform="rotate(-45 26 26)"/>
                </svg>
                <div class="logo-core"></div>
              </div>
              <span class="logo-text">AgentFlow</span>
            </div>

            <h1 class="brand-title">
              <span class="glitch" data-text="智能体开发平台">智能体开发平台</span>
            </h1>
            <p class="brand-desc">连接智能体、工作流与知识库<br>构建下一代 AI 应用的中枢神经</p>
          </div>

          <div class="feature-list">
            <div class="feature-item">
              <div class="feature-icon fi-cyan">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
              </div>
              <div class="feature-info">
                <div class="feature-title">可视化工作流编排</div>
                <div class="feature-sub">8 NODE TYPES · DRAG &amp; DROP</div>
              </div>
            </div>
            <div class="feature-item">
              <div class="feature-icon fi-violet">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
              </div>
              <div class="feature-info">
                <div class="feature-title">智能知识库引擎</div>
                <div class="feature-sub">RAG · GRAPH RAG · VECTOR</div>
              </div>
            </div>
            <div class="feature-item">
              <div class="feature-icon fi-magenta">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
              </div>
              <div class="feature-info">
                <div class="feature-title">多模型智能体调度</div>
                <div class="feature-sub">QWEN · DEEPSEEK · SSE STREAM</div>
              </div>
            </div>
          </div>

          <div class="brand-footer">© 2025 AgentFlow · NEXUS PROTOCOL v3.1</div>
        </div>

        <!-- RIGHT: Form Panel -->
        <div class="form-panel">
          <div class="panel-hud">
            <span>AUTH MODULE</span>
            <span class="hud-dot"></span>
          </div>

          <div class="form-header">
            <div class="form-mode-tabs">
              <div class="mode-indicator" :class="{ right: mode === 'register' }"></div>
              <div class="mode-tab" :class="{ active: mode === 'login' }" @click="mode = 'login'">登 录</div>
              <div class="mode-tab" :class="{ active: mode === 'register' }" @click="mode = 'register'">注 册</div>
            </div>

            <h2 class="form-title">{{ mode === 'login' ? '欢迎回来' : '创建新账号' }}</h2>
            <p class="form-subtitle">{{ mode === 'login' ? '// ACCESS YOUR NEURAL WORKSPACE' : '// INITIALIZE NEW NEURAL PROFILE' }}</p>
          </div>

          <!-- Login Form -->
          <form class="form-fields" @submit.prevent="handleLogin" v-show="mode === 'login'">
            <div class="field-group" v-if="loginError">
              <div class="field-error">{{ loginError }}</div>
            </div>
            <div class="field-group">
              <label class="field-label">用户名 <span class="req">*</span></label>
              <div class="field-input-wrap">
                <span class="field-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                </span>
                <input type="text" class="field-input" placeholder="输入您的账号" autocomplete="username" v-model="loginForm.username">
              </div>
            </div>

            <div class="field-group">
              <label class="field-label">密码 <span class="req">*</span></label>
              <div class="field-input-wrap">
                <span class="field-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                </span>
                <input :type="loginPwVisible ? 'text' : 'password'" class="field-input" placeholder="至少 6 位字符" autocomplete="current-password" v-model="loginForm.password">
                <button type="button" class="pw-toggle" @click="loginPwVisible = !loginPwVisible">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                </button>
              </div>
            </div>

            <button type="submit" class="btn-submit" :class="{ loading: loginLoading }">
              <span>
                <span class="btn-text">{{ loginLoading ? '正在连接...' : '启 动 连 接' }}</span>
                <svg class="btn-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                <span class="spinner"></span>
              </span>
            </button>
          </form>

          <!-- Register Form -->
          <form class="form-fields" @submit.prevent="handleRegister" v-show="mode === 'register'">
            <div class="field-group" v-if="registerError">
              <div class="field-error">{{ registerError }}</div>
            </div>
            <div class="field-group">
              <label class="field-label">用户名 <span class="req">*</span></label>
              <div class="field-input-wrap">
                <span class="field-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                </span>
                <input type="text" class="field-input" placeholder="设定账号名" v-model="registerForm.username">
              </div>
            </div>

            <div class="field-group">
              <label class="field-label">邮箱 <span class="req">*</span></label>
              <div class="field-input-wrap">
                <span class="field-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
                </span>
                <input type="email" class="field-input" placeholder="your@email.com" v-model="registerForm.email">
              </div>
            </div>

            <div class="field-group">
              <label class="field-label">密码 <span class="req">*</span></label>
              <div class="field-input-wrap">
                <span class="field-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                </span>
                <input :type="regPwVisible ? 'text' : 'password'" class="field-input" placeholder="至少 6 位字符" v-model="registerForm.password">
                <button type="button" class="pw-toggle" @click="regPwVisible = !regPwVisible">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                </button>
              </div>
            </div>

            <div class="field-group">
              <label class="field-label">确认密码 <span class="req">*</span></label>
              <div class="field-input-wrap">
                <span class="field-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                </span>
                <input :type="regPw2Visible ? 'text' : 'password'" class="field-input" placeholder="再次输入密码" v-model="registerForm.confirmPassword">
                <button type="button" class="pw-toggle" @click="regPw2Visible = !regPw2Visible">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                </button>
              </div>
            </div>

            <button type="submit" class="btn-submit" :class="{ loading: registerLoading }">
              <span>
                <span class="btn-text">{{ registerLoading ? '正在创建...' : '创 建 账 号' }}</span>
                <svg class="btn-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                <span class="spinner"></span>
              </span>
            </button>
          </form>

          <p class="switch-mode">
            <template v-if="mode === 'login'">还没有账号？ <a href="#" @click.prevent="mode = 'register'">立即注册</a></template>
            <template v-else>已有账号？ <a href="#" @click.prevent="mode = 'login'">返回登录</a></template>
          </p>
        </div>

      </div>
    </div>

    <!-- Bottom Terminal -->
    <div class="terminal-bar">
      <span class="term-prefix">agentflow@nexus:~$</span>
      <span class="terminal-text" ref="terminalText">{{ terminalText }}</span>
      <span class="terminal-cursor"></span>
      <div class="term-stats">
        <span class="term-stat">CPU <span class="val">2%</span></span>
        <span class="term-stat">MEM <span class="val">128MB</span></span>
        <span class="term-stat">NET <span class="val">●</span></span>
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
const particleCanvas = ref(null)
const gridCanvas = ref(null)

// Mode
const mode = ref('login')

// Login form
const loginForm = reactive({ username: '', password: '' })
const loginLoading = ref(false)
const loginError = ref('')
const loginPwVisible = ref(false)

// Register form
const registerForm = reactive({ username: '', email: '', password: '', confirmPassword: '' })
const registerLoading = ref(false)
const registerError = ref('')
const regPwVisible = ref(false)
const regPw2Visible = ref(false)

// Clock
const clock = ref('')
let clockInterval = null

// Terminal
const terminalText = ref('')
const termMessages = [
  'Initializing authentication protocol... Neural link established. Awaiting credentials.',
  'Loading neural models: qwen-max, deepseek-v3... Ready.',
  'Knowledge base vector store: 12,847 chunks indexed. Graph RAG: active.',
  'Workflow engine: 8 node types loaded. SSE streaming: enabled.',
  'Security: JWT token validation active. All channels encrypted.',
]

function validateForm() {
  if (mode.value === 'login') {
    if (!loginForm.username.trim()) { loginError.value = '请输入账号'; return false }
    if (!loginForm.password) { loginError.value = '请输入密码'; return false }
    loginError.value = ''
    return true
  }
  if (!registerForm.username.trim()) { registerError.value = '请输入账号'; return false }
  if (!registerForm.email.trim()) { registerError.value = '请输入邮箱'; return false }
  if (!registerForm.password) { registerError.value = '请输入密码'; return false }
  if (registerForm.password.length < 6) { registerError.value = '密码不少于6位'; return false }
  if (registerForm.password !== registerForm.confirmPassword) { registerError.value = '两次密码不一致'; return false }
  registerError.value = ''
  return true
}

async function handleLogin() {
  if (!validateForm()) return
  loginLoading.value = true
  try {
    const res = await api.auth.login(loginForm.username, loginForm.password)
    api.setToken(res.data.access_token)
    ElMessage.success('登录成功')
    router.push('/home')
  } catch (error) {
    loginError.value = error.message || '登录失败'
  } finally {
    loginLoading.value = false
  }
}

async function handleRegister() {
  if (!validateForm()) return
  registerLoading.value = true
  try {
    await api.auth.register(registerForm.username, registerForm.password, registerForm.email, '')
    ElMessage.success('注册成功，请登录')
    mode.value = 'login'
    registerForm.username = ''
    registerForm.email = ''
    registerForm.password = ''
    registerForm.confirmPassword = ''
  } catch (error) {
    registerError.value = error.message || '注册失败'
  } finally {
    registerLoading.value = false
  }
}

/* ==================== PARTICLE NETWORK ==================== */
let pAnimId = null
let gAnimId = null

function initParticles() {
  const canvas = particleCanvas.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  let pw = canvas.width = window.innerWidth
  let ph = canvas.height = window.innerHeight

  const PARTICLES = []
  const P_COUNT = Math.min(100, Math.floor(window.innerWidth / 16))
  const P_MAX_DIST = 160
  for (let i = 0; i < P_COUNT; i++) {
    PARTICLES.push({
      x: Math.random() * pw, y: Math.random() * ph,
      vx: (Math.random() - 0.5) * 0.4, vy: (Math.random() - 0.5) * 0.4,
      r: Math.random() * 1.8 + 0.6,
      a: Math.random() * 0.4 + 0.2,
      hue: Math.random() > 0.7 ? '177,78,255' : '0,240,255'
    })
  }

  let mouseX = pw / 2, mouseY = ph / 2
  const onMouseMove = (e) => { mouseX = e.clientX; mouseY = e.clientY }
  window.addEventListener('mousemove', onMouseMove)

  function draw() {
    ctx.clearRect(0, 0, pw, ph)
    for (let i = 0; i < PARTICLES.length; i++) {
      const p = PARTICLES[i]
      for (let j = i + 1; j < PARTICLES.length; j++) {
        const q = PARTICLES[j]
        const dx = p.x - q.x, dy = p.y - q.y
        const dist = Math.sqrt(dx * dx + dy * dy)
        if (dist < P_MAX_DIST) {
          const alpha = (1 - dist / P_MAX_DIST) * 0.15
          ctx.strokeStyle = `rgba(${p.hue},${alpha})`
          ctx.lineWidth = 0.5
          ctx.beginPath()
          ctx.moveTo(p.x, p.y)
          ctx.lineTo(q.x, q.y)
          ctx.stroke()
        }
      }
      const mdx = p.x - mouseX, mdy = p.y - mouseY
      const mdist = Math.sqrt(mdx * mdx + mdy * mdy)
      if (mdist < 200) {
        const force = (1 - mdist / 200) * 0.5
        p.x -= mdx / mdist * force * 0.5
        p.y -= mdy / mdist * force * 0.5
        ctx.strokeStyle = `rgba(0,240,255,${(1 - mdist / 200) * 0.3})`
        ctx.lineWidth = 0.6
        ctx.beginPath()
        ctx.moveTo(p.x, p.y)
        ctx.lineTo(mouseX, mouseY)
        ctx.stroke()
      }
      p.x += p.vx; p.y += p.vy
      if (p.x < 0 || p.x > pw) p.vx *= -1
      if (p.y < 0 || p.y > ph) p.vy *= -1
      ctx.beginPath()
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(${p.hue},${p.a})`
      ctx.fill()
    }
    pAnimId = requestAnimationFrame(draw)
  }
  draw()

  const onResize = () => {
    pw = canvas.width = window.innerWidth
    ph = canvas.height = window.innerHeight
  }
  window.addEventListener('resize', onResize)
}

/* ==================== PERSPECTIVE GRID ==================== */
function initGrid() {
  const canvas = gridCanvas.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  let gw = canvas.width = window.innerWidth
  let gh = canvas.height = window.innerHeight
  let gridOffset = 0

  function draw() {
    ctx.clearRect(0, 0, gw, gh)
    const horizon = gh * 0.35
    const vanishX = gw / 2
    const gridSize = 50
    const numLines = 30

    for (let i = 0; i < numLines; i++) {
      const t = (i + gridOffset / gridSize) / numLines
      if (t <= 0 || t >= 1) continue
      const y = horizon + (gh - horizon) * t * t
      const alpha = t * 0.12
      ctx.strokeStyle = `rgba(0,240,255,${alpha})`
      ctx.lineWidth = 1
      ctx.beginPath()
      ctx.moveTo(0, y)
      ctx.lineTo(gw, y)
      ctx.stroke()
    }
    for (let i = -15; i <= 15; i++) {
      const xEnd = vanishX + i * gw / 8
      const alpha = 0.06 * (1 - Math.abs(i) / 15)
      ctx.strokeStyle = `rgba(0,240,255,${alpha})`
      ctx.lineWidth = 0.8
      ctx.beginPath()
      ctx.moveTo(vanishX, horizon)
      ctx.lineTo(xEnd, gh)
      ctx.stroke()
    }
    const grad = ctx.createLinearGradient(0, horizon - 30, 0, horizon + 30)
    grad.addColorStop(0, 'rgba(0,240,255,0)')
    grad.addColorStop(0.5, 'rgba(0,240,255,0.08)')
    grad.addColorStop(1, 'rgba(0,240,255,0)')
    ctx.fillStyle = grad
    ctx.fillRect(0, horizon - 30, gw, 60)

    gridOffset = (gridOffset + 0.5) % gridSize
    gAnimId = requestAnimationFrame(draw)
  }
  draw()

  const onResize = () => {
    gw = canvas.width = window.innerWidth
    gh = canvas.height = window.innerHeight
  }
  window.addEventListener('resize', onResize)
}

/* ==================== TERMINAL TYPING ==================== */
let termTimer = null
function typeTerminal(text, idx) {
  terminalText.value = ''
  let i = 0
  const interval = setInterval(() => {
    if (i < text.length) {
      terminalText.value = text.substring(0, i + 1)
      i++
    } else {
      clearInterval(interval)
      termTimer = setTimeout(() => {
        const next = (idx + 1) % termMessages.length
        typeTerminal(termMessages[next], next)
      }, 4000)
    }
  }, 25)
}

onMounted(() => {
  initParticles()
  initGrid()
  typeTerminal(termMessages[0], 0)

  clockInterval = setInterval(() => {
    const d = new Date()
    clock.value = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}`
  }, 1000)
})

onUnmounted(() => {
  if (pAnimId) cancelAnimationFrame(pAnimId)
  if (gAnimId) cancelAnimationFrame(gAnimId)
  if (termTimer) clearTimeout(termTimer)
  if (clockInterval) clearInterval(clockInterval)
})
</script>

<style scoped>
/* ────────────── SCI-FI LOGIN THEME ────────────── */
.sci-fi-login {
  --neon-cyan: #00f0ff;
  --neon-violet: #b14eff;
  --neon-magenta: #ff2e97;
  --neon-green: #00ff9d;
  --neon-amber: #ffb800;
  --bg-deep: #030608;
  --sf-surface: rgba(10,16,30,0.65);
  --sf-border: rgba(0,240,255,0.15);
  --sf-border-active: rgba(0,240,255,0.45);
  --glow-cyan: 0 0 20px rgba(0,240,255,0.35);
  --glow-violet: 0 0 20px rgba(177,78,255,0.35);
  --sf-mono: 'SF Mono','Fira Code','Cascadia Code','Consolas',monospace;
  --sf-font: -apple-system,'SF Pro Display','Segoe UI',system-ui,'PingFang SC','Microsoft YaHei',sans-serif;
  --t-1: rgba(255,255,255,0.92);
  --t-2: rgba(255,255,255,0.60);
  --t-3: rgba(255,255,255,0.32);

  position: fixed;inset:0;z-index:2000;
  background:#050810;font-family:var(--sf-font);color:var(--t-1);
  overflow:hidden;
}

/* ── Background layers ── */
.bg-layer{position:fixed;inset:0;pointer-events:none}
#particleCanvas{z-index:1}
#gridCanvas{z-index:2;opacity:0.4}

.nebula{position:fixed;border-radius:50%;filter:blur(80px);z-index:0;pointer-events:none}
.nebula-1{width:600px;height:600px;background:radial-gradient(circle,rgba(0,240,255,0.12),transparent 70%);top:-150px;left:-150px;animation:drift1 20s ease-in-out infinite}
.nebula-2{width:500px;height:500px;background:radial-gradient(circle,rgba(177,78,255,0.10),transparent 70%);bottom:-100px;right:-100px;animation:drift2 25s ease-in-out infinite}
.nebula-3{width:400px;height:400px;background:radial-gradient(circle,rgba(255,46,151,0.06),transparent 70%);top:50%;left:50%;transform:translate(-50%,-50%);animation:drift3 18s ease-in-out infinite}
@keyframes drift1{0%,100%{transform:translate(0,0)scale(1)}50%{transform:translate(60px,40px)scale(1.1)}}
@keyframes drift2{0%,100%{transform:translate(0,0)scale(1)}50%{transform:translate(-50px,-30px)scale(1.15)}}
@keyframes drift3{0%,100%{transform:translate(-50%,-50%)scale(1)}50%{transform:translate(-45%,-55%)scale(1.2)}}

.scanlines{position:fixed;inset:0;z-index:50;pointer-events:none;
  background:repeating-linear-gradient(0deg,transparent 0,transparent 2px,rgba(0,240,255,0.015) 2px,rgba(0,240,255,0.015) 4px);
}
.scanlines::after{content:'';position:absolute;left:0;right:0;height:120px;
  background:linear-gradient(180deg,transparent,rgba(0,240,255,0.04),rgba(0,240,255,0.06),rgba(0,240,255,0.04),transparent);
  animation:scanMove 8s linear infinite}
@keyframes scanMove{0%{top:-120px}100%{top:100%}}

.vignette{position:fixed;inset:0;z-index:3;pointer-events:none;
  background:radial-gradient(ellipse at center,transparent 30%,rgba(3,6,8,0.7) 100%)}

/* ── HUD Corners ── */
.hud-corner{position:fixed;width:60px;height:60px;z-index:60;pointer-events:none}
.hud-corner::before,.hud-corner::after{content:'';position:absolute;background:var(--neon-cyan);box-shadow:var(--glow-cyan)}
.hud-corner.tl{top:20px;left:20px}
.hud-corner.tl::before{top:0;left:0;width:2px;height:24px}
.hud-corner.tl::after{top:0;left:0;width:24px;height:2px}
.hud-corner.tr{top:20px;right:20px}
.hud-corner.tr::before{top:0;right:0;width:2px;height:24px}
.hud-corner.tr::after{top:0;right:0;width:24px;height:2px}
.hud-corner.bl{bottom:20px;left:20px}
.hud-corner.bl::before{bottom:0;left:0;width:2px;height:24px}
.hud-corner.bl::after{bottom:0;left:0;width:24px;height:2px}
.hud-corner.br{bottom:20px;right:20px}
.hud-corner.br::before{bottom:0;right:0;width:2px;height:24px}
.hud-corner.br::after{bottom:0;right:0;width:24px;height:2px}

/* ── Status Bar ── */
.status-bar{position:fixed;top:24px;left:50%;transform:translateX(-50%);z-index:55;
  display:flex;align-items:center;gap:16px;padding:6px 20px;
  background:rgba(5,8,16,0.7);backdrop-filter:blur(12px);
  border:1px solid var(--sf-border);border-radius:100px;
  font-family:var(--sf-mono);font-size:11px;color:var(--t-2);letter-spacing:0.5px}
.status-dot{width:7px;height:7px;border-radius:50%;background:var(--neon-green);box-shadow:0 0 8px var(--neon-green);animation:pulse 2s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.4}}
.status-divider{width:1px;height:12px;background:var(--sf-border)}

/* ── Auth Card ── */
.auth-wrapper{position:relative;z-index:10;width:100%;height:100%;display:flex;align-items:center;justify-content:center;padding:20px}
.auth-card{
  position:relative;width:920px;max-width:100%;height:560px;
  display:flex;border-radius:20px;overflow:hidden;
  background:var(--sf-surface);backdrop-filter:blur(24px);
  border:1px solid var(--sf-border);
  box-shadow:0 0 0 1px rgba(0,240,255,0.05),0 30px 100px rgba(0,0,0,0.6),inset 0 1px 0 rgba(255,255,255,0.05);
  animation:cardIn 0.8s cubic-bezier(0.16,1,0.3,1) both;
}
@keyframes cardIn{0%{opacity:0;transform:scale(0.92)translateY(20px)}100%{opacity:1;transform:scale(1)translateY(0)}}
.auth-card::before{
  content:'';position:absolute;inset:-1px;border-radius:20px;padding:1px;z-index:-1;
  background:conic-gradient(from var(--angle,0deg),transparent 0%,transparent 40%,rgba(0,240,255,0.5) 50%,transparent 60%,transparent 100%);
  -webkit-mask:linear-gradient(#000 0 0)content-box,linear-gradient(#000 0 0);
  -webkit-mask-composite:xor;mask-composite:exclude;
  animation:rotateBorder 6s linear infinite;
}
@property --angle{syntax:'<angle>';initial-value:0deg;inherits:false}
@keyframes rotateBorder{to{--angle:360deg}}

/* ── Brand Panel ── */
.brand-panel{
  position:relative;width:440px;flex-shrink:0;padding:48px 40px;
  display:flex;flex-direction:column;justify-content:space-between;
  background:linear-gradient(135deg,rgba(0,240,255,0.04),rgba(177,78,255,0.06));
  border-right:1px solid var(--sf-border);
}
.brand-panel::before{
  content:'';position:absolute;inset:0;opacity:0.5;pointer-events:none;
  background-image:linear-gradient(rgba(0,240,255,0.03) 1px,transparent 1px),linear-gradient(90deg,rgba(0,240,255,0.03) 1px,transparent 1px);
  background-size:20px 20px;
}
.brand-top{position:relative;z-index:1}
.logo-wrap{display:flex;align-items:center;gap:14px;margin-bottom:36px}
.logo-orb{position:relative;width:52px;height:52px;flex-shrink:0}
.logo-orb svg{position:absolute;inset:0}
.ring-1{animation:spin 8s linear infinite}
.ring-2{animation:spin 12s linear infinite reverse}
@keyframes spin{to{transform:rotate(360deg)}}
.logo-core{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:14px;height:14px;border-radius:50%;background:var(--neon-cyan);box-shadow:0 0 20px var(--neon-cyan),0 0 40px rgba(0,240,255,0.4);animation:corePulse 3s ease-in-out infinite}
@keyframes corePulse{0%,100%{transform:translate(-50%,-50%)scale(1);box-shadow:0 0 20px var(--neon-cyan),0 0 40px rgba(0,240,255,0.4)}50%{transform:translate(-50%,-50%)scale(1.3);box-shadow:0 0 28px var(--neon-cyan),0 0 56px rgba(0,240,255,0.6)}}
.logo-text{font-size:26px;font-weight:800;letter-spacing:2px;
  background:linear-gradient(135deg,#fff,rgba(0,240,255,0.8));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}

.brand-title{font-size:30px;font-weight:700;line-height:1.35;margin-bottom:14px}
.brand-title .glitch{position:relative;display:inline-block}
.brand-title .glitch::before,.brand-title .glitch::after{
  content:attr(data-text);position:absolute;top:0;left:0;width:100%;
  background:var(--sf-bg, #050810);overflow:hidden}
.brand-title .glitch::before{color:var(--neon-magenta);clip-path:polygon(0 0,100% 0,100% 33%,0 33%);animation:glitchTop 4s steps(1) infinite}
.brand-title .glitch::after{color:var(--neon-cyan);clip-path:polygon(0 67%,100% 67%,100% 100%,0 100%);animation:glitchBot 4s steps(1) infinite}
@keyframes glitchTop{0%,90%,100%{transform:translate(0)}92%{transform:translate(-2px,-1px)}94%{transform:translate(2px,1px)}96%{transform:translate(-1px,1px)}}
@keyframes glitchBot{0%,90%,100%{transform:translate(0)}93%{transform:translate(2px,1px)}95%{transform:translate(-2px,-1px)}97%{transform:translate(1px,-1px)}}
.brand-desc{font-size:14px;line-height:1.8;color:var(--t-2);max-width:340px}

.feature-list{position:relative;z-index:1;display:flex;flex-direction:column;gap:14px;margin-top:8px}
.feature-item{display:flex;align-items:center;gap:12px;padding:10px 14px;
  background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.08);border-radius:10px;
  transition:all 0.3s ease}
.feature-item:hover{background:rgba(0,240,255,0.06);border-color:rgba(0,240,255,0.2);transform:translateX(4px)}
.feature-icon{width:32px;height:32px;border-radius:8px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.feature-icon svg{width:18px;height:18px}
.fi-cyan{background:rgba(0,240,255,0.1);color:var(--neon-cyan)}
.fi-violet{background:rgba(177,78,255,0.1);color:var(--neon-violet)}
.fi-magenta{background:rgba(255,46,151,0.1);color:var(--neon-magenta)}
.feature-info{flex:1}
.feature-title{font-size:13px;font-weight:600;color:var(--t-1)}
.feature-sub{font-size:11px;color:var(--t-3);font-family:var(--sf-mono)}
.brand-footer{position:relative;z-index:1;font-size:11px;color:var(--t-3);font-family:var(--sf-mono);letter-spacing:0.5px}

/* ── Form Panel ── */
.form-panel{flex:1;padding:48px 56px;display:flex;flex-direction:column;justify-content:center;position:relative}
.panel-hud{position:absolute;top:24px;right:32px;display:flex;align-items:center;gap:8px;
  font-family:var(--sf-mono);font-size:10px;color:var(--t-3);letter-spacing:1px}
.panel-hud .hud-dot{width:6px;height:6px;border-radius:50%;background:var(--neon-cyan);box-shadow:0 0 6px var(--neon-cyan)}

.form-header{margin-bottom:36px}
.form-mode-tabs{display:flex;gap:0;margin-bottom:24px;background:rgba(0,0,0,0.3);border-radius:10px;padding:3px;border:1px solid rgba(255,255,255,0.04);position:relative}
.mode-tab{flex:1;padding:9px 0;text-align:center;font-size:13px;font-weight:600;color:var(--t-3);
  border-radius:8px;cursor:pointer;transition:all 0.3s ease;position:relative;z-index:1}
.mode-tab.active{color:var(--neon-cyan)}
.mode-indicator{position:absolute;top:3px;left:3px;width:calc(50% - 3px);height:calc(100% - 6px);
  background:rgba(0,240,255,0.08);border:1px solid rgba(0,240,255,0.2);border-radius:8px;
  transition:transform 0.35s cubic-bezier(0.4,0,0.2,1);box-shadow:inset 0 0 20px rgba(0,240,255,0.05)}
.mode-indicator.right{transform:translateX(calc(100% + 3px))}

.form-title{font-size:22px;font-weight:700;margin-bottom:6px}
.form-subtitle{font-size:13px;color:var(--t-3);font-family:var(--sf-mono);letter-spacing:0.3px}

.form-fields{display:flex;flex-direction:column;gap:18px}
.field-group{position:relative}
.field-label{display:block;font-size:11px;font-weight:600;color:var(--t-2);letter-spacing:1.5px;
  text-transform:uppercase;margin-bottom:8px;font-family:var(--sf-mono)}
.field-label .req{color:var(--neon-magenta)}
.field-input-wrap{position:relative}
.field-icon{position:absolute;left:14px;top:50%;transform:translateY(-50%);z-index:1;color:var(--t-3);transition:color 0.3s}
.field-icon svg{width:16px;height:16px;display:block}
.field-input{
  width:100%;padding:12px 14px 12px 42px;font-size:14px;font-family:var(--sf-font);
  background:rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.08);border-radius:10px;
  color:var(--t-1);outline:none;transition:all 0.3s ease;
}
.field-input::placeholder{color:var(--t-3)}
.field-input:focus{border-color:var(--sf-border-active);background:rgba(0,240,255,0.03);box-shadow:0 0 0 3px rgba(0,240,255,0.08),inset 0 0 20px rgba(0,240,255,0.02)}
.field-input-wrap:focus-within .field-icon{color:var(--neon-cyan)}
.field-input-wrap::after{content:'';position:absolute;bottom:0;left:50%;width:0;height:1px;
  background:linear-gradient(90deg,transparent,var(--neon-cyan),transparent);
  transition:width 0.4s ease,left 0.4s ease}
.field-input-wrap:focus-within::after{width:100%;left:0}

.pw-toggle{position:absolute;right:12px;top:50%;transform:translateY(-50%);background:none;border:none;
  color:var(--t-3);cursor:pointer;padding:4px;display:flex;align-items:center}
.pw-toggle:hover{color:var(--t-2)}
.pw-toggle svg{width:16px;height:16px}

.field-error{background:rgba(255,46,151,0.1);border:1px solid rgba(255,46,151,0.2);border-radius:8px;padding:10px 14px;font-size:12px;color:var(--neon-magenta);font-family:var(--sf-mono);margin-bottom:4px}

.btn-submit{
  position:relative;width:100%;padding:13px;margin-top:6px;font-size:14px;font-weight:700;
  font-family:var(--sf-font);letter-spacing:1px;
  background:linear-gradient(135deg,rgba(0,240,255,0.15),rgba(177,78,255,0.15));
  border:1px solid rgba(0,240,255,0.3);border-radius:10px;color:var(--t-1);
  cursor:pointer;overflow:hidden;transition:all 0.3s ease;
}
.btn-submit::before{content:'';position:absolute;inset:0;
  background:linear-gradient(135deg,rgba(0,240,255,0.3),rgba(177,78,255,0.3));opacity:0;transition:opacity 0.3s}
.btn-submit:hover{border-color:var(--neon-cyan);box-shadow:0 0 24px rgba(0,240,255,0.3),inset 0 0 20px rgba(0,240,255,0.1);transform:translateY(-1px)}
.btn-submit:hover::before{opacity:1}
.btn-submit:active{transform:translateY(0)}
.btn-submit span{position:relative;z-index:1;display:flex;align-items:center;justify-content:center;gap:8px}
.btn-submit::after{content:'';position:absolute;top:0;left:-100%;width:60%;height:100%;
  background:linear-gradient(90deg,transparent,rgba(255,255,255,0.1),transparent);
  transition:left 0.6s ease}
.btn-submit:hover::after{left:120%}
.btn-submit.loading{pointer-events:none;opacity:0.7}
.btn-submit.loading span{opacity:0.6}
.btn-submit .spinner{width:16px;height:16px;border:2px solid rgba(255,255,255,0.2);border-top-color:var(--neon-cyan);border-radius:50%;animation:spin 0.8s linear infinite;display:none}
.btn-submit.loading .spinner{display:block}
.btn-submit.loading .btn-arrow{display:none}

.switch-mode{text-align:center;margin-top:20px;font-size:13px;color:var(--t-3)}
.switch-mode a{color:var(--neon-cyan);text-decoration:none;font-weight:600;transition:all 0.2s}
.switch-mode a:hover{text-shadow:var(--glow-cyan)}

/* ── Terminal Bar ── */
.terminal-bar{position:fixed;bottom:0;left:0;right:0;z-index:55;height:32px;
  display:flex;align-items:center;gap:12px;padding:0 24px;
  background:rgba(3,6,8,0.8);backdrop-filter:blur(12px);border-top:1px solid var(--sf-border);
  font-family:var(--sf-mono);font-size:10px;color:var(--t-3);letter-spacing:0.5px;overflow:hidden}
.terminal-bar .term-prefix{color:var(--neon-green)}
.terminal-text{flex:1;white-space:nowrap;overflow:hidden;
  mask:linear-gradient(90deg,transparent,#000 5%,#000 95%,transparent)}
.terminal-cursor{display:inline-block;width:7px;height:12px;background:var(--neon-cyan);animation:blink 1s steps(1) infinite;vertical-align:middle}
@keyframes blink{50%{opacity:0}}
.term-stats{display:flex;gap:16px;flex-shrink:0}
.term-stat{display:flex;align-items:center;gap:4px}
.term-stat .val{color:var(--neon-cyan)}

/* ── Responsive ── */
@media(max-width:820px){
  .auth-card{flex-direction:column;width:94%;height:auto;max-height:92vh;overflow-y:auto}
  .brand-panel{width:100%;padding:32px 24px;border-right:none;border-bottom:1px solid var(--sf-border)}
  .brand-title{font-size:24px}
  .feature-list{display:none}
  .form-panel{padding:32px 24px;min-height:400px}
}
@media(max-width:480px){
  .status-bar{font-size:10px;gap:10px;padding:5px 14px}
  .hud-corner{width:40px;height:40px}
  .brand-panel{padding:24px 20px}
  .logo-text{font-size:22px}
  .brand-title{font-size:20px}
  .brand-desc{font-size:13px}
  .form-panel{padding:28px 20px}
  .terminal-bar{font-size:9px}
  .term-stats{display:none}
}
</style>
