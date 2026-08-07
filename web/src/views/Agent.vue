<template>
  <div class="agent-page">
    <div class="page-header">
      <div>
        <h2>智能体管理</h2>
        <p class="page-desc">管理和配置您的 AI 智能体</p>
      </div>
      <div class="header-actions">
        <el-input v-model="searchQuery" placeholder="搜索智能体..." class="search-input" @keyup.enter="loadAgents">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-button type="primary" @click="showCreateModal = true" icon="Plus">新建智能体</el-button>
      </div>
    </div>

    <div class="agent-grid">
      <div v-for="agent in filteredAgents" :key="agent.id" class="agent-card" @click="goToDetail(agent.id)">
        <div class="card-header">
          <el-avatar :size="64" :src="getAvatarUrl(agent.avatar)" class="agent-avatar">
            <Cpu />
          </el-avatar>
          <div class="card-info">
            <h3 class="agent-name">{{ agent.name }}</h3>
            <el-tag :type="getArchitectureType(agent.architecture)" size="small">{{ getArchitectureName(agent.architecture) }}</el-tag>
          </div>
        </div>
        <p class="agent-desc">{{ agent.description || '暂无描述' }}</p>
        <div class="card-footer">
          <div class="skills-badge">
            <el-tag v-for="skill in agent.skills?.slice(0, 3)" :key="skill" size="small" effect="plain">{{ skill }}</el-tag>
            <span v-if="agent.skills?.length > 3" class="more-skills">+{{ agent.skills.length - 3 }}</span>
          </div>
          <div class="card-actions">
            <el-button size="small" @click.stop="editAgent(agent)">编辑</el-button>
            <el-button size="small" type="danger" @click.stop="confirmDelete(agent)">删除</el-button>
          </div>
        </div>
      </div>

      <div v-if="filteredAgents.length === 0" class="empty-card" @click="showCreateModal = true">
        <div class="empty-icon"><el-icon :size="48"><Plus /></el-icon></div>
        <p>创建第一个智能体</p>
      </div>
    </div>

    <el-dialog v-model="showCreateModal" :title="isEdit ? '编辑智能体' : '新建智能体'" width="700px">
      <el-tabs v-model="activeTab" type="border-card">
        <el-tab-pane label="手动配置" name="manual">
          <el-form :model="formData" label-width="100px">
            <el-form-item label="智能体头像">
              <div class="avatar-upload">
                <div class="avatar-circle" @click="triggerAvatarUpload">
                  <img v-if="formData.avatar" :src="formData.avatar" class="avatar-img" />
                  <div v-else class="avatar-placeholder">
                    <el-icon :size="24"><Plus /></el-icon>
                  </div>
                </div>
                <span class="avatar-hint">点击上传头像</span>
                <input type="file" ref="avatarInput" accept="image/*" class="hidden-input" @change="handleAvatarUpload" />
              </div>
            </el-form-item>
            <el-form-item label="智能体名称">
              <el-input v-model="formData.name" placeholder="请输入智能体名称" />
            </el-form-item>
            <el-form-item label="智能体类型">
              <el-select v-model="formData.type" placeholder="请选择类型">
                <el-option label="单智能体" value="single" />
                <el-option label="多智能体" value="multi" />
              </el-select>
            </el-form-item>
            <el-form-item label="架构类型">
              <el-select v-model="formData.architecture" placeholder="请选择架构">
                <template v-if="formData.type === 'single'">
                  <el-option label="单智能体" value="single" />
                  <el-option label="ReAct 架构" value="react" />
                  <el-option label="Plan & Execute" value="plan_execute" />
                  <el-option label="Router+Skill" value="router_skill" />
                </template>
                <template v-else>
                  <el-option label="多智能体" value="multi" />
                  <el-option label="Graph/Workflow" value="graph_workflow" />
                  <el-option label="Blackboard" value="blackboard" />
                </template>
              </el-select>
            </el-form-item>
            <el-form-item label="描述">
              <el-input v-model="formData.description" type="textarea" :rows="3" placeholder="请输入描述" />
            </el-form-item>
            <el-form-item label="关联知识库">
              <el-select v-model="formData.kb_ids" multiple placeholder="请选择知识库">
                <el-option v-for="kb in knowledgeBases" :key="kb.id" :label="kb.name" :value="kb.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="技能选择">
              <el-select v-model="formData.skills" multiple placeholder="请选择技能">
                <el-option v-for="tool in availableTools" :key="tool.name" :label="`${tool.name} - ${tool.description}`" :value="tool.name" />
              </el-select>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="一键生成" name="generate">
          <div class="generate-section">
            <el-input v-model="generatePrompt" type="textarea" :rows="6" placeholder="请描述您需要的智能体功能，例如：我需要一个数据分析助手，能够查询知识库并进行数学计算" />
            <el-button type="primary" :loading="isGenerating" @click="generateAgent" class="generate-btn">让 AI 帮我配置</el-button>
          </div>
        </el-tab-pane>
      </el-tabs>
      <template #footer>
        <el-button @click="showCreateModal = false">取消</el-button>
        <el-button type="primary" @click="saveAgent" :loading="isSaving">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showDeleteConfirm" title="确认删除" width="400px">
      <p>确定要删除智能体「{{ deleteAgent?.name }}」吗？此操作不可撤销。</p>
      <template #footer>
        <el-button @click="showDeleteConfirm = false">取消</el-button>
        <el-button type="danger" @click="deleteAgentConfirm">确认删除</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Search, Plus, Cpu } from '@element-plus/icons-vue'
