<template>
  <div class="home-container" v-loading="loading">
    <div class="page-header">
      <h2>欢迎回来，{{ userInfo.nickname || userInfo.username }}</h2>
      <p class="subtitle">这是您的工作概览</p>
    </div>

    <div class="stats-grid">
      <div class="stat-card" @click="$router.push('/knowledge')">
        <div class="stat-icon blue">
          <el-icon :size="26"><Folder /></el-icon>
        </div>
        <div class="stat-content">
          <p class="stat-label">知识库</p>
          <p class="stat-value">{{ stats.knowledgeCount }}</p>
        </div>
      </div>
      <div class="stat-card" @click="$router.push('/knowledge')">
        <div class="stat-icon purple">
          <el-icon :size="26"><Document /></el-icon>
        </div>
        <div class="stat-content">
          <p class="stat-label">文档</p>
          <p class="stat-value">{{ stats.documentCount }}</p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon orange">
          <el-icon :size="26"><Grid /></el-icon>
        </div>
        <div class="stat-content">
          <p class="stat-label">分段</p>
          <p class="stat-value">{{ stats.chunkCount }}</p>
        </div>
      </div>
    </div>

    <div class="bottom-grid">
      <div class="recent-section">
        <h3>最近知识库</h3>
        <div v-if="recentKnowledge.length === 0" class="empty-hint">
          <el-icon :size="40" color="#d1d5db"><Folder /></el-icon>
          <p>暂无知识库，点击上方卡片创建</p>
        </div>
        <div v-else class="recent-list">
          <div
            v-for="kb in recentKnowledge"
            :key="kb.id"
            class="recent-item"
            @click="$router.push(`/knowledge/${kb.id}`)"
          >
            <div class="recent-icon" :style="{ background: getIconColor(kb.id) }">
              <img v-if="kb.icon" :src="getIconUrl(kb.icon)" class="recent-icon-img" />
              <el-icon v-else :size="18"><Folder /></el-icon>
            </div>
            <div class="recent-info">
              <div class="recent-name">{{ kb.name }}</div>
              <div class="recent-meta">
                <span>{{ kb.document_count || 0 }} 文档</span>
                <span>{{ formatDate(kb.updated_at || kb.created_at) }}</span>
              </div>
            </div>
            <el-icon :size="16" color="#d1d5db"><ArrowRight /></el-icon>
          </div>
        </div>
      </div>

      <div class="quick-section">
        <h3>快捷操作</h3>
        <div class="quick-grid">
          <div class="quick-card" @click="$router.push('/knowledge')">
            <div class="quick-icon blue">
              <el-icon :size="20"><Plus /></el-icon>
            </div>
            <span>创建知识库</span>
          </div>
          <div class="quick-card" @click="$router.push('/knowledge')">
            <div class="quick-icon purple">
              <el-icon :size="20"><Upload /></el-icon>
            </div>
            <span>上传文档</span>
          </div>
          <div class="quick-card" @click="$router.push('/profile')">
            <div class="quick-icon orange">
              <el-icon :size="20"><User /></el-icon>
            </div>
            <span>个人设置</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Folder, Document, Grid, Plus, Upload, User, ArrowRight } from '@element-plus/icons-vue'
import { api } from '../api'

const loading = ref(true)
const userInfo = ref({})
const stats = reactive({ knowledgeCount: 0, documentCount: 0, chunkCount: 0 })
const recentKnowledge = ref([])

const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#6366f1', '#8b5cf6', '#06b6d4', '#ec4899']
function getIconColor(id) { return colors[id % colors.length] }
function getIconUrl(icon) {
  if (!icon) return ''
  if (icon.startsWith('http')) return icon
  return icon
}
function formatDate(d) {
  if (!d) return ''
  const t = new Date(d)
  return `${t.getFullYear()}-${String(t.getMonth()+1).padStart(2,'0')}-${String(t.getDate()).padStart(2,'0')}`
}

