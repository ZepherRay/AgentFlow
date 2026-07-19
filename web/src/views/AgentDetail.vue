<template>
  <div class="agent-detail">
    <div class="detail-header">
      <el-button @click="goBack" icon="ArrowLeft">返回列表</el-button>
      <div class="header-info">
        <el-avatar :size="48" :src="getAvatarUrl(agent.avatar)" class="agent-avatar">
          <Cpu />
        </el-avatar>
        <div>
          <h2>{{ agent.name }}</h2>
          <div class="header-tags">
            <el-tag :type="getArchitectureType(agent.architecture)" size="small">{{ getArchitectureName(agent.architecture) }}</el-tag>
            <el-tag size="small" effect="plain">{{ agent.type === 'single' ? '单智能体' : '多智能体' }}</el-tag>
          </div>
        </div>
      </div>
      <el-button type="primary" @click="showEditModal = true" icon="Edit">编辑</el-button>
    </div>

    <div class="detail-body">
      <div class="left-nav">
        <el-menu :default-active="activeTab" class="nav-menu">
          <el-menu-item index="chat" @click="activeTab = 'chat'">
            <el-icon><ChatSquare /></el-icon>
            <span>聊天</span>
          </el-menu-item>
          <el-menu-item index="prompt" @click="activeTab = 'prompt'">
            <el-icon><Document /></el-icon>
            <span>系统提示词</span>
          </el-menu-item>
          <el-menu-item index="params" @click="activeTab = 'params'">
            <el-icon><Star /></el-icon>
            <span>大模型参数</span>
          </el-menu-item>
          <el-menu-item index="skills" @click="activeTab = 'skills'">
            <el-icon><Setting /></el-icon>
            <span>技能管理</span>
          </el-menu-item>
        </el-menu>
      </div>

      <div class="content-area">
        <div v-show="activeTab === 'chat'" class="chat-panel">
          <div class="chat-messages" ref="messagesContainer">
            <div v-for="(msg, idx) in messages" :key="idx" :class="['message-item', msg.role]">
              <el-avatar :size="36" :src="msg.role === 'user' ? '' : getAvatarUrl(agent.avatar)">
                <User v-if="msg.role === 'user'" />
                <Cpu v-else />
              </el-avatar>
              <div class="message-content">
                <div class="message-text">{{ msg.content }}</div>
              </div>
            </div>
            <div v-if="isSending && !isStreaming" class="message-item assistant">
              <el-avatar :size="36" :src="getAvatarUrl(agent.avatar)">
                <Cpu />
              </el-avatar>
              <div class="message-content">
                <div class="thinking-indicator">
                  <div class="thinking-dots">
                    <span></span><span></span><span></span>
                  </div>
                  <span class="thinking-text">AI 正在思考...</span>
                </div>
              </div>
            </div>
            <div v-if="isStreaming" class="message-item assistant">
              <el-avatar :size="36" :src="getAvatarUrl(agent.avatar)">
                <Cpu />
              </el-avatar>
              <div class="message-content">
                <div class="message-text">{{ streamingContent }}<span class="typing">▌</span></div>
              </div>
            </div>
          </div>
          <div class="chat-input">
            <el-input v-model="inputMessage" placeholder="输入消息..." @keyup.enter="sendMessage">
              <template #append>
                <el-button type="primary" :loading="isSending" @click="sendMessage">发送</el-button>
              </template>
            </el-input>
          </div>
        </div>

        <div v-show="activeTab === 'prompt'" class="prompt-panel">
          <div class="panel-header">
            <h3>系统提示词</h3>
            <el-button @click="regeneratePrompt" :loading="isRegenerating">重新生成</el-button>
          </div>
          <el-input v-model="systemPrompt" type="textarea" :rows="15" class="prompt-textarea" placeholder="系统提示词将基于关联知识库自动生成..." />
          <el-button type="primary" @click="savePrompt" :loading="isSavingPrompt" class="save-btn">保存提示词</el-button>
        </div>

        <div v-show="activeTab === 'params'" class="params-panel">
          <div class="panel-header">
            <h3>大模型参数配置</h3>
          </div>
          <div class="params-section">
            <div class="section-header" @click="toggleSection('llm')">
              <el-icon :size="16"><Cpu /></el-icon>
              <span>大模型</span>
              <el-icon :size="16" :class="{ rotated: paramsSections.llm }"><ArrowRight /></el-icon>
            </div>
            <div v-show="paramsSections.llm" class="section-content">
              <el-form :model="llmParams" label-width="140px">
                <el-form-item label="Temperature">
                  <div class="param-slider">
                    <el-slider v-model="llmParams.temperature" :min="0" :max="1" :step="0.1" />
                    <div class="param-control">
                      <el-button size="small" @click="adjustParam('temperature', -0.1)">-</el-button>
                      <span class="param-value">{{ llmParams.temperature }}</span>
                      <el-button size="small" @click="adjustParam('temperature', 0.1)">+</el-button>
                    </div>
                  </div>
                  <p class="param-desc">控制输出的随机性，值越大越随机</p>
                </el-form-item>
                <el-form-item label="Max Tokens">
                  <div class="param-slider">
                    <el-slider v-model="llmParams.max_tokens" :min="256" :max="8192" :step="256" />
                    <div class="param-control">
                      <el-button size="small" @click="adjustParam('max_tokens', -256)">-</el-button>
                      <span class="param-value">{{ llmParams.max_tokens }}</span>
                      <el-button size="small" @click="adjustParam('max_tokens', 256)">+</el-button>
                    </div>
                  </div>
                  <p class="param-desc">最大输出token数</p>
                </el-form-item>
              </el-form>
            </div>
          </div>
          <div class="params-section">
            <div class="section-header" @click="toggleSection('chat')">
              <el-icon :size="16"><ChatSquare /></el-icon>
              <span>对话设置</span>
              <el-icon :size="16" :class="{ rotated: paramsSections.chat }"><ArrowRight /></el-icon>
            </div>
            <div v-show="paramsSections.chat" class="section-content">
              <el-form :model="chatParams" label-width="140px">
                <el-form-item label="最大工具轮次">
                  <div class="param-slider">
                    <el-slider v-model="chatParams.max_tool_rounds" :min="1" :max="30" :step="1" />
                    <div class="param-control">
                      <el-button size="small" @click="adjustChatParam('max_tool_rounds', -1)">-</el-button>
                      <span class="param-value">{{ chatParams.max_tool_rounds }}</span>
                      <el-button size="small" @click="adjustChatParam('max_tool_rounds', 1)">+</el-button>
                    </div>
                  </div>
                  <p class="param-desc">工具调用的最大轮次数</p>
                </el-form-item>
                <el-form-item label="记忆上下文">
                  <el-switch v-model="chatParams.memory_context" :active-value="true" :inactive-value="false" />
                  <p class="param-desc">是否启用对话历史记忆</p>
                </el-form-item>
                <el-form-item label="召回数量">
                  <div class="param-slider">
                    <el-slider v-model="chatParams.recall_count" :min="1" :max="20" :step="1" />
                    <div class="param-control">
                      <el-button size="small" @click="adjustChatParam('recall_count', -1)">-</el-button>
                      <span class="param-value">{{ chatParams.recall_count }}</span>
                      <el-button size="small" @click="adjustChatParam('recall_count', 1)">+</el-button>
                    </div>
                  </div>
                  <p class="param-desc">从知识库召回的文档数量</p>
                </el-form-item>
                <el-form-item label="向量权重">
                  <div class="param-slider">
                    <el-slider v-model="chatParams.vector_weight" :min="0" :max="1" :step="0.05" />
                    <div class="param-control">
                      <el-button size="small" @click="adjustChatParam('vector_weight', -0.05)">-</el-button>
                      <span class="param-value">{{ chatParams.vector_weight }}</span>
                      <el-button size="small" @click="adjustChatParam('vector_weight', 0.05)">+</el-button>
                    </div>
                  </div>
                  <p class="param-desc">向量检索结果的权重</p>
                </el-form-item>
                <el-form-item label="关键词权重">
                  <div class="param-slider">
                    <el-slider v-model="chatParams.keyword_weight" :min="0" :max="1" :step="0.05" />
                    <div class="param-control">
                      <el-button size="small" @click="adjustChatParam('keyword_weight', -0.05)">-</el-button>
                      <span class="param-value">{{ chatParams.keyword_weight }}</span>
                      <el-button size="small" @click="adjustChatParam('keyword_weight', 0.05)">+</el-button>
                    </div>
                  </div>
                  <p class="param-desc">关键词检索结果的权重</p>
                </el-form-item>
              </el-form>
            </div>
          </div>
          <div class="params-section">
            <div class="section-header" @click="toggleSection('knowledge')">
              <el-icon :size="16"><Document /></el-icon>
              <span>知识库</span>
              <span class="kb-badge">{{ linkedKbs.length }}</span>
              <el-icon :size="16" :class="{ rotated: paramsSections.knowledge }"><ArrowRight /></el-icon>
            </div>
            <div v-show="paramsSections.knowledge" class="section-content">
              <div v-if="linkedKbs.length === 0" class="empty-kb">
                <el-empty description="暂无关联知识库" />
              </div>
              <div v-else class="kb-list">
                <div v-for="kb in linkedKbs" :key="kb.id" class="kb-item">
                  <div class="kb-info">
                    <div class="kb-icon" :style="{ background: kb.icon_color || '#3b82f6' }">
                      <el-icon :size="14"><Folder /></el-icon>
                    </div>
                    <div class="kb-detail">
                      <div class="kb-name">{{ kb.name }}</div>
                      <div class="kb-desc">{{ kb.description }}</div>
                    </div>
                  </div>
                  <el-button size="small" type="danger" @click="unlinkKb(kb.id)">取消关联</el-button>
                </div>
              </div>
              <el-button @click="showLinkKbModal = true" type="primary" size="small">+ 挂载知识库</el-button>
            </div>
          </div>
          <el-button type="primary" @click="saveParams" :loading="isSavingParams" class="save-btn">保存参数</el-button>
        </div>

        <div v-show="activeTab === 'skills'" class="skills-panel">
          <div class="panel-header">
            <h3>技能管理</h3>
            <div class="btn-group">
              <el-button @click="showAddSkillsModal = true" icon="Plus">选择内置技能</el-button>
              <el-button @click="showUploadSkillModal = true" type="success" icon="Upload">上传技能文件</el-button>
            </div>
          </div>
          <div v-if="agentSkills.length === 0" class="empty-skills">
            <el-empty description="暂无技能，点击上方按钮添加" />
          </div>
          <div v-else class="skills-grid">
            <div v-for="skill in agentSkills" :key="skill.name" class="skill-card">
              <div class="skill-info">
                <div class="skill-name">{{ skill.name }}</div>
                <div class="skill-desc">{{ skill.description }}</div>
                <div v-if="skill.content" class="skill-type custom">自定义</div>
                <div v-else class="skill-type builtin">内置</div>
              </div>
              <div class="skill-actions">
                <el-switch v-model="skill.enabled" :active-value="true" :inactive-value="false" />
                <el-button size="small" type="danger" @click="removeSkill(skill.name)">删除</el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <el-dialog v-model="showAddSkillsModal" title="选择内置技能" width="600px">
      <el-select v-model="selectedSkills" multiple placeholder="请选择技能" style="width: 100%;">
        <el-option v-for="tool in availableTools" :key="tool.name" :label="`${tool.name} - ${tool.description}`" :value="tool.name" />
      </el-select>
      <template #footer>
        <el-button @click="showAddSkillsModal = false">取消</el-button>
        <el-button type="primary" @click="addSkills" :loading="isAddingSkills">确认添加</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showUploadSkillModal" title="上传技能文件" width="600px">
      <el-form :model="uploadSkillForm" label-width="100px">
        <el-form-item label="技能名称">
          <el-input v-model="uploadSkillForm.name" placeholder="可选，默认使用文件名" />
        </el-form-item>
        <el-form-item label="技能文件">
          <div class="file-upload-area" @click="triggerSkillFileUpload">
            <div v-if="uploadSkillForm.fileName" class="uploaded-file-info">
              <el-icon :size="32"><Document /></el-icon>
              <span>{{ uploadSkillForm.fileName }}</span>
            </div>
            <div v-else class="upload-placeholder">
              <el-icon :size="48"><Upload /></el-icon>
              <p>点击选择或拖拽文件</p>
              <p class="upload-hint">支持 .md 文件或包含 .md 文件的 .zip 压缩包</p>
            </div>
          </div>
          <input type="file" ref="skillFileInput" accept=".md,.zip" class="hidden-input" @change="handleSkillFileSelect" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUploadSkillModal = false">取消</el-button>
        <el-button type="primary" @click="uploadSkill" :loading="isUploadingSkill" :disabled="!uploadSkillForm.file">确认上传</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showLinkKbModal" title="挂载知识库" width="600px">
      <el-select v-model="selectedKbs" multiple placeholder="请选择知识库" style="width: 100%;">
        <el-option v-for="kb in availableKbs" :key="kb.id" :label="`${kb.name}`" :value="kb.id" />
      </el-select>
      <template #footer>
        <el-button @click="showLinkKbModal = false">取消</el-button>
        <el-button type="primary" @click="linkKbs" :loading="isLinkingKbs">确认挂载</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showEditModal" title="编辑智能体" width="600px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="智能体头像">
          <div class="avatar-upload">
            <div class="avatar-circle" @click="triggerAvatarUpload">
              <img v-if="editForm.avatar" :src="editForm.avatar" class="avatar-img" />
              <div v-else class="avatar-placeholder">
                <el-icon :size="24"><Plus /></el-icon>
              </div>
            </div>
            <span class="avatar-hint">点击上传头像</span>
            <input type="file" ref="avatarInput" accept="image/*" class="hidden-input" @change="handleAvatarUpload" />
          </div>
        </el-form-item>
        <el-form-item label="智能体名称">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editForm.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="智能体类型">
          <el-select v-model="editForm.type" placeholder="请选择类型">
            <el-option label="单智能体" value="single" />
            <el-option label="多智能体" value="multi" />
          </el-select>
        </el-form-item>
        <el-form-item label="架构类型">
          <el-select v-model="editForm.architecture" placeholder="请选择架构">
            <template v-if="editForm.type === 'single'">
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
      </el-form>
      <template #footer>
        <el-button @click="showEditModal = false">取消</el-button>
        <el-button type="primary" @click="saveEdit" :loading="isSavingEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Cpu, User, ChatSquare, Document, Star, Setting, Upload, ArrowRight, Folder } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { api } from '../api'

