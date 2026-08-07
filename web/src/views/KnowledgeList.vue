<template>
  <div class="knowledge-container">
    <!-- Page Header -->
    <div class="page-header">
      <div class="page-title-group">
        <h1>知识库</h1>
        <div class="subtitle">管理你的知识资产 · 智能检索 · Graph RAG</div>
      </div>
      <div class="page-actions">
        <select v-model="sortKey" class="select">
          <option value="name">按名称</option>
          <option value="document_count">按文档数</option>
          <option value="created_at">按创建时间</option>
        </select>
        <div class="search-box">
          <span class="ico">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
          </span>
          <input v-model="searchText" type="text" placeholder="搜索知识库..." @keyup.enter="loadKbs" />
        </div>
        <button class="btn btn-primary" @click="showCreateDialog = true">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          创建知识库
        </button>
      </div>
    </div>

    <!-- KB Card Grid -->
    <div class="kb-grid">
      <div v-for="kb in filteredKbs" :key="kb.id" class="kb-card" :style="{ '--card-color': getIconColor(kb.id), '--card-glow': getIconGlow(kb.id) }" @click="goToEdit(kb.id)">
        <div class="kb-card-header">
          <div class="kb-icon" :style="{ background: getIconColor(kb.id) }">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
          </div>
          <div class="kb-card-actions" @click.stop>
            <el-dropdown @command="(cmd) => handleAction(cmd, kb)">
              <button class="icon-btn">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/></svg>
              </button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="edit">编辑</el-dropdown-item>
                  <el-dropdown-item divided command="delete">删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
        <div class="kb-card-body">
          <div class="kb-card-name">{{ kb.name }}</div>
          <div class="kb-card-meta">创建于 {{ formatDate(kb.created_at) }}</div>
          <div class="kb-card-desc">{{ kb.description || '暂无描述' }}</div>
        </div>
        <div class="kb-card-footer">
          <div class="kb-stat">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            <span class="num">{{ kb.document_count }}</span> 文档
          </div>
          <div class="kb-stat">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
            <span class="num">{{ kb.chunk_count }}</span> 分段
          </div>
          <div class="kb-stat">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 7 4 4 20 4 20 7"/><line x1="9" y1="20" x2="15" y2="20"/><line x1="12" y1="4" x2="12" y2="20"/></svg>
            <span class="num">{{ formatChars(kb.char_count) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Create KB Modal -->
    <div class="modal-overlay" :class="{ show: showCreateDialog }" @click.self="showCreateDialog = false">
      <div class="modal modal-create">
        <button class="modal-close" @click="showCreateDialog = false">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
        <div class="modal-header">
          <div class="modal-title">创建知识库</div>
          <div class="modal-subtitle">为你的 AI 智能体构建专属知识资产</div>
        </div>
        <div class="modal-body">
          <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="0" class="create-form">
            <div class="field-group">
              <label class="field-label">图标主题色</label>
              <div class="gradient-picker">
                <div v-for="(grad, idx) in gradients" :key="idx"
                  class="gradient-option" :class="{ selected: selectedGradient === grad }"
                  :style="{ background: grad }"
                  @click="selectedGradient = grad">
                </div>
              </div>
            </div>
            <div class="field-group">
              <el-form-item prop="name" class="no-margin">
                <label class="field-label">知识库名称 *</label>
                <el-input v-model="createForm.name" placeholder="请输入知识库名称" maxlength="64" class="field-input" />
                <div class="char-counter">{{ createForm.name.length }} / 64</div>
              </el-form-item>
            </div>
            <div class="field-group">
              <el-form-item prop="description" class="no-margin">
                <label class="field-label">知识库描述 *</label>
                <el-input v-model="createForm.description" type="textarea" placeholder="描述知识库的内容，详尽的描述将帮助 AI 更准确地检索到内容，提高命中率。" maxlength="256" class="field-input" :rows="3" />
                <div class="char-counter">{{ createForm.description.length }} / 256</div>
              </el-form-item>
            </div>
          </el-form>
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="showCreateDialog = false">取消</button>
          <button class="btn btn-primary" :disabled="createLoading" @click="handleCreate">创建知识库</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

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

const gradients = [
  'linear-gradient(135deg, #3b82f6, #8b5cf6)',
  'linear-gradient(135deg, #10b981, #06b6d4)',
  'linear-gradient(135deg, #f59e0b, #ef4444)',
  'linear-gradient(135deg, #ec4899, #8b5cf6)',
  'linear-gradient(135deg, #6366f1, #a855f7)',
  'linear-gradient(135deg, #14b8a6, #3b82f6)',
  'linear-gradient(135deg, #f43f5e, #f59e0b)',
  'linear-gradient(135deg, #64748b, #475569)'
]

const selectedGradient = ref(gradients[0])

function getIconColor(id) {
  return colors[id % colors.length]
}

function getIconGlow(id) {
  const color = colors[id % colors.length]
  const r = parseInt(color.slice(1,3), 16)
  const g = parseInt(color.slice(3,5), 16)
  const b = parseInt(color.slice(5,7), 16)
  return `rgba(${r},${g},${b},0.3)`
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
.knowledge-container { padding: 0; height: 100%; display: flex; flex-direction: column; overflow: hidden; }

/* ═══ Page Header ═══ */
.page-header {
  display: flex; align-items: flex-end; justify-content: space-between;
  margin-bottom: 28px; flex-shrink: 0;
}
.page-title-group h1 {
  font-size: 26px; font-weight: 700; margin: 0;
  background: linear-gradient(135deg, var(--t-0) 0%, var(--t-2) 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
}
.page-title-group .subtitle { font-size: 13px; color: var(--t-3); margin-top: 4px; }
.page-actions { display: flex; gap: 10px; align-items: center; }

/* ═══ Buttons ═══ */
.btn {
  display: inline-flex; align-items: center; gap: 6px;
  height: 36px; padding: 0 16px;
  border-radius: var(--r-sm);
  font-size: 13px; font-weight: 500;
  cursor: pointer; transition: all 0.15s;
  border: none; outline: none; white-space: nowrap; font-family: inherit;
}
.btn-ghost { background: rgba(255,255,255,0.08); color: var(--t-0); border: 1px solid rgba(255,255,255,0.15); }
.btn-ghost:hover { background: rgba(255,255,255,0.14); border-color: rgba(255,255,255,0.25); }
.btn-primary { background: var(--ac-grad); color: #fff; box-shadow: 0 4px 14px var(--ac-glow); }
.btn-primary:hover { box-shadow: 0 6px 24px var(--ac-glow); transform: translateY(-1px); }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
.btn-sm { height: 30px; padding: 0 12px; font-size: 12px; }

/* ═══ Select ═══ */
.select {
  height: 36px;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: var(--r-sm);
  color: var(--t-0);
  padding: 0 30px 0 12px;
  font-size: 13px; outline: none; cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E");
  background-repeat: no-repeat; background-position: right 10px center;
}
.select:focus { border-color: var(--ac); box-shadow: 0 0 0 3px var(--ac-glow); }
.select option { background: var(--bg-2); }

/* ═══ Search Box ═══ */
.search-box { position: relative; width: 220px; }
.search-box input {
  width: 100%; height: 34px;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: var(--r-sm);
  color: var(--t-0);
  padding: 0 12px 0 34px;
  font-size: 13px; outline: none;
  transition: all 0.2s; font-family: inherit;
}
.search-box input::placeholder { color: rgba(255,255,255,0.35); }
.search-box input:focus { border-color: var(--ac); box-shadow: 0 0 0 3px var(--ac-glow); background: rgba(255,255,255,0.12); }
.search-box .ico { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); color: rgba(255,255,255,0.35); display: flex; }

/* ═══ KB Card Grid ═══ */
.kb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  flex: 1; overflow-y: auto;
  align-content: start;
  padding-bottom: 8px;
}

/* ═══ KB Card ═══ */
.kb-card {
  background: rgba(255,255,255,0.07);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: var(--r-xl);
  padding: 24px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  backdrop-filter: blur(16px);
}
.kb-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: var(--card-color, var(--ac));
  opacity: 0.7;
  transition: opacity 0.3s;
}
.kb-card::after {
  content: '';
  position: absolute;
  top: 0; right: 0;
  width: 140px; height: 140px;
  background: radial-gradient(circle, var(--card-glow, var(--ac-glow)) 0%, transparent 70%);
  opacity: 0;
  transition: opacity 0.4s;
  pointer-events: none;
}
.kb-card:hover {
  background: rgba(255,255,255,0.12);
  border-color: rgba(255,255,255,0.25);
  transform: translateY(-3px);
  box-shadow: 0 8px 32px rgba(0,0,0,0.35);
}
.kb-card:hover::before { opacity: 1; }
.kb-card:hover::after { opacity: 0.5; }

.kb-card-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  margin-bottom: 18px;
}
.kb-icon {
  width: 48px; height: 48px;
  border-radius: var(--r-md);
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 22px;
  position: relative; flex-shrink: 0;
}
.kb-icon::after {
  content: '';
  position: absolute; inset: 0;
  border-radius: var(--r-md);
  box-shadow: 0 0 24px var(--card-glow, var(--ac-glow));
  opacity: 0.5;
}
.kb-card-actions { display: flex; gap: 4px; opacity: 0; transition: opacity 0.2s; }
.kb-card:hover .kb-card-actions { opacity: 1; }
.icon-btn {
  width: 28px; height: 28px;
  border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  background: rgba(255,255,255,0.1);
  color: rgba(255,255,255,0.55);
  cursor: pointer;
  border: 1px solid rgba(255,255,255,0.12);
  transition: all 0.15s;
  font-family: inherit;
}
.icon-btn:hover { background: rgba(255,255,255,0.18); color: rgba(255,255,255,0.9); }

.kb-card-body { margin-bottom: 20px; }
.kb-card-name {
  font-size: 17px; font-weight: 700; color: #fff;
  margin-bottom: 8px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.kb-card-meta { font-size: 12px; color: rgba(255,255,255,0.4); margin-bottom: 10px; display: flex; align-items: center; gap: 6px; }
.kb-card-desc {
  font-size: 13px; color: rgba(255,255,255,0.65);
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.6;
}

.kb-card-footer {
  display: flex; gap: 20px;
  padding-top: 16px;
  border-top: 1px solid rgba(255,255,255,0.1);
}
.kb-stat {
  display: flex; align-items: center; gap: 5px;
  font-size: 12px; color: rgba(255,255,255,0.45);
}
.kb-stat svg { flex-shrink: 0; }
.kb-stat .num { color: rgba(255,255,255,0.85); font-weight: 700; }

/* ═══ Modal ═══ */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(7,11,22,0.65);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  z-index: 1000;
  display: flex; align-items: center; justify-content: center;
  opacity: 0; visibility: hidden;
  transition: opacity 0.25s, visibility 0.25s;
}
.modal-overlay.show { opacity: 1; visibility: visible; }

.modal {
  background: rgba(18,26,48,0.95);
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: var(--r-xl);
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
  max-height: 90vh;
  display: flex; flex-direction: column;
  transform: scale(0.92) translateY(20px);
  opacity: 0;
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.25s;
  position: relative;
  overflow: hidden;
}
.modal-overlay.show .modal { transform: scale(1) translateY(0); opacity: 1; }

.modal::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--ac), transparent);
  opacity: 0.6;
}

