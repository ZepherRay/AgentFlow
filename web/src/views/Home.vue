<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h1>欢迎回来，{{ userInfo.nickname || userInfo.username }}</h1>
      <p class="subtitle">今天是 {{ formatDate(new Date()) }}</p>
    </div>
    
    <el-row :gutter="20" style="margin-bottom: 24px">
      <el-col :span="6">
        <el-card class="stat-card primary">
          <div class="stat-icon">
            <el-icon :size="32"><Cpu /></el-icon>
          </div>
          <div class="stat-info">
            <el-statistic title="智能体数量" :value="stats.agentCount" />
            <span class="stat-trend positive">+12%</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card success">
          <div class="stat-icon">
            <el-icon :size="32"><GitBranch /></el-icon>
          </div>
          <div class="stat-info">
            <el-statistic title="工作流数量" :value="stats.workflowCount" />
            <span class="stat-trend positive">+8%</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card warning">
          <div class="stat-icon">
            <el-icon :size="32"><BookOpen /></el-icon>
          </div>
          <div class="stat-info">
            <el-statistic title="知识库数量" :value="stats.kbCount" />
            <span class="stat-trend positive">+25%</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card danger">
          <div class="stat-icon">
            <el-icon :size="32"><Clock /></el-icon>
          </div>
          <div class="stat-info">
            <el-statistic title="今日调用" :value="stats.todayCalls" />
            <span class="stat-trend negative">-5%</span>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20">
      <el-col :span="16">
        <el-card class="content-card">
          <template #header>
            <span class="card-title">最近活动</span>
            <el-button type="text" size="small">查看全部</el-button>
          </template>
          <el-timeline>
            <el-timeline-item v-for="activity in activities" :key="activity.id" :timestamp="activity.time">
              <div class="activity-content">
                <span class="activity-title">{{ activity.title }}</span>
                <span class="activity-desc">{{ activity.description }}</span>
              </div>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="content-card">
          <template #header>
            <span class="card-title">快捷操作</span>
          </template>
          <div class="quick-actions">
            <button class="action-btn" @click="$router.push('/agents')">
              <el-icon :size="28"><Cpu /></el-icon>
              <span>创建智能体</span>
            </button>
            <button class="action-btn" @click="$router.push('/workflow')">
              <el-icon :size="28"><GitBranch /></el-icon>
              <span>新建工作流</span>
            </button>
            <button class="action-btn" @click="$router.push('/knowledge')">
              <el-icon :size="28"><BookOpen /></el-icon>
              <span>创建知识库</span>
            </button>
          </div>
        </el-card>
        
        <el-card class="content-card" style="margin-top: 20px">
          <template #header>
            <span class="card-title">系统状态</span>
          </template>
          <div class="system-status">
            <div class="status-item">
              <span class="status-dot online"></span>
              <span>后端服务</span>
              <span class="status-text">运行中</span>
            </div>
            <div class="status-item">
              <span class="status-dot online"></span>
              <span>数据库</span>
              <span class="status-text">正常</span>
            </div>
            <div class="status-item">
              <span class="status-dot online"></span>
              <span>Redis</span>
              <span class="status-text">正常</span>
            </div>
            <div class="status-item">
              <span class="status-dot warning"></span>
              <span>向量服务</span>
              <span class="status-text">待优化</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Cpu, GitBranch, BookOpen, Clock } from '@element-plus/icons-vue'
import { api } from '../api'

const router = useRouter()
const userInfo = ref({})

const stats = ref({
  agentCount: 0,
  workflowCount: 0,
  kbCount: 0,
  todayCalls: 0
})

const activities = ref([
  { id: 1, title: '创建了知识库', description: '产品文档知识库', time: '10分钟前' },
  { id: 2, title: '部署了智能体', description: '客服助手v2.0', time: '1小时前' },
  { id: 3, title: '更新了工作流', description: '订单处理流程', time: '2小时前' },
  { id: 4, title: '导入了文档', description: 'API文档.pdf', time: '3小时前' },
  { id: 5, title: '登录系统', description: '从 192.168.1.100', time: '今天 09:30' }
])

function formatDate(date) {
  const options = { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' }
  return date.toLocaleDateString('zh-CN', options)
}

onMounted(async () => {
  try {
    const res = await api.auth.getMe()
    userInfo.value = res.data
  } catch {
    router.push('/login')
  }
})
</script>

<style scoped>
.dashboard {
  padding: 0;
}

.dashboard-header {
  margin-bottom: 24px;
}

.dashboard-header h1 {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 8px 0;
}

.subtitle {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.stat-card {
  border-radius: 12px;
  padding: 20px;
  border: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.stat-card .el-card__body {
  padding: 0;
}

.stat-card.primary {
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
}

.stat-card.success {
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
}

.stat-card.warning {
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
}

.stat-card.danger {
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
}

.stat-icon {
  display: inline-flex;
  width: 60px;
  height: 60px;
  border-radius: 12px;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
}

.stat-card.primary .stat-icon {
  background: #3b82f6;
  color: #fff;
}

.stat-card.success .stat-icon {
  background: #22c55e;
  color: #fff;
}

.stat-card.warning .stat-icon {
  background: #f59e0b;
  color: #fff;
}

.stat-card.danger .stat-icon {
  background: #ef4444;
  color: #fff;
}

.stat-info {
  display: inline-block;
  vertical-align: top;
}

.stat-info :deep(.el-statistic__label) {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 4px;
}

.stat-info :deep(.el-statistic__value) {
  font-size: 28px;
  font-weight: 700;
  color: #1e293b;
}

.stat-trend {
  font-size: 12px;
  font-weight: 500;
  margin-left: 8px;
}

.stat-trend.positive {
  color: #22c55e;
}

.stat-trend.negative {
  color: #ef4444;
}

.content-card {
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #334155;
}

.activity-content {
  display: flex;
  flex-direction: column;
}

.activity-title {
  font-size: 14px;
  font-weight: 500;
  color: #1e293b;
}

.activity-desc {
  font-size: 13px;
  color: #64748b;
  margin-top: 4px;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #fff;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover {
  border-color: #3b82f6;
  background: #eff6ff;
}

.action-btn span {
  font-size: 14px;
  font-weight: 500;
  color: #334155;
}

.system-status {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: #334155;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-dot.online {
  background: #22c55e;
  box-shadow: 0 0 8px rgba(34, 197, 94, 0.4);
}

.status-dot.warning {
  background: #f59e0b;
  box-shadow: 0 0 8px rgba(245, 158, 11, 0.4);
}

.status-text {
  margin-left: auto;
  font-size: 13px;
  color: #64748b;
}
</style>