const route = useRoute()
const router = useRouter()
const agentId = ref(parseInt(route.params.id))

// localStorage 持久化已删除技能（跨页面导航记住）
const DELETED_LS_PREFIX = 'agentflow_agent_deleted_skills_'
function getDeletedSkillSet() {
  try {
    return new Set(JSON.parse(localStorage.getItem(DELETED_LS_PREFIX + agentId.value) || '[]'))
  } catch { return new Set() }
}
function saveDeletedSkillSet(names) {
  localStorage.setItem(DELETED_LS_PREFIX + agentId.value, JSON.stringify([...names]))
}

// 路由参数变化时重新加载（切到其他智能体、或从其他页面切回来时自动刷新）
watch(() => route.params.id, async (newId) => {
  agentId.value = parseInt(newId)
  await loadAgent()
})
const agent = ref({})
const activeTab = ref('chat')
const messages = ref([])
const inputMessage = ref('')
const isStreaming = ref(false)
const isSending = ref(false)
const streamingContent = ref('')
const systemPrompt = ref('')
const llmParams = ref({ temperature: 0.7, max_tokens: 2048 })
const chatParams = ref({ max_tool_rounds: 10, memory_context: true, recall_count: 6, vector_weight: 0.6, keyword_weight: 0.3 })
const agentSkills = ref([])
const availableTools = ref([])
const selectedSkills = ref([])
const showAddSkillsModal = ref(false)
const showUploadSkillModal = ref(false)
const showLinkKbModal = ref(false)
const showEditModal = ref(false)
const avatarInput = ref(null)
const skillFileInput = ref(null)