async function loadData() {
  loading.value = true
  try {
    const [meRes, kbRes] = await Promise.all([
      api.auth.getMe(),
      api.knowledge.list()
    ])
    userInfo.value = meRes.data || {}
    const kbs = kbRes.data || []
    recentKnowledge.value = kbs.slice(0, 5)
    stats.knowledgeCount = kbs.length
    stats.documentCount = kbs.reduce((s, k) => s + (k.document_count || 0), 0)
    stats.chunkCount = kbs.reduce((s, k) => s + (k.chunk_count || 0), 0)
  } catch (e) {
    console.error('Home load failed:', e)
  } finally {
    loading.value = false
  }
}

onMounted(() => loadData())
</script>

<style scoped>
.home-container { padding: 0; min-height: 400px; }
.page-header { margin-bottom: 36px; }
.page-header h2 { font-size: 28px; font-weight: 700; color: #111827; margin: 0; }
.page-header .subtitle { font-size: 15px; color: #6b7280; margin: 10px 0 0; }

.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; margin-bottom: 36px; }
.stat-card {
  background: #fff; border-radius: 16px; padding: 28px 24px;
  display: flex; align-items: center; gap: 18px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04); border: 1px solid #f3f4f6;
  cursor: pointer; transition: all 0.25s;
}
.stat-card:hover { box-shadow: 0 8px 24px rgba(0,0,0,0.08); transform: translateY(-2px); border-color: #e5e7eb; }
.stat-icon {
  width: 52px; height: 52px; border-radius: 14px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.stat-icon.blue { background: #eff6ff; color: #3b82f6; }
.stat-icon.green { background: #ecfdf5; color: #10b981; }
.stat-icon.purple { background: #f5f3ff; color: #8b5cf6; }
.stat-icon.orange { background: #fff7ed; color: #f97316; }
.stat-content { flex: 1; }
.stat-label { font-size: 13px; color: #6b7280; margin: 0 0 4px; font-weight: 500; }
.stat-value { font-size: 32px; font-weight: 700; color: #111827; margin: 0; }

.bottom-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 24px; }

.recent-section {
  background: #fff; border-radius: 16px; padding: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04); border: 1px solid #f3f4f6;
}
.recent-section h3 { font-size: 16px; font-weight: 600; color: #111827; margin: 0 0 20px; }
.empty-hint { display: flex; flex-direction: column; align-items: center; padding: 40px 0; gap: 12px; color: #9ca3af; font-size: 14px; }
.recent-list { display: flex; flex-direction: column; gap: 4px; }
.recent-item {
  display: flex; align-items: center; gap: 14px; padding: 14px 16px;
  border-radius: 10px; cursor: pointer; transition: all 0.15s;
}
.recent-item:hover { background: #f9fafb; }
.recent-icon {
  width: 40px; height: 40px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  color: #fff; flex-shrink: 0;
}
.recent-icon-img { width: 40px; height: 40px; border-radius: 10px; object-fit: cover; }
.recent-info { flex: 1; min-width: 0; }
.recent-name { font-size: 14px; font-weight: 600; color: #1f2937; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.recent-meta { display: flex; gap: 16px; font-size: 12px; color: #9ca3af; margin-top: 4px; }

.quick-section {
  background: #fff; border-radius: 16px; padding: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04); border: 1px solid #f3f4f6;
}
.quick-section h3 { font-size: 16px; font-weight: 600; color: #111827; margin: 0 0 20px; }
.quick-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.quick-card {
  display: flex; flex-direction: column; align-items: center; gap: 10px;
  padding: 18px 12px; border-radius: 12px; cursor: pointer;
  transition: all 0.2s; border: 1px solid #f3f4f6;
}
.quick-card:hover { background: #f9fafb; border-color: #e5e7eb; }
.quick-icon {
  width: 40px; height: 40px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
}
.quick-icon.blue { background: #eff6ff; color: #3b82f6; }
.quick-icon.green { background: #ecfdf5; color: #10b981; }
.quick-icon.purple { background: #f5f3ff; color: #8b5cf6; }
.quick-icon.orange { background: #fff7ed; color: #f97316; }
.quick-card span { font-size: 13px; color: #4b5563; font-weight: 500; }
</style>