import { api } from '../api'

const router = useRouter()
const agents = ref([])
const searchQuery = ref('')
const showCreateModal = ref(false)
const showDeleteConfirm = ref(false)
const isEdit = ref(false)
const isSaving = ref(false)
const isGenerating = ref(false)
const activeTab = ref('manual')
const generatePrompt = ref('')
const knowledgeBases = ref([])
const availableTools = ref([])
const deleteAgent = ref(null)
const avatarInput = ref(null)

const formData = ref({
  id: null,
  name: '',
  avatar: '',
  type: 'single',
  description: '',
  architecture: '',
  skills: [],
  kb_ids: [],
  llm_params: { temperature: 0.7, max_tokens: 2048 }
})

const filteredAgents = computed(() => {
  if (!searchQuery.value) return agents.value
  const query = searchQuery.value.toLowerCase()
  return agents.value.filter(a => 
    a.name.toLowerCase().includes(query) || 
    a.description?.toLowerCase().includes(query)
  )
})

function getArchitectureName(architecture) {
  const map = {
    'single': '单智能体',
    'react': 'ReAct',
    'plan_execute': 'Plan & Execute',
    'router_skill': 'Router+Skill',
    'multi': '多智能体',
    'graph_workflow': 'Graph/Workflow',
    'blackboard': 'Blackboard'
  }
  return map[architecture] || architecture || '未配置'
}

function getArchitectureType(architecture) {
  const map = {
    'single': 'default',
    'react': 'primary',
    'plan_execute': 'success',
    'router_skill': 'warning',
    'multi': 'danger',
    'graph_workflow': 'info',
    'blackboard': 'purple'
  }
  return map[architecture] || 'default'
}

function getAvatarUrl(avatar) {
  if (!avatar) return ''
  if (!avatar.startsWith('/') && !avatar.startsWith('http')) {
    return `/uploads/avatars/${avatar}`
  }
  return avatar
}

function goToDetail(agentId) {
  router.push(`/agents/${agentId}`)
}

async function loadAgents() {
  try {
    const res = await api.agents.list()
    agents.value = res.data
  } catch (e) {
    console.error('加载智能体失败:', e)
  }
}

async function loadKnowledgeBases() {
  try {
    const res = await api.knowledge.list()
    knowledgeBases.value = res.data || []
  } catch (e) {
    console.error('加载知识库失败:', e)
  }
}

