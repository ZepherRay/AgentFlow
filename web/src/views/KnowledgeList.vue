<template>
  <div class="knowledge-container">
    <div class="kb-header">
      <div class="header-left">
        <h2>知识库</h2>
      </div>
      <div class="header-right">
        <el-select v-model="sortKey" placeholder="名称" style="width: 100px; margin-right: 12px">
          <el-option label="名称" value="name" />
          <el-option label="文档数" value="document_count" />
          <el-option label="创建时间" value="created_at" />
        </el-select>
        <el-input v-model="searchText" placeholder="按名称搜索" style="width: 200px" @keyup.enter="loadKbs">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-button type="primary" @click="showCreateDialog = true">创建</el-button>
      </div>
    </div>

    <div class="kb-grid">
      <div v-for="kb in filteredKbs" :key="kb.id" class="kb-card" @click="goToEdit(kb.id)">
        <div class="card-header">
          <div class="kb-icon" :style="{ background: getIconColor(kb.id) }">
            <el-icon :size="24"><Folder /></el-icon>
          </div>
          <div class="card-actions">
            <el-dropdown @command="(cmd) => handleAction(cmd, kb)">
              <el-button type="text" circle size="small">
                <el-icon><MoreFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="edit">编辑</el-dropdown-item>
                  <el-dropdown-item divided command="delete">删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
        <div class="card-body">
          <h3 class="kb-name">{{ kb.name }}</h3>
          <p class="kb-meta">演示用户 创建于 {{ formatDate(kb.created_at) }}</p>
          <p class="kb-desc">{{ kb.description || '暂无描述' }}</p>
        </div>
        <div class="card-footer">
          <span class="stat-item">
            <el-icon><FileText /></el-icon>
            <span>{{ kb.document_count }} 文档数</span>
          </span>
          <span class="stat-item">
            <el-icon><Font /></el-icon>
            <span>{{ formatChars(kb.char_count) }}</span>
          </span>
          <span class="stat-item">
            <el-icon><Link /></el-icon>
            <span>0 关联应用</span>
          </span>
        </div>
      </div>
    </div>

    <el-dialog v-model="showCreateDialog" title="创建知识库" width="500px" :close-on-click-modal="false">
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="120px">
        <el-form-item label="知识库名称" prop="name">
          <el-input v-model="createForm.name" placeholder="请输入知识库名称" maxlength="64" show-word-limit />
        </el-form-item>
        <el-form-item label="知识库描述" prop="description">
          <el-input v-model="createForm.description" type="textarea" placeholder="描述知识库的内容，详尽的描述将帮助AI能深入理解知识库的内容，能更准确的检索到内容，提高该知识库的命中率。" maxlength="256" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Folder, MoreFilled, FileText, Font, Link } from '@element-plus/icons-vue'
import { api } from '../api'

const router = useRouter()
const kbs = ref([])
const searchText = ref('')
const sortKey = ref('name')
const showCreateDialog = ref(false)
const createFormRef = ref(null)
const createLoading = ref(false)

const createForm = reactive({
  name: '',
  description: ''
})

const createRules = {
  name: [{ required: true, message: '请输入知识库名称', trigger: 'blur' }],
  description: [{ required: true, message: '请输入知识库描述', trigger: 'blur' }]
}

const colors = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399']

function getIconColor(id) {
  return colors[id % colors.length]
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

function formatChars(count) {
  if (count >= 10000) {
    return (count / 10000).toFixed(1) + 'k 字符'
  } else if (count >= 1000) {
    return (count / 1000).toFixed(1) + 'k 字符'
  }
  return count + ' 字符'
}

const filteredKbs = computed(() => {
  let result = [...kbs.value]
  if (searchText.value) {
    const kw = searchText.value.toLowerCase()
    result = result.filter(kb => kb.name.toLowerCase().includes(kw))
  }
  if (sortKey.value === 'document_count') {
    result.sort((a, b) => b.document_count - a.document_count)
  } else if (sortKey.value === 'created_at') {
    result.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
  } else {
    result.sort((a, b) => a.name.localeCompare(b.name))
  }
  return result
})

onMounted(() => {
  loadKbs()
})

async function loadKbs() {
  try {
    const res = await api.knowledge.list()
    kbs.value = res.data
  } catch (error) {
    ElMessage.error(error.message || '加载失败')
  }
}

function goToEdit(id) {
  router.push(`/knowledge/${id}`)
}

function handleAction(cmd, kb) {
  if (cmd === 'edit') {
    goToEdit(kb.id)
  } else if (cmd === 'delete') {
    handleDelete(kb)
  }
}

async function handleCreate() {
  await createFormRef.value.validate()
  createLoading.value = true
  try {
    await api.knowledge.create(createForm)
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    createForm.name = ''
    createForm.description = ''
    loadKbs()
  } catch (error) {
    ElMessage.error(error.message || '创建失败')
  } finally {
    createLoading.value = false
  }
}

async function handleDelete(kb) {
  try {
    await api.knowledge.delete(kb.id)
    ElMessage.success('删除成功')
    loadKbs()
  } catch (error) {
    ElMessage.error(error.message || '删除失败')
  }
}
</script>

<style scoped>
.knowledge-container {
  padding: 24px;
}
.kb-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.header-left h2 {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.kb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}
.kb-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #e5e7eb;
}
.kb-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border-color: #409eff;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.kb-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}
.card-actions {
  opacity: 0;
  transition: opacity 0.2s;
}
.kb-card:hover .card-actions {
  opacity: 1;
}
.card-body {
  margin-bottom: 16px;
}
.kb-name {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 6px 0;
  color: #303133;
}
.kb-meta {
  font-size: 12px;
  color: #909399;
  margin: 0 0 8px 0;
}
.kb-desc {
  font-size: 13px;
  color: #606266;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.card-footer {
  display: flex;
  gap: 16px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}
.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
}
</style>