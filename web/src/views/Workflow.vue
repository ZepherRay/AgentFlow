<template>
  <div class="workflow-page">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">工作流</h2>
        <p class="page-desc">管理和编排您的工作流</p>
      </div>
      <div class="header-right">
        <el-input v-model="searchText" placeholder="搜索工作流" style="width: 240px" @keyup.enter="loadWorkflows">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>创建工作流
        </el-button>
      </div>
    </div>

    <el-card class="main-card">
      <el-table :data="filteredWorkflows" style="width: 100%" :header-cell-class-name="'table-header'">
        <el-table-column prop="name" label="名称" min-width="200">
          <template #default="{ row }">
            <div class="workflow-name">
              <el-avatar :size="36" class="workflow-avatar">
                <el-icon :size="18"><GitBranch /></el-icon>
              </el-avatar>
              <div class="name-info">
                <span class="name-text">{{ row.name }}</span>
                <span class="name-desc">{{ row.description || '暂无描述' }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="nodeCount" label="节点数" width="100">
          <template #default="{ row }">
            <el-tag type="info" size="small">
              {{ (row.nodes && row.nodes.length) || 0 }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '运行中' : '已停止' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="filteredWorkflows.length === 0" class="empty-state">
        <el-icon :size="48" class="empty-icon"><GitBranch /></el-icon>
        <p class="empty-text">暂无工作流</p>
        <el-button type="primary" @click="showCreateDialog = true">创建第一个工作流</el-button>
      </div>
    </el-card>

    <el-dialog v-model="showCreateDialog" title="创建工作流" width="520px" :close-on-click-modal="false">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入工作流名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" placeholder="描述该工作流的用途和流程" :rows="3" />
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
import { Search, Plus, GitBranch } from '@element-plus/icons-vue'
import { api } from '../api'

const workflows = ref([])
const searchText = ref('')
const showCreateDialog = ref(false)
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  name: '',
  description: ''
})

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }]
}

const filteredWorkflows = computed(() => {
  if (!searchText.value) return workflows.value
  const kw = searchText.value.toLowerCase()
  return workflows.value.filter(w => w.name.toLowerCase().includes(kw))
})

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

onMounted(() => {
  loadWorkflows()
})

async function loadWorkflows() {
  try {
    const res = await api.workflows.list()
    workflows.value = res.data
  } catch (error) {
    ElMessage.error(error.message || '加载失败')
  }
}

async function handleSubmit() {
  await formRef.value.validate()
  loading.value = true
  try {
    await api.workflows.create(form)
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    form.name = ''
    form.description = ''
    loadWorkflows()
  } catch (error) {
    ElMessage.error(error.message || '创建失败')
  } finally {
    loading.value = false
  }
}

function handleEdit(row) {
  ElMessage.info(`编辑工作流: ${row.name}`)
}

async function handleDelete(row) {
  try {
    await api.workflows.delete(row.id)
    ElMessage.success('删除成功')
    loadWorkflows()
  } catch (error) {
    ElMessage.error(error.message || '删除失败')
  }
}
</script>

<style scoped>
.workflow-page {
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

.workflow-name {
  display: flex;
  align-items: center;
  gap: 12px;
}

.workflow-avatar {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: #fff;
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