async function loadAvailableTools() {
  try {
    const res = await api.skills.getAvailableTools()
    availableTools.value = res.data || []
  } catch (e) {
    console.error('加载工具失败:', e)
  }
}

function editAgent(agent) {
  isEdit.value = true
  formData.value = {
    id: agent.id,
    name: agent.name,
    avatar: agent.avatar || '',
    type: agent.type,
    description: agent.description,
    architecture: agent.architecture,
    skills: agent.skills || [],
    kb_ids: agent.kb_ids || [],
    llm_params: agent.llm_params || { temperature: 0.7, max_tokens: 2048 }
  }
  showCreateModal.value = true
}

function confirmDelete(agent) {
  deleteAgent.value = agent
  showDeleteConfirm.value = true
}

function triggerAvatarUpload() {
  avatarInput.value?.click()
}

async function handleAvatarUpload(event) {
  const file = event.target.files?.[0]
  if (!file) return
  
  try {
    if (isEdit.value) {
      const res = await api.agents.uploadAvatar(formData.value.id, file)
      formData.value.avatar = res.data.url
    } else {
      const res = await api.agents.uploadTempAvatar(file)
      formData.value.avatar = res.data.url
    }
  } catch (e) {
    console.error('上传头像失败:', e)
  }
}

async function deleteAgentConfirm() {
  try {
    await api.agents.delete([deleteAgent.value.id])
    await loadAgents()
    showDeleteConfirm.value = false
    deleteAgent.value = null
  } catch (e) {
    console.error('删除失败:', e)
  }
}

async function saveAgent() {
  if (!formData.value.name) {
    alert('请输入智能体名称')
    return
  }
  isSaving.value = true
  try {
    if (isEdit.value) {
      await api.agents.update(formData.value.id, formData.value)
    } else {
      await api.agents.create(formData.value)
    }
    showCreateModal.value = false
    await loadAgents()
    formData.value = {
      id: null,
      name: '',
      avatar: '',
      type: 'single',
      description: '',
      architecture: '',
      skills: [],
      kb_ids: [],
      llm_params: { temperature: 0.7, max_tokens: 2048 }
    }
    isEdit.value = false
  } catch (e) {
    console.error('保存失败:', e)
  } finally {
    isSaving.value = false
  }
}

async function generateAgent() {
  if (!generatePrompt.value.trim()) {
    alert('请输入智能体需求描述')
    return
  }
  isGenerating.value = true
  try {
    const res = await api.agents.generate(generatePrompt.value)
    const agent = res.data
    formData.value = {
      id: null,
      name: agent.name,
      type: agent.type,
      description: agent.description,
      architecture: agent.architecture,
      skills: agent.skills || [],
      kb_ids: agent.kb_ids || [],
      llm_params: agent.llm_params || { temperature: 0.7, max_tokens: 2048 }
    }
    activeTab.value = 'manual'
  } catch (e) {
    console.error('生成失败:', e)
  } finally {
    isGenerating.value = false
  }
}

watch(() => formData.value.type, (newType) => {
  const currentArch = formData.value.architecture
  if (newType === 'single') {
    if (!['single', 'react', 'plan_execute', 'router_skill'].includes(currentArch)) {
      formData.value.architecture = ''
    }
  } else {
    if (!['multi', 'graph_workflow', 'blackboard'].includes(currentArch)) {
      formData.value.architecture = ''
    }
  }
})

onMounted(async () => {
  await loadAgents()
  await loadKnowledgeBases()
  await loadAvailableTools()
})
</script>

<style scoped>
.agent-page { padding: 0; background: var(--bg-1); }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 28px; }
.page-header h2 { font-size: 22px; font-weight: 700; color: var(--t-0); margin: 0 0 8px; }
.page-desc { color: var(--t-3); font-size: 14px; margin: 0; }
.header-actions { display: flex; gap: 12px; align-items: center; }
.search-input { width: 240px; }
.search-input :deep(.el-input__wrapper) { background: var(--bg-2); border: 1px solid var(--border); box-shadow: none; }
.search-input :deep(.el-input__inner) { color: var(--t-0); }

