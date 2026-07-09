<template>
  <div id="app-layout">
    <router-view v-if="$route.path === '/login'" />
    <el-container v-else>
      <el-aside width="240px" class="sidebar">
        <div class="logo-wrapper">
          <svg viewBox="0 0 40 40" class="logo-icon">
            <path d="M20 3L34 16V24L20 37L6 24V16L20 3Z" fill="url(#logoGrad)" />
            <path d="M20 10L30 19V21L20 30L10 21V19L20 10Z" fill="white" opacity="0.9" />
            <defs>
              <linearGradient id="logoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#409eff" />
                <stop offset="100%" style="stop-color:#7c3aed" />
              </linearGradient>
            </defs>
          </svg>
          <span class="logo-text">AgentFlow</span>
        </div>
        <el-menu
          :default-active="activeMenu"
          router
          background-color="#0f172a"
          text-color="#94a3b8"
          active-text-color="#60a5fa"
          class="sidebar-menu"
        >
          <el-menu-item index="/">
            <el-icon class="menu-icon"><HomeFilled /></el-icon>
            <span>首页</span>
          </el-menu-item>
          <el-menu-item index="/agents">
            <el-icon class="menu-icon"><Cpu /></el-icon>
            <span>Agent 管理</span>
          </el-menu-item>
          <el-menu-item index="/workflow">
            <el-icon class="menu-icon"><GitBranch /></el-icon>
            <span>工作流</span>
          </el-menu-item>
          <el-menu-item index="/goods">
            <el-icon class="menu-icon"><ShoppingBag /></el-icon>
            <span>商品</span>
          </el-menu-item>
          <el-menu-item index="/knowledge">
            <el-icon class="menu-icon"><BookOpen /></el-icon>
            <span>知识库</span>
          </el-menu-item>
          <el-menu-item index="/profile">
            <el-icon class="menu-icon"><User /></el-icon>
            <span>个人中心</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      <el-container>
        <el-header class="header">
          <div class="header-left">
            <el-icon class="menu-toggle" @click="toggleSidebar"><Menu /></el-icon>
            <span class="header-title">{{ currentPageTitle }}</span>
          </div>
          <div class="header-right">
            <el-dropdown @command="handleCommand" trigger="click">
              <div class="user-info">
                <el-avatar :size="32" class="user-avatar">
                  {{ userInfo.nickname?.charAt(0) || userInfo.username?.charAt(0) || 'U' }}
                </el-avatar>
                <span class="user-name">{{ userInfo.nickname || userInfo.username }}</span>
                <el-icon class="arrow-icon"><ArrowDown /></el-icon>
              </div>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">
                    <el-icon><User /></el-icon>个人中心
                  </el-dropdown-item>
                  <el-dropdown-item divided command="logout">
                    <el-icon><SwitchButton /></el-icon>退出登录
                  </el-dropdown-item>
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
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { HomeFilled, Cpu, GitBranch, ShoppingBag, BookOpen, User, ArrowDown, Menu, SwitchButton } from '@element-plus/icons-vue'
import { api } from './api'

const route = useRoute()
const router = useRouter()
const activeMenu = computed(() => route.path)
const userInfo = ref({})
const sidebarCollapsed = ref(false)

const pageTitles = {
  '/': '首页',
  '/agents': 'Agent 管理',
  '/workflow': '工作流',
  '/goods': '商品管理',
  '/knowledge': '知识库',
  '/profile': '个人中心'
}

const currentPageTitle = computed(() => pageTitles[route.path] || 'AgentFlow')

onMounted(async () => {
  try {
    const res = await api.auth.getMe()
    userInfo.value = res.data
  } catch {
    router.push('/login')
  }
})

function handleCommand(command) {
  if (command === 'profile') {
    router.push('/profile')
  } else if (command === 'logout') {
    api.logout()
    window.location.href = '/login'
  }
}

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
}
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body, #app { height: 100%; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; }
#app-layout { height: 100%; }
</style>

<style scoped>
.sidebar {
  background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
  border-right: 1px solid #334155;
  transition: width 0.3s ease;
}

.logo-wrapper {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border-bottom: 1px solid #334155;
  padding: 0 16px;
}

.logo-icon {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 1px;
}

.sidebar-menu {
  border-right: none;
  padding: 16px 8px;
}

.menu-icon {
  font-size: 18px;
}

.header {
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  padding: 0 24px;
  justify-content: space-between;
  height: 64px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.menu-toggle {
  font-size: 20px;
  color: #64748b;
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  transition: background 0.2s;
}

.menu-toggle:hover {
  background: #f1f5f9;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.user-info:hover {
  background: #f1f5f9;
}

.user-avatar {
  background: linear-gradient(135deg, #409eff 0%, #7c3aed 100%);
  color: #fff;
  font-weight: 600;
}

.user-name {
  font-size: 14px;
  color: #334155;
  font-weight: 500;
}

.arrow-icon {
  font-size: 14px;
  color: #94a3b8;
}

.main-content {
  background: #f8fafc;
  padding: 24px;
  overflow-y: auto;
}

.el-container {
  height: 100%;
}

.el-menu-item {
  margin: 4px 0;
  border-radius: 8px;
}

.el-menu-item.is-active {
  background: rgba(96, 165, 250, 0.15) !important;
}

.el-menu-item:hover {
  background: rgba(255, 255, 255, 0.05);
}
</style>