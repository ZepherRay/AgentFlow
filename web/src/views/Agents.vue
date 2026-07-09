<template>
  <div class="agents-page">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">Agent 管理</h2>
        <p class="page-desc">管理您的 AI 智能体</p>
      </div>
      <div class="header-right">
        <el-input v-model="searchText" placeholder="搜索 Agent" style="width: 240px" @keyup.enter="loadAgents">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>创建 Agent
        </el-button>
      </div>
    </div>

    <el-card class="main-card">
      <el-table :data="filteredAgents" style="width: 100%" :header-cell-class-name="'table-header'">
        <el-table-column prop="name" label="名称" min-width="200">
          <template #default="{ row }">
            <div class="agent-name">
              <el-avatar :size="36" class="agent-avatar">
                {{ row.name?.charAt(0) || 'A' }}
              </el-avatar>
              <div class="name-info">
                <span class="name-text">{{ row.name }}</span>
                <span class="name-desc">{{ row.description || '暂无描述' }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag type="info" size="small">{{ row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '运行中' : '已停止' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="filteredAgents.length === 0" class="empty-state">
        <el-icon :size="48" class="empty-icon"><Cpu /></el-icon>
        <p class="empty-text">暂无 Agent</p>
        <el-button type="primary" @click="showCreateDialog = true">创建第一个 Agent</el-button>
      </div>
    </el-card>

    <el-dialog v-model="showCreateDialog" title="创建 Agent" width="520px" :close-on-click-modal="false">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入 Agent 名称" />
        </el-form-item>
        <el-form-item label="类型" prop="type">
          <el-select v-model="form.type" placeholder="请选择类型">
            <el-option label="对话智能体" value="chat" />
            <el-option label="任务智能体" value="task" />
            <el-option label="工具智能体" value="tool" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" placeholder="描述该 Agent 的用途和功能" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="loading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Plus, Cpu } from '@element-plus/icons-vue'
import { api } from '../api'

const agents = ref([])
const searchText = ref('')
const showCreateDialog = ref(false)
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  name: '',
  type: '',
  description: ''
})

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择类型', trigger: 'change' }]
}

const filteredAgents = computed(() => {
  if (!searchText.value) return agents.value
  const kw = searchText.value.toLowerCase()
  return agents.value.filter(a => a.name.toLowerCase().includes(kw))
})

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

onMounted(() => {
  loadAgents()
})

async function loadAgents() {
  try {
    const res = await api.agents.list()
    agents.value = res.data
  } catch (error) {
    ElMessage.error(error.message || '加载失败')
  }
}

async function handleSubmit() {
  await formRef.value.validate()
  loading.value = true
  try {
    await api.agents.create(form)
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    form.name = ''
    form.type = ''
    form.description = ''
    loadAgents()
  } catch (error) {
    ElMessage.error(error.message || '创建失败')
  } finally {
    loading.value = false
  }
}

function handleEdit(row) {
  ElMessage.info(`编辑 Agent: ${row.name}`)
}

async function handleDelete(row) {
  try {
    await api.agents.delete(row.id)
    ElMessage.success('删除成功')
    loadAgents()
  } catch (error) {
    ElMessage.error(error.message || '删除失败')
  }
}
</script>

<style scoped>
.agents-page {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  flex-direction: column;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.page-desc {
  font-size: 14px;
  color: #64748b;
  margin: 4px 0 0 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.main-card {
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.table-header {
  background: #f8fafc;
  font-weight: 600;
  color: #334155;
}

.agent-name {
  display: flex;
  align-items: center;
  gap: 12px;
}

.agent-avatar {
  background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  color: #fff;
  font-weight: 600;
}

.name-info {
  display: flex;
  flex-direction: column;
}

.name-text {
  font-size: 14px;
  font-weight: 500;
  color: #1e293b;
}

.name-desc {
  font-size: 12px;
  color: #64748b;
  margin-top: 2px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
}

.empty-icon {
  color: #cbd5e1;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 14px;
  color: #64748b;
  margin: 0 0 16px 0;
}
</style>