.agent-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; }
.agent-card { background: var(--surface); border-radius: var(--r-lg); padding: 24px; cursor: pointer; transition: all 0.3s; border: 1px solid var(--border); backdrop-filter: blur(12px); }
.agent-card:hover { transform: translateY(-2px); box-shadow: var(--sh-md); border-color: var(--border-2); }
.card-header { display: flex; align-items: center; gap: 16px; margin-bottom: 14px; }
.agent-avatar { background: linear-gradient(135deg, #60a5fa 0%, #818cf8 100%); }
.card-info { flex: 1; }
.agent-name { font-size: 16px; font-weight: 600; color: var(--t-0); margin: 0 0 8px; }
.agent-desc { color: var(--t-2); font-size: 14px; line-height: 1.6; margin: 0 0 16px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.card-footer { display: flex; justify-content: space-between; align-items: center; }
.skills-badge { display: flex; gap: 6px; flex-wrap: wrap; }
.more-skills { font-size: 12px; color: var(--t-3); }
.card-actions { display: flex; gap: 8px; }

.empty-card { background: var(--surface); border: 2px dashed var(--border-2); border-radius: var(--r-lg); padding: 40px; display: flex; flex-direction: column; align-items: center; justify-content: center; cursor: pointer; transition: all 0.3s; }
.empty-card:hover { background: var(--surface-2); border-color: var(--ac); }
.empty-icon { color: var(--t-3); margin-bottom: 12px; }
.empty-card p { color: var(--t-3); font-size: 14px; margin: 0; }

.generate-section { padding: 16px 0; }

.avatar-upload {
  display: flex;
  align-items: center;
  gap: 16px;
}
.avatar-circle {
  width: 72px; height: 72px;
  border-radius: 12px;
  border: 2px dashed var(--border-2);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  overflow: hidden;
  background: var(--bg-2);
}
.avatar-circle:hover { border-color: var(--ac); background: var(--surface-2); }
.avatar-img { width: 72px; height: 72px; object-fit: cover; border-radius: 12px; }
.avatar-placeholder { color: var(--t-3); }
.avatar-hint { font-size: 13px; color: var(--t-3); }
.hidden-input { display: none; }
.generate-btn { width: 100%; margin-top: 16px; }

.agent-page :deep(.el-dialog) { background: var(--bg-2); border: 1px solid var(--border); border-radius: var(--r-lg); }
.agent-page :deep(.el-dialog__title) { color: var(--t-0); }
.agent-page :deep(.el-dialog__body) { color: var(--t-2); }
.agent-page :deep(.el-input__wrapper),
.agent-page :deep(.el-select__wrapper),
.agent-page :deep(.el-textarea__inner) { background: var(--bg-2); border: 1px solid var(--border); box-shadow: none; }
.agent-page :deep(.el-input__inner),
.agent-page :deep(.el-select__placeholder),
.agent-page :deep(.el-select__selected-item) { color: var(--t-0); }
.agent-page :deep(.el-form-item__label) { color: var(--t-2); }
.agent-page :deep(.el-tabs__item) { color: var(--t-3); }
.agent-page :deep(.el-tabs__item.is-active) { color: var(--ac-2); }
.agent-page :deep(.el-tabs__header) { border-color: var(--border); }

@media (max-width: 768px) {
  .page-header { flex-direction: column; gap: 16px; }
  .header-actions { width: 100%; }
  .search-input { flex: 1; }
  .agent-grid { grid-template-columns: 1fr; }
}

@media (max-width: 480px) {
  .page-header h2 { font-size: 20px; }
  .page-desc { font-size: 13px; }
  .agent-card { padding: 16px; }
  .card-header { gap: 12px; }
  .agent-avatar { width: 56px; height: 56px; }
  .agent-name { font-size: 15px; }
  .agent-desc { font-size: 13px; }
  .card-actions { flex-direction: column; gap: 4px; }
  .card-actions .el-button { width: 100%; }
  .el-dialog { width: 95% !important; margin: 10px !important; }
}
</style>