.modal-header {
  padding: 20px 24px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
  flex-shrink: 0;
}
.modal-title { font-size: 17px; font-weight: 700; color: #fff; }
.modal-subtitle { font-size: 12px; color: rgba(255,255,255,0.45); margin-top: 3px; }
.modal-close {
  position: absolute; top: 16px; right: 16px;
  width: 30px; height: 30px;
  border-radius: 8px;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.12);
  color: rgba(255,255,255,0.5);
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.15s;
  z-index: 1;
  font-family: inherit;
}
.modal-close:hover { background: rgba(255,255,255,0.16); color: rgba(255,255,255,0.9); }

.modal-body { padding: 24px; overflow-y: auto; flex: 1; }
.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid rgba(255,255,255,0.1);
  display: flex; justify-content: flex-end; gap: 10px;
  flex-shrink: 0;
}

.modal-create { width: 480px; }

/* ═══ Create Form ═══ */
.create-form .field-group { margin-bottom: 22px; }
.create-form .field-label {
  display: block; font-size: 13px; font-weight: 700;
  color: rgba(255,255,255,0.8); margin-bottom: 8px;
}
.create-form .field-input { width: 100%; }
.create-form .field-input :deep(.el-input__wrapper),
.create-form .field-input :deep(.el-textarea__inner) {
  width: 100%; height: 40px;
  background: rgba(255,255,255,0.06) !important;
  border: 1px solid rgba(255,255,255,0.12) !important;
  border-radius: var(--r-sm) !important;
  color: #fff !important;
  padding: 0 14px !important;
  font-size: 13px !important;
  outline: none !important;
  transition: all 0.2s !important;
  box-shadow: none !important;
}
.create-form .field-input :deep(.el-textarea__inner) {
  height: auto; padding: 12px 14px !important;
  min-height: 80px; resize: vertical; line-height: 1.6;
}
.create-form .field-input :deep(.el-input__wrapper):focus-within,
.create-form .field-input :deep(.el-textarea__inner):focus {
  border-color: var(--ac) !important;
  box-shadow: 0 0 0 3px var(--ac-glow) !important;
}
.create-form .field-input :deep(.el-input__inner) {
  background: transparent !important;
  color: #fff !important;
  font-size: 13px !important;
}
.create-form .el-form-item.no-margin { margin-bottom: 0; }
.char-counter { text-align: right; font-size: 11px; color: rgba(255,255,255,0.35); margin-top: 4px; }

/* ═══ Gradient Picker ═══ */
.gradient-picker { display: flex; gap: 10px; flex-wrap: wrap; }
.gradient-option {
  width: 44px; height: 44px;
  border-radius: var(--r-sm);
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s;
  position: relative;
}
.gradient-option:hover { transform: scale(1.1); }
.gradient-option.selected { border-color: #fff; box-shadow: 0 0 12px rgba(255,255,255,0.25); }
.gradient-option.selected::after {
  content: '✓';
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 18px; font-weight: 700;
  text-shadow: 0 2px 4px rgba(0,0,0,0.4);
}
</style>