const isRegenerating = ref(false)
const isSavingPrompt = ref(false)
const isSavingParams = ref(false)
const isAddingSkills = ref(false)
const isSavingEdit = ref(false)
const isUploadingSkill = ref(false)
const isLinkingKbs = ref(false)

const uploadSkillForm = ref({
  name: '',
  file: null,
  fileName: ''
})

const editForm = ref({ name: '', avatar: '', description: '', type: 'single', architecture: '' })

const messagesContainer = ref(null)

const paramsSections = ref({ llm: true, chat: true, knowledge: true })
const linkedKbs = ref([])
const availableKbs = ref([])
const selectedKbs = ref([])

function goBack() {
  router.push('/agents')
}

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

async function loadAgent() {
  try {
    const res = await api.agents.get(agentId.value)
    agent.value = res.data
    systemPrompt.value = agent.value.system_prompt || ''
    llmParams.value = agent.value.llm_params || { temperature: 0.7, max_tokens: 2048 }
    chatParams.value = agent.value.chat_params || { max_tool_rounds: 10, memory_context: true, recall_count: 6, vector_weight: 0.6, keyword_weight: 0.3 }
    editForm.value = {
      name: agent.value.name,
      avatar: agent.value.avatar || '',
      description: agent.value.description,
      type: agent.value.type || 'single',
      architecture: agent.value.architecture
    }
    await loadSkills()
    await loadAvailableTools()
    await loadKbs()
  } catch (e) {
    console.error('加载智能体失败:', e)
  }
}

