<template>
  <div id="app-layout">
    <el-container class="app-container">
      <el-aside class="sidebar">
        <div class="sidebar-logo">
          <div class="logo-icon">
            <svg viewBox="0 0 40 40" width="32" height="32" fill="none">
              <path d="M20 4L36 12V28L20 36L4 28V12L20 4Z" stroke="#4fc3f7" stroke-width="2" fill="rgba(79,195,247,0.1)"/>
              <path d="M20 10L30 16V26L20 32L10 26V16L20 10Z" stroke="#60a5fa" stroke-width="2" fill="rgba(96,165,250,0.15)"/>
              <circle cx="20" cy="20" r="3" fill="#60a5fa"/>
            </svg>
          </div>
          <span class="logo-text">AgentFlow</span>
        </div>
        <el-menu
          :default-active="activeMenu"
          router
          class="sidebar-menu"
          @select="handleMenuSelect"
        >
          <el-menu-item index="/home">
            <el-icon><HomeFilled /></el-icon>
            <span>首页</span>
          </el-menu-item>
          <el-menu-item index="/knowledge">
            <el-icon><Document /></el-icon>
            <span>知识库</span>
          </el-menu-item>
          <el-menu-item index="/agents">
            <el-icon><Cpu /></el-icon>
            <span>智能体</span>
          </el-menu-item>
          <el-menu-item index="/workflows">
            <el-icon><Connection /></el-icon>
            <span>工作流</span>
          </el-menu-item>
          <el-menu-item index="/profile">
            <el-icon><User /></el-icon>
            <span>个人中心</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      <el-container class="main-container">
        <el-header class="header">
          <div class="header-left">
            <span class="header-title">{{ pageTitle }}</span>
          </div>
          <div class="header-right">
            <el-dropdown @command="handleCommand">
              <span class="user-dropdown">
                <el-avatar :size="32" :src="navbarAvatarUrl" class="user-avatar">
                  <User />
                </el-avatar>
                <span class="user-name">{{ userInfo.nickname || userInfo.username }}</span>
                <el-icon class="arrow-icon"><ArrowDown /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                  <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>
        <el-main class="main-content">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowDown, HomeFilled, User, Document, Cpu, Connection } from '@element-plus/icons-vue'
import { api } from '../api'

const route = useRoute()
const router = useRouter()
const activeMenu = computed(() => {
  if (route.path.startsWith('/knowledge/')) return '/knowledge'
  return route.path
})
const userInfo = ref({})
const avatarVersion = ref(Date.now())

const navbarAvatarUrl = computed(() => {
  let url = userInfo.value.avatar
  if (!url) return ''
  if (!url.startsWith('/') && !url.startsWith('http')) {
    url = `/uploads/avatars/${url}`
  }
  return `${url}?t=${avatarVersion.value}`
})

const pageTitles = {
  '/home': '首页',
  '/knowledge': '知识库',
  '/profile': '个人中心',
  '/agents': '智能体管理',
  '/workflows': '工作流管理'
}

const pageTitle = computed(() => {
  if (pageTitles[route.path]) return pageTitles[route.path]
  if (route.path.startsWith('/knowledge/')) return '知识库详情'
  return 'AgentFlow'
})

onMounted(async () => {
  try {
    const res = await api.auth.getMe()
    userInfo.value = res.data
  } catch {
    router.push('/login')
  }
  window.addEventListener('avatar-updated', onAvatarUpdated)
})

onUnmounted(() => {
  window.removeEventListener('avatar-updated', onAvatarUpdated)
})

function onAvatarUpdated(e) {
  if (e.detail?.url) {
    userInfo.value = { ...userInfo.value, avatar: e.detail.url }
    avatarVersion.value = e.detail.ts || Date.now()
  }
}

function handleMenuSelect(index) {
  router.push(index)
}
function handleCommand(command) {
  if (command === 'profile') {
    router.push('/profile')
  } else if (command === 'logout') {
    api.logout()
    window.location.href = '/login'
  }
}
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body, #app { height: 100%; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif; }
#app-layout { height: 100%; }
.app-container { height: 100%; }
/* Force Element Plus menu to be transparent */
.sidebar-menu,
.sidebar-menu .el-menu,
.sidebar-menu > .el-menu,
.sidebar-menu .el-menu-item,
.sidebar-menu > .el-menu > .el-menu-item {
  background-color: transparent !important;
  --el-menu-bg-color: transparent !important;
  --el-menu-hover-bg-color: transparent !important;
}
</style>

