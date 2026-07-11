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
        <el-input v-model="searchText" placeholder="按名称搜索" style="width: 240px" @keyup.enter="loadKbs">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-button type="primary" @click="showCreateDialog = true">创建</el-button>
      </div>
    </div>

    <div class="kb-grid">
      <div v-for="kb in filteredKbs" :key="kb.id" class="kb-card" :style="{ '--card-color': getIconColor(kb.id) }" @click="goToEdit(kb.id)">
      <div class="card-header">
        <div class="kb-icon-wrap">
          <img v-if="kb.icon" :src="getIconUrl(kb.icon)" class="kb-icon-img" />
          <div v-else class="kb-icon" :style="{ background: getIconColor(kb.id) }">
            <el-icon :size="24"><Folder /></el-icon>
          </div>
        </div>
          <div class="card-actions" @click.stop>
            <el-dropdown @command="(cmd) => handleAction(cmd, kb)">
              <el-button link class="more-btn">
                <el-icon :size="18"><MoreFilled /></el-icon>
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
            <el-icon><Document /></el-icon>
            <span>{{ kb.document_count }} 文档数</span>
          </span>
          <span class="stat-item">
            <el-icon><ChatLineRound /></el-icon>
            <span>{{ formatChars(kb.char_count) }}</span>
          </span>
          <span class="stat-item">
            <el-icon><Link /></el-icon>
            <span>0 关联应用</span>
          </span>
        </div>
      </div>
    </div>

    <el-dialog v-model="showCreateDialog" title="创建知识库" width="520px" :close-on-click-modal="false">
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="0" class="create-form">
        <div class="form-row">
          <el-form-item prop="name" class="name-item">
            <label class="form-label">知识库名称 *</label>
            <el-input v-model="createForm.name" placeholder="请输入知识库名称" maxlength="64" show-word-limit />
          </el-form-item>
        </div>
        <div class="form-row">
          <el-form-item prop="description" class="desc-item">
            <label class="form-label">知识库描述 *</label>
            <el-input v-model="createForm.description" type="textarea" placeholder="描述知识库的内容，详尽的描述将帮助AI能深入理解知识库的内容，能更准确的检索到内容，提高该知识库的命中率。" maxlength="256" show-word-limit :rows="3" />
          </el-form-item>
        </div>
        <div class="form-row">
          <label class="form-label">图标</label>
          <div class="icon-upload-area">
            <div class="icon-preview" @click="triggerIconUpload">
              <img v-if="createForm.icon" :src="getIconUrl(createForm.icon)" class="preview-img" />
              <el-icon v-else class="upload-icon"><Plus /></el-icon>
            </div>
            <span class="upload-tip">点击上传图标</span>
            <input type="file" ref="iconInput" accept="image/*" class="hidden-input" @change="handleIconUpload" />
          </div>
        </div>
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Folder, MoreFilled, Document, ChatLineRound, Link, Plus } from '@element-plus/icons-vue'
import { api } from '../api'

const router = useRouter()
const kbs = ref([])
const searchText = ref('')
const sortKey = ref('name')
const showCreateDialog = ref(false)
const createFormRef = ref(null)
const createLoading = ref(false)
const iconInput = ref(null)

const createForm = reactive({
  name: '',
  description: '',
  icon: ''
})

const createRules = {
  name: [{ required: true, message: '请输入知识库名称', trigger: 'blur' }],
  description: [{ required: true, message: '请输入知识库描述', trigger: 'blur' }]
}

const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#6366f1', '#8b5cf6', '#06b6d4', '#ec4899']

function getIconColor(id) {
  return colors[id % colors.length]
}

function getIconUrl(icon) {
  if (!icon) return ''
  if (icon.startsWith('http')) return icon
  return icon
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

onMounted(() => loadKbs())

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
    router.push({ path: `/knowledge/${kb.id}`, query: { tab: 'config' } })
  } else if (cmd === 'delete') {
    handleDelete(kb)
  }
}

function triggerIconUpload() {
  iconInput.value?.click()
}

async function handleIconUpload(event) {
  const file = event.target.files?.[0]
  if (!file) return
  if (!file.type.startsWith('image/')) {
    ElMessage.error('请上传图片文件')
    return
  }
  try {
    const res = await api.knowledge.uploadTempIcon(file)
    createForm.icon = res.data.url
  } catch (error) {
    ElMessage.error(error.message || '上传失败')
  }
  event.target.value = ''
}

async function handleCreate() {
  const valid = await createFormRef.value.validate().catch(() => false)
  if (!valid) return
  createLoading.value = true
  try {
    await api.knowledge.create(createForm)
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    createForm.name = ''
    createForm.description = ''
    createForm.icon = ''
    loadKbs()
  } catch (error) {
    ElMessage.error(error.message || '创建失败')
  } finally {
    createLoading.value = false
  }
}

async function handleDelete(kb) {
  try {
    await ElMessageBox.confirm(`确定删除知识库 "${kb.name}" 吗？删除后不可恢复。`, '删除确认', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await api.knowledge.delete([kb.id])
    ElMessage.success('删除成功')
    loadKbs()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}
</script>

<style scoped>
.knowledge-container { padding: 0; }
.kb-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 32px; }
.header-left h2 { font-size: 26px; font-weight: 700; color: #111827; margin: 0; }
.header-right { display: flex; align-items: center; gap: 16px; }

.kb-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 24px; }
.kb-card { background: #fff; border-radius: 16px; padding: 28px; cursor: pointer; transition: all 0.3s; border: 1px solid #f3f4f6; position: relative; overflow: hidden; }
.kb-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, var(--card-color, #3b82f6) 0%, transparent 100%); }
.kb-card:hover { box-shadow: 0 12px 32px rgba(0,0,0,0.08); border-color: #e5e7eb; transform: translateY(-4px); }

.card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.kb-icon-wrap { flex-shrink: 0; }
.kb-icon { width: 52px; height: 52px; border-radius: 14px; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 24px; }
.kb-icon-img { width: 52px; height: 52px; border-radius: 14px; object-fit: cover; }
.card-actions { opacity: 0; transition: opacity 0.2s; }
.kb-card:hover .card-actions { opacity: 1; }
.more-btn { color: #9ca3af; }
.more-btn:hover { color: #3b82f6; }

.card-body { margin-bottom: 22px; }
.kb-name { font-size: 17px; font-weight: 600; margin: 0 0 10px 0; color: #111827; }
.kb-meta { font-size: 13px; color: #9ca3af; margin: 0 0 12px 0; display: flex; align-items: center; gap: 4px; }
.kb-desc { font-size: 14px; color: #6b7280; margin: 0; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; line-height: 1.7; }

.card-footer { display: flex; gap: 24px; padding-top: 20px; border-top: 1px solid #f3f4f6; }
.stat-item { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #9ca3af; }
.stat-item svg { font-size: 15px; }

.create-form { padding: 12px 0; }
.form-row { margin-bottom: 24px; }
.form-label { display: block; font-size: 14px; font-weight: 600; color: #374151; margin-bottom: 10px; }
.name-item { margin-bottom: 0; }
.desc-item { margin-bottom: 0; }
.desc-item :deep(.el-textarea__inner) { border-radius: 10px; }

.icon-upload-area { display: flex; flex-direction: column; align-items: flex-start; gap: 10px; }
.icon-preview { width: 88px; height: 88px; border-radius: 14px; border: 2px dashed #e5e7eb; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.2s; background: #f9fafb; }
.icon-preview:hover { border-color: #3b82f6; background: #eff6ff; }
.preview-img { width: 88px; height: 88px; border-radius: 14px; object-fit: cover; }
.upload-icon { font-size: 32px; color: #9ca3af; }
.upload-tip { font-size: 13px; color: #9ca3af; }
.hidden-input { display: none; }
</style>