async function loadSkills() {
  try {
    const res = await api.agents.getSkills(agentId.value)
    const deletedNames = getDeletedSkillSet()
    agentSkills.value = (res.data || [])
      .map(s => ({ ...s, enabled: true }))
      .filter(s => !deletedNames.has(s.name))
  } catch (e) {
    console.error('加载技能失败:', e)
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

async function sendMessage() {
  if (!inputMessage.value.trim() || isSending.value) return
  
  messages.value.push({ role: 'user', content: inputMessage.value })
  const message = inputMessage.value
  inputMessage.value = ''
  isSending.value = true
  isStreaming.value = false
  streamingContent.value = ''
  
  await nextTick()
  scrollToBottom()
  
  try {
    // 发送最近 20 条历史记录让后端有记忆
    const recentHistory = messages.value.slice(-20).map(m => ({ role: m.role, content: m.content }))
    const response = await api.agents.chat(agentId.value, message, recentHistory)
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    
    isStreaming.value = true
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      streamingContent.value += decoder.decode(value, { stream: true })
      await nextTick()
      scrollToBottom()
    }
    
    isStreaming.value = false
    messages.value.push({ role: 'assistant', content: streamingContent.value })
    streamingContent.value = ''
  } catch (e) {
    console.error('发送消息失败:', e)
    isStreaming.value = false
    messages.value.push({ role: 'assistant', content: '发送失败，请重试: ' + e.message })
  } finally {
    isSending.value = false
    await nextTick()
    scrollToBottom()
  }
}

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

async function regeneratePrompt() {
  isRegenerating.value = true
  try {
    const res = await api.agents.regeneratePrompt(agentId.value)
    systemPrompt.value = res.data.system_prompt
  } catch (e) {
    console.error('重新生成失败:', e)
  } finally {
    isRegenerating.value = false
  }
}

async function savePrompt() {
  isSavingPrompt.value = true
  try {
    await api.agents.update(agentId.value, { system_prompt: systemPrompt.value })
    agent.value.system_prompt = systemPrompt.value
    ElMessage.success('提示词保存成功！')
  } catch (e) {
    ElMessage.error('保存失败：' + e.message)
    console.error('保存失败:', e)
  } finally {
    isSavingPrompt.value = false
  }
}

function toggleSection(section) {
  paramsSections.value[section] = !paramsSections.value[section]
}

function adjustChatParam(key, delta) {
  const newValue = chatParams.value[key] + delta
  if (key === 'max_tool_rounds') {
    chatParams.value[key] = Math.max(1, Math.min(30, newValue))
  } else if (key === 'recall_count') {
    chatParams.value[key] = Math.max(1, Math.min(20, newValue))
  } else if (key === 'vector_weight' || key === 'keyword_weight') {
    chatParams.value[key] = Math.max(0, Math.min(1, parseFloat(newValue.toFixed(2))))
  }
}

async function saveParams() {
  isSavingParams.value = true
  try {
    await api.agents.update(agentId.value, { llm_params: llmParams.value, chat_params: chatParams.value })
    agent.value.llm_params = llmParams.value
    agent.value.chat_params = chatParams.value
    ElMessage.success('参数保存成功！')
  } catch (e) {
    ElMessage.error('保存失败：' + e.message)
    console.error('保存失败:', e)
  } finally {
    isSavingParams.value = false
  }
}

async function loadKbs() {
  try {
    const res = await api.knowledge.list()
    availableKbs.value = res.data || []
    linkedKbs.value = (agent.value.kb_ids || []).map(kbId => {
      const kb = availableKbs.value.find(k => k.id === kbId)
      return kb || { id: kbId, name: `知识库 ${kbId}`, description: '' }
    })
  } catch (e) {
    console.error('加载知识库失败:', e)
  }
}

async function linkKbs() {
  if (selectedKbs.value.length === 0) return
  isLinkingKbs.value = true
  try {
    const currentKbs = agent.value.kb_ids || []
    const newKbs = [...new Set([...currentKbs, ...selectedKbs.value])]
    await api.agents.update(agentId.value, { kb_ids: newKbs })
    agent.value.kb_ids = newKbs
    await loadKbs()
    showLinkKbModal.value = false
    selectedKbs.value = []
    ElMessage.success('知识库挂载成功！')
  } catch (e) {
    ElMessage.error('挂载失败：' + e.message)
    console.error('挂载知识库失败:', e)
  } finally {
    isLinkingKbs.value = false
  }
}

async function unlinkKb(kbId) {
  try {
    const currentKbs = agent.value.kb_ids || []
    const newKbs = currentKbs.filter(id => id !== kbId)
    await api.agents.update(agentId.value, { kb_ids: newKbs })
    agent.value.kb_ids = newKbs
    await loadKbs()
    ElMessage.success('知识库取消关联成功！')
  } catch (e) {
    ElMessage.error('取消关联失败：' + e.message)
    console.error('取消关联失败:', e)
  }
}

async function addSkills() {
  if (selectedSkills.value.length === 0) return
  isAddingSkills.value = true
  try {
    await api.agents.addSkills(agentId.value, selectedSkills.value)
    await loadSkills()
    showAddSkillsModal.value = false
    selectedSkills.value = []
    ElMessage.success('技能添加成功！')
  } catch (e) {
    ElMessage.error('添加技能失败：' + e.message)
    console.error('添加技能失败:', e)
  } finally {
    isAddingSkills.value = false
  }
}

function triggerSkillFileUpload() {
  skillFileInput.value?.click()
}

function handleSkillFileSelect(event) {
  const file = event.target.files?.[0]
  if (!file) return
  uploadSkillForm.value.file = file
  uploadSkillForm.value.fileName = file.name
}

async function uploadSkill() {
  if (!uploadSkillForm.value.file) return
  isUploadingSkill.value = true
  try {
    const res = await api.skills.upload(uploadSkillForm.value.file, uploadSkillForm.value.name)
    const newSkill = res.data
    await api.agents.addSkills(agentId.value, [newSkill.name])
    await loadSkills()
    showUploadSkillModal.value = false
    uploadSkillForm.value = { name: '', file: null, fileName: '' }
    ElMessage.success('技能上传并添加成功！')
  } catch (e) {
    ElMessage.error('上传技能失败：' + e.message)
    console.error('上传技能失败:', e)
  } finally {
    isUploadingSkill.value = false
  }
}

async function removeSkill(skillName) {
  try {
    const skill = agentSkills.value.find(s => s.name === skillName)
    const isCustom = skill && skill.id

    if (isCustom) {
      await api.skills.delete([skill.id])
      await api.agents.removeSkill(agentId.value, skillName)
      ElMessage.success('技能已删除')
    } else {
      await api.agents.removeSkill(agentId.value, skillName)
      ElMessage.success('已从智能体移除')
    }
    // 存入 localStorage，跨页面导航记住删除状态
    const deleted = getDeletedSkillSet()
    deleted.add(skillName)
    saveDeletedSkillSet(deleted)
    // 本地过滤
    agentSkills.value = agentSkills.value.filter(s => s.name !== skillName)
  } catch (e) {
    ElMessage.error('删除技能失败: ' + (e.message || ''))
    console.error('删除技能失败:', e)
  }
}

function triggerAvatarUpload() {
  avatarInput.value?.click()
}

async function handleAvatarUpload(event) {
  const file = event.target.files?.[0]
  if (!file) return
  
  try {
    const res = await api.agents.uploadAvatar(agentId.value, file)
    editForm.value.avatar = res.data.url
    agent.value.avatar = res.data.url
  } catch (e) {
    console.error('上传头像失败:', e)
  }
}

function adjustParam(key, delta) {
  if (key === 'temperature') {
    const newValue = llmParams.value.temperature + delta
    llmParams.value.temperature = Math.max(0, Math.min(1, newValue))
  } else if (key === 'max_tokens') {
    const newValue = llmParams.value.max_tokens + delta
    llmParams.value.max_tokens = Math.max(256, Math.min(8192, newValue))
  }
}

async function saveEdit() {
  isSavingEdit.value = true
  try {
    await api.agents.update(agentId.value, editForm.value)
    await loadAgent()
    showEditModal.value = false
  } catch (e) {
    console.error('保存失败:', e)
  } finally {
    isSavingEdit.value = false
  }
}

watch(() => editForm.value.type, (newType) => {
  const currentArch = editForm.value.architecture
  if (newType === 'single') {
    if (!['single', 'react', 'plan_execute', 'router_skill'].includes(currentArch)) {
      editForm.value.architecture = ''
    }
  } else {
    if (!['multi', 'graph_workflow', 'blackboard'].includes(currentArch)) {
      editForm.value.architecture = ''
    }
  }
})

onMounted(async () => {
  await loadAgent()
})
</script>

<style scoped>
.agent-detail { height: 100%; display: flex; flex-direction: column; }
.detail-header { display: flex; align-items: center; gap: 16px; padding: 0 0 20px; border-bottom: 1px solid #e2e8f0; }
.header-info { display: flex; align-items: center; gap: 14px; flex: 1; }
.agent-avatar { background: linear-gradient(135deg, #60a5fa 0%, #818cf8 100%); }
.header-info h2 { font-size: 20px; font-weight: 600; color: #1e293b; margin: 0; }
.header-tags { display: flex; gap: 8px; margin-top: 6px; }

.detail-body { flex: 1; display: flex; gap: 20px; margin-top: 20px; overflow: hidden; }
.left-nav { width: 180px; flex-shrink: 0; }
.nav-menu { border-right: none; }
.nav-menu :deep(.el-menu-item) { height: 44px; line-height: 44px; margin: 4px 0; border-radius: 8px; }
.nav-menu :deep(.el-menu-item.is-active) { background: rgba(96,165,250,0.15); color: #60a5fa; }

.content-area { flex: 1; background: #fff; border-radius: 12px; padding: 24px; overflow-y: auto; }

.chat-panel { height: 100%; display: flex; flex-direction: column; }
.chat-messages { flex: 1; overflow-y: auto; margin-bottom: 20px; padding-right: 12px; }
.message-item { display: flex; gap: 12px; margin-bottom: 16px; }
.message-item.user { flex-direction: row-reverse; }
.message-item.user .message-content { text-align: right; }
.message-content { max-width: 70%; }
.message-text { padding: 12px 16px; border-radius: 12px; font-size: 14px; line-height: 1.6; }
.message-item.user .message-text { background: #60a5fa; color: #fff; border-radius: 12px 0 12px 12px; }
.message-item.assistant .message-text { background: #f1f5f9; color: #1e293b; border-radius: 0 12px 12px 12px; }
.typing { animation: blink 1s infinite; }
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
.chat-input { flex-shrink: 0; }

.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.panel-header h3 { font-size: 16px; font-weight: 600; color: #1e293b; margin: 0; }
.prompt-textarea { width: 100%; }
.save-btn { margin-top: 16px; }

.params-panel h3 { font-size: 16px; font-weight: 600; color: #1e293b; margin: 0 0 20px; }
.param-slider { display: flex; align-items: center; gap: 16px; flex: 1; }
.param-control { display: flex; align-items: center; gap: 8px; min-width: 100px; }
.param-control .el-button { width: 32px; height: 32px; padding: 0; }
.param-value { font-size: 14px; font-weight: 600; color: #1e293b; min-width: 60px; text-align: center; }
.param-desc { font-size: 12px; color: #94a3b8; margin: 6px 0 0; }

.skills-panel h3 { font-size: 16px; font-weight: 600; color: #1e293b; margin: 0; }
.empty-skills { padding: 40px; }
.skills-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; margin-top: 16px; }
.skill-card { background: #f8fafc; border-radius: 10px; padding: 16px; display: flex; justify-content: space-between; align-items: center; }
.skill-info { flex: 1; }
.skill-name { font-size: 14px; font-weight: 600; color: #1e293b; margin-bottom: 4px; }
.skill-desc { font-size: 12px; color: #64748b; }
.skill-actions { display: flex; align-items: center; gap: 12px; }
.skill-actions .el-switch { margin-right: 8px; }

@media (max-width: 900px) {
  .detail-body { flex-direction: column; }
  .left-nav { width: 100%; }
  .nav-menu { display: flex; overflow-x: auto; }
  .nav-menu :deep(.el-menu-item) { flex-shrink: 0; }
}

.avatar-upload {
  display: flex;
  align-items: center;
  gap: 16px;
}
.avatar-circle {
  width: 72px; height: 72px;
  border-radius: 12px;
  border: 2px dashed #cbd5e1;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  overflow: hidden;
  background: #f8fafc;
}
.avatar-circle:hover { border-color: #3b82f6; background: #eff6ff; }
.avatar-img { width: 72px; height: 72px; object-fit: cover; border-radius: 12px; }
.avatar-placeholder { color: #94a3b8; }
.avatar-hint { font-size: 13px; color: #94a3b8; }
.hidden-input { display: none; }

.btn-group { display: flex; gap: 8px; }
.skill-type {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
  margin-top: 4px;
}
.skill-type.custom { background: #dbeafe; color: #1d4ed8; }
.skill-type.builtin { background: #fef3c7; color: #b45309; }

.file-upload-area {
  border: 2px dashed #cbd5e1;
  border-radius: 12px;
  padding: 32px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  background: #f8fafc;
}
.file-upload-area:hover { border-color: #3b82f6; background: #eff6ff; }
.upload-placeholder { color: #94a3b8; }
.upload-placeholder p { margin: 8px 0 0; font-size: 14px; }
.upload-hint { font-size: 12px !important; color: #94a3b8 !important; }
.uploaded-file-info { display: flex; align-items: center; justify-content: center; gap: 12px; color: #3b82f6; }
.uploaded-file-info span { font-size: 14px; font-weight: 500; }

.params-section {
  background: #f8fafc;
  border-radius: 10px;
  margin-bottom: 12px;
  overflow: hidden;
}
.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 16px;
  cursor: pointer;
  transition: background 0.2s;
}
.section-header:hover { background: #f1f5f9; }
.section-header span { font-size: 14px; font-weight: 500; color: #334155; }
.section-header .rotated { transform: rotate(90deg); }
.section-content { padding: 0 16px 16px; }
.kb-badge {
  background: #3b82f6;
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
}
.kb-list { margin-top: 8px; }
.kb-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: #fff;
  border-radius: 8px;
  margin-bottom: 8px;
}
.kb-item:last-child { margin-bottom: 0; }
.kb-info { display: flex; align-items: center; gap: 10px; }
.kb-icon {
  width: 32px; height: 32px;
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  color: #fff;
}
.kb-detail { flex: 1; }
.kb-name { font-size: 13px; font-weight: 500; color: #1e293b; }
.kb-desc { font-size: 12px; color: #64748b; }
.empty-kb { padding: 20px; text-align: center; }
.thinking-indicator { display: flex; align-items: center; padding: 12px 16px; background: #f1f5f9; border-radius: 12px; }
.thinking-dots { display: flex; gap: 4px; margin-right: 10px; }
.thinking-dots span { width: 6px; height: 6px; background: #3b82f6; border-radius: 50%; animation: blink 1.4s infinite ease-in-out both; }
.thinking-dots span:nth-child(2) { animation-delay: 0.2s; }
.thinking-dots span:nth-child(3) { animation-delay: 0.4s; }
.thinking-text { font-size: 13px; color: #64748b; }
@keyframes blink {
  0%, 80%, 100% { opacity: 0.3; }
  40% { opacity: 1; }
}

@media (max-width: 768px) {
  .detail-header { flex-wrap: wrap; gap: 12px; }
  .header-info { flex: 1; min-width: 0; }
  .header-info h2 { font-size: 18px; }
  .agent-avatar { width: 40px; height: 40px; }
  .content-area { padding: 16px; }
  .panel-header { flex-direction: column; align-items: flex-start; gap: 12px; }
  .btn-group { flex-wrap: wrap; gap: 8px; }
  .skills-grid { grid-template-columns: 1fr; }
  .skill-card { flex-direction: column; align-items: flex-start; gap: 12px; }
  .skill-actions { width: 100%; justify-content: space-between; }
}

@media (max-width: 480px) {
  .detail-header { padding-bottom: 16px; }
  .header-info { gap: 10px; }
  .header-info h2 { font-size: 16px; }
  .agent-avatar { width: 36px; height: 36px; }
  .content-area { padding: 12px; }
  .message-content { max-width: 85%; }
  .message-text { padding: 10px 14px; font-size: 13px; }
  .param-slider { flex-direction: column; align-items: stretch; }
  .param-control { justify-content: flex-start; }
  .param-value { font-size: 13px; }
  .kb-item { flex-direction: column; align-items: flex-start; gap: 10px; }
  .kb-info { flex: 1; }
  .el-dialog { width: 95% !important; margin: 10px !important; }
}
</style>