<style scoped>
.sidebar { background: linear-gradient(180deg, #0c1222 0%, #0f1a3a 40%, #141b3d 70%, #1a1140 100%); overflow: hidden; border-right: 1px solid #1e2a5a; width: 250px; flex-shrink: 0; position: relative; }
.sidebar::before { content: ''; position: absolute; inset: 0; background-image: radial-gradient(1.5px 1.5px at 20px 40px, rgba(255,255,255,0.5) 0%, transparent 100%), radial-gradient(1px 1px at 60px 120px, rgba(255,255,255,0.4) 0%, transparent 100%), radial-gradient(1.5px 1.5px at 180px 60px, rgba(255,255,255,0.3) 0%, transparent 100%), radial-gradient(1px 1px at 40px 200px, rgba(255,255,255,0.4) 0%, transparent 100%), radial-gradient(1.5px 1.5px at 200px 250px, rgba(255,255,255,0.3) 0%, transparent 100%), radial-gradient(1px 1px at 120px 300px, rgba(255,255,255,0.35) 0%, transparent 100%), radial-gradient(1.5px 1.5px at 220px 180px, rgba(255,255,255,0.25) 0%, transparent 100%), radial-gradient(1px 1px at 80px 360px, rgba(255,255,255,0.3) 0%, transparent 100%); pointer-events: none; }
.sidebar-logo { height: 70px; display: flex; align-items: center; padding: 0 24px; gap: 14px; border-bottom: 1px solid #1e2a5a; position: relative; z-index: 1; }
.logo-icon { flex-shrink: 0; }
.logo-text { font-size: 20px; font-weight: 700; color: #fff; letter-spacing: 0.5px; background: linear-gradient(135deg, #4fc3f7 0%, #60a5fa 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.sidebar-menu { border-right: none; height: calc(100% - 70px); padding-top: 8px; background: transparent; }
.sidebar-menu :deep(.el-menu) { background: transparent !important; }
.sidebar-menu :deep(.el-menu-item) { height: 46px; line-height: 46px; margin: 3px 14px; border-radius: 10px; font-size: 14px; font-weight: 500; color: #94a3b8; background: transparent !important; }
.sidebar-menu :deep(.el-menu-item:hover) { background: rgba(96,165,250,0.15); color: #e2e8f0; }
.sidebar-menu :deep(.el-menu-item.is-active) { background: linear-gradient(135deg, rgba(96,165,250,0.25) 0%, rgba(99,102,241,0.2) 100%); color: #a5b4fc; box-shadow: 0 0 12px rgba(96,165,250,0.08); }
.sidebar-menu :deep(.el-menu-item.is-active::before) { content: ''; position: absolute; left: 0; top: 50%; transform: translateY(-50%); width: 3px; height: 22px; background: #818cf8; border-radius: 0 3px 3px 0; box-shadow: 0 0 8px rgba(129,140,248,0.4); }
.sidebar-menu :deep(.el-menu-item i) { font-size: 18px; margin-right: 12px; }

.main-container { height: 100%; display: flex; flex-direction: column; }
.header { background: #f8fafc; border-bottom: 1px solid #e2e8f0; display: flex; align-items: center; padding: 0 28px; justify-content: space-between; height: 70px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); position: relative; z-index: 10; }
.header::after { content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 1px; background: linear-gradient(90deg, transparent 0%, rgba(96,165,250,0.08) 50%, transparent 100%); }
.header-left { display: flex; align-items: center; }
.header-title { font-size: 18px; font-weight: 600; color: #1e293b; letter-spacing: 0.3px; }
.header-right { display: flex; align-items: center; gap: 16px; }
.user-dropdown { display: flex; align-items: center; gap: 10px; cursor: pointer; padding: 8px 14px; border-radius: 10px; transition: all 0.2s; }
.user-dropdown:hover { background: #e2e8f0; }
.user-avatar { border: 2px solid #cbd5e1; width: 36px; height: 36px; }
.user-name { font-size: 14px; color: #334155; font-weight: 600; }
.arrow-icon { font-size: 12px; color: #94a3b8; }

.main-content { background: #f1f5f9; padding: 28px; overflow-y: auto; flex: 1; }
</style>
