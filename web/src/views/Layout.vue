<template>
  <div id="app-layout">
    <el-container class="app-container">
      <el-aside :class="['sidebar', { show: sidebarVisible }]">
        <div class="sidebar-logo">
          <div class="logo-icon">
            <svg viewBox="0 0 40 40" width="32" height="32" fill="none">
              <path d="M20 4L36 12V28L20 36L4 28V12L20 4Z" stroke="#818cf8" stroke-width="2" fill="rgba(99,102,241,0.15)"/>
              <path d="M20 10L30 16V26L20 32L10 26V16L20 10Z" stroke="#a78bfa" stroke-width="2" fill="rgba(167,139,250,0.2)"/>
              <circle cx="20" cy="20" r="3" fill="#818cf8"/>
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
          <el-menu-item index="/assistant">
            <el-icon><ChatRound /></el-icon>
            <span>智能助手</span>
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
            <el-button class="menu-toggle" @click="toggleSidebar" icon="Menu" style="display: none;">菜单</el-button>
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
import { ArrowDown, HomeFilled, User, Document, Cpu, Connection, ChatRound, Menu } from '@element-plus/icons-vue'
import { api } from '../api'

const route = useRoute()
const router = useRouter()
const activeMenu = computed(() => {
  if (route.path.startsWith('/knowledge/')) return '/knowledge'
  if (route.path.startsWith('/agents/')) return '/agents'
  return route.path
})
const userInfo = ref({})
const avatarVersion = ref(Date.now())
const sidebarVisible = ref(false)

function toggleSidebar() {
  sidebarVisible.value = !sidebarVisible.value
}

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
  '/assistant': '智能助手',
  '/workflows': '工作流管理'
}

const pageTitle = computed(() => {
  if (pageTitles[route.path]) return pageTitles[route.path]
  if (route.path.startsWith('/knowledge/')) return '知识库详情'
  if (route.path.startsWith('/agents/')) return '智能体详情'
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

<style scoped>
#app-layout { height: 100%; overflow: hidden; position: relative; z-index: 1; }
.app-container { height: 100%; overflow: hidden; }

/* ── Sidebar ── */
.sidebar {
  width: 250px;
  flex-shrink: 0;
  background: rgba(18,26,48,0.6);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-right: 1px solid rgba(255,255,255,0.1);
  position: relative;
  overflow: hidden;
}
.sidebar-logo {
  height: 70px;
  display: flex;
  align-items: center;
  padding: 0 24px;
  gap: 14px;
  border-bottom: 1px solid var(--border);
  position: relative;
  z-index: 1;
}
.logo-icon { flex-shrink: 0; }
.logo-text {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 0.5px;
  background: var(--ac-grad);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.sidebar-menu {
  border-right: none;
  height: calc(100% - 70px);
  padding-top: 8px;
  background: transparent !important;
}
.sidebar-menu :deep(.el-menu-item) {
  height: 46px;
  line-height: 46px;
  margin: 3px 14px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  color: var(--t-2) !important;
  background: transparent !important;
  transition: all 0.15s;
}
.sidebar-menu :deep(.el-menu-item:hover) {
  background: var(--surface) !important;
  color: var(--t-1) !important;
}
.sidebar-menu :deep(.el-menu-item.is-active) {
  color: var(--t-0) !important;
  background: var(--surface-3) !important;
  position: relative;
}
.sidebar-menu :deep(.el-menu-item.is-active::before) {
  content: '';
  position: absolute;
  left: -14px;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 22px;
  background: var(--ac-grad);
  border-radius: 0 3px 3px 0;
}
.sidebar-menu :deep(.el-menu-item i) {
  font-size: 18px;
  margin-right: 12px;
}

/* ── Main ── */
.main-container { height: 100%; display: flex; flex-direction: column; position: relative; z-index: 1; }

/* ── Header ── */
.header {
  height: 56px;
  flex-shrink: 0;
  background: rgba(18,26,48,0.7);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255,255,255,0.1);
  display: flex;
  align-items: center;
  padding: 0 28px;
  justify-content: space-between;
  position: relative;
  z-index: 10;
}
.header-left { display: flex; align-items: center; }
.header-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--t-0);
  letter-spacing: 0.3px;
}
.header-right { display: flex; align-items: center; gap: 16px; }
.user-dropdown {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 8px 14px;
  border-radius: 10px;
  transition: all 0.2s;
}
.user-dropdown:hover { background: var(--surface); }
.user-avatar {
  border: 2px solid var(--border-2);
  width: 36px;
  height: 36px;
}
.user-name { font-size: 14px; color: var(--t-1); font-weight: 600; }
.arrow-icon { font-size: 12px; color: var(--t-3); }

/* ── Content area ── */
.main-content {
  background: var(--bg-1);
  padding: 28px;
  overflow-y: auto;
  flex: 1;
}

/* ── Responsive ── */
@media (max-width: 900px) {
  .sidebar { width: 64px; }
  .sidebar .logo-text,
  .sidebar :deep(.el-menu-item span) { display: none; }
  .sidebar :deep(.el-menu-item) { justify-content: center; padding: 0; }
  .sidebar :deep(.el-menu-item i) { margin-right: 0; }
  .sidebar-logo { justify-content: center; padding: 0 8px; }
}
@media (max-width: 480px) {
  .sidebar { position: fixed; left: 0; top: 0; bottom: 0; z-index: 100; transform: translateX(-100%); transition: transform 0.3s; }
  .sidebar.show { transform: translateX(0); }
  .menu-toggle { display: block !important; margin-right: 12px; }
  .header { padding: 0 16px; }
  .header-title { font-size: 16px; }
  .main-content { padding: 16px; }
  .user-name { display: none; }
  .user-avatar { width: 32px; height: 32px; }
}
</style>
