<template>
  <div class="assistant-page">
    <div class="chat-container">
      <div class="chat-sidebar">
        <div class="sidebar-header">
          <h3>智能助手</h3>
          <el-button size="small" @click="newSession">
            <el-icon><Plus /></el-icon> 新会话
          </el-button>
        </div>
        <div class="knowledge-select">
          <el-select v-model="selectedKbId" placeholder="选择知识库" size="small" class="kb-select">
            <el-option label="不使用知识库" :value="null" />
            <el-option v-for="kb in knowledgeBases" :key="kb.id" :label="kb.name" :value="kb.id" />
          </el-select>
        </div>
        <div class="session-list">
          <div
            v-for="session in sessions"
            :key="session.session_id"
            :class="{ active: currentSessionId === session.session_id }"
            class="session-item"
            @click="switchSession(session.session_id)"
          >
            <div class="session-icon">
              <el-icon><ChatRound /></el-icon>
            </div>
            <div class="session-info">
              <div class="session-name">{{ getSessionTitle(session) }}</div>
              <div class="session-count">{{ session.message_count }} 条消息</div>
            </div>
            <el-button size="small" text type="danger" @click.stop="deleteSession(session.session_id)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
        <div class="sidebar-footer">
          <div class="thinking-toggle">
            <span>思考模式</span>
            <el-switch v-model="enableThinking" size="small" />
          </div>
        </div>
      </div>

      <div class="chat-main">
        <div class="chat-header">
          <div class="header-info">
            <el-icon :size="24" color="#3b82f6"><Cpu /></el-icon>
            <div>
              <h4>AI 助手</h4>
              <p class="header-sub">{{ selectedKbName || '不使用知识库' }}</p>
            </div>
          </div>
          <div class="header-actions">
            <el-button size="small" @click="clearCurrentSession">
              <el-icon><RefreshLeft /></el-icon> 清空
            </el-button>
          </div>
        </div>

        <div ref="messagesContainer" class="messages-container">
          <div v-if="!messages.length" class="empty-chat">
            <el-icon :size="64" color="#cbd5e1"><ChatRound /></el-icon>
            <p>开始与 AI 助手对话</p>
            <p class="empty-hint">选择知识库后，助手将基于文档内容回答问题</p>
          </div>

          <div v-for="(msg, index) in messages" :key="index" :class="['message-item', msg.role]">
            <div class="avatar">
              <el-icon v-if="msg.role === 'user'" :size="24" color="#64748b"><User /></el-icon>
              <el-icon v-else :size="24" color="#3b82f6"><Cpu /></el-icon>
            </div>
            <div class="message-content">
              <div v-if="msg.isThinking" class="thinking-badge">🤔 思考中...</div>
              <div v-html="formatMessage(msg.content)" class="message-text"></div>
              <div v-if="msg.sources" class="sources-info">
                <el-tag size="small" type="info">{{ msg.sources.length }} 个参考文档</el-tag>
              </div>
            </div>
          </div>

          <div v-if="isThinking" class="thinking-indicator">
            <div class="thinking-dots">
              <span></span><span></span><span></span>
            </div>
            <span class="thinking-text">AI 正在思考...</span>
          </div>

          <div v-if="isLoading" class="typing-indicator">
            <div class="typing-dots">
              <span></span><span></span><span></span>
            </div>
            <span class="typing-text">AI 正在回答...</span>
          </div>
        </div>

        <div class="chat-input-area">
          <el-input
            v-model="inputMessage"
            type="textarea"
            :rows="2"
            placeholder="输入您的问题..."
            class="chat-input"
            @keyup.enter.exact="sendMessage"
            :disabled="isLoading"
          />
          <div class="input-actions">
            <el-button size="small" @click="sendMessage" :loading="isLoading" :disabled="!inputMessage.trim() || isLoading">
              <el-icon><ArrowRight /></el-icon> 发送
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import { Plus, ChatRound, Delete, Cpu, User, RefreshLeft, ArrowRight } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { api } from '../api'

const currentSessionId = ref('session_' + Date.now())
const selectedKbId = ref(null)
const enableThinking = ref(false)
const inputMessage = ref('')
const messages = ref([])
const isLoading = ref(false)
const isThinking = ref(false)
const sessions = ref([])
const knowledgeBases = ref([])
const messagesContainer = ref(null)

const selectedKbName = computed(() => {
  const kb = knowledgeBases.value.find(k => k.id === selectedKbId.value)
  return kb ? kb.name : null
})

function formatMessage(content) {
  if (!content) return ''
  return content
    .replace(/\[思考\]/g, '<span class="thinking-tag">思考</span>')
    .replace(/\[\/思考\]/g, '</span>')
    .replace(/\n/g, '<br/>')
}

function generateSessionId() {
  return 'session_' + Date.now()
}

function getSessionTitle(session) {
  if (session.title) return session.title
  return '会话 ' + session.session_id.slice(-8)
}

async function loadKnowledgeBases() {
  try {
    const res = await api.knowledge.list()
    knowledgeBases.value = res.data
  } catch (error) {
    console.error('加载知识库失败:', error)
  }
}

async function loadSessions() {
  try {
    const res = await api.assistant.listSessions()
    sessions.value = res.data
  } catch (error) {
    console.error('加载会话列表失败:', error)
  }
}

async function loadHistory(sessionId) {
  try {
    const res = await api.assistant.getHistory(sessionId)
    messages.value = res.data
    scrollToBottom()
  } catch (error) {
    console.error('加载历史记录失败:', error)
  }
}

function switchSession(sessionId) {
  currentSessionId.value = sessionId
  loadHistory(sessionId)
}

async function archiveCurrentSession() {
  if (messages.value.length === 0) return  // 无对话不归档
  try {
    await api.assistant.archiveSession(currentSessionId.value)
    loadSessions()
  } catch (e) {
    console.error('归档会话失败:', e)
  }
}

async function newSession() {
  await archiveCurrentSession()
  currentSessionId.value = generateSessionId()
  messages.value = []
  loadSessions()
}

async function deleteSession(sessionId) {
  try {
    await api.assistant.clearHistory(sessionId)
    sessions.value = sessions.value.filter(s => s.session_id !== sessionId)
    if (currentSessionId.value === sessionId) {
      await archiveCurrentSession()
      currentSessionId.value = generateSessionId()
      messages.value = []
      loadSessions()
    }
  } catch (error) {
    console.error('删除会话失败:', error)
  }
}

async function clearCurrentSession() {
  try {
    await api.assistant.clearHistory(currentSessionId.value)
    messages.value = []
  } catch (error) {
    console.error('清空会话失败:', error)
  }
}

function handleBeforeUnload() {
  if (messages.value.length === 0) return  // 无对话不归档
  const token = localStorage.getItem('token')
  if (token && currentSessionId.value) {
    const url = '/api/v1/assistant/sessions/' + encodeURIComponent(currentSessionId.value) + '/archive'
    fetch(url, {
      method: 'POST',
      headers: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' },
      body: '{}',
      keepalive: true,
    }).catch(() => {})
  }
}

async function sendMessage() {
  const query = inputMessage.value.trim()
  if (!query || isLoading.value) return
  
  inputMessage.value = ''
  messages.value.push({ role: 'user', content: query })
  scrollToBottom()
  
  isLoading.value = true
  
  try {
    const response = await fetch('/api/v1/assistant/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + localStorage.getItem('token')
      },
      body: JSON.stringify({
        query,
        session_id: currentSessionId.value,
        kb_id: selectedKbId.value,
        llm_model: 'qwen3.7-plus',
        embed_model: 'text-embedding-v4',
        temperature: 0.7,
        max_tokens: 2048,
        enable_thinking: enableThinking.value,
        top_k: 5,
      })
    })
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''
    let answerContent = ''
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n\n')
      buffer = lines.pop() || ''
      
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        
        try {
          const data = JSON.parse(line.slice(6))
          
          if (data.type === 'thinking') {
            isThinking.value = true
            messages.value.push({ role: 'assistant', content: data.content, isThinking: true })
            scrollToBottom()
          } else if (data.type === 'token') {
            answerContent += data.content
            updateLastMessage(answerContent)
            scrollToBottom()
          } else if (data.type === 'error') {
            isLoading.value = false
            isThinking.value = false
            ElMessage.error('回答生成失败: ' + (data.message || '未知错误'))
            messages.value.push({ role: 'assistant', content: '回答生成失败: ' + (data.message || '未知错误') })
          } else if (data.type === 'end') {
            isThinking.value = false
          }
        } catch (e) {
          console.error('解析消息失败:', e)
        }
      }
    }
    
    isLoading.value = false
    isThinking.value = false
    loadSessions()
    
  } catch (error) {
    console.error('发送消息失败:', error)
    isLoading.value = false
    isThinking.value = false
    messages.value.push({ role: 'assistant', content: '网络错误，请重试', isThinking: false })
    scrollToBottom()
  }
}

function updateLastMessage(content) {
  if (messages.value.length > 0) {
    const last = messages.value[messages.value.length - 1]
    if (last.role === 'assistant' && !last.isThinking) {
      last.content = content
    } else {
      messages.value.push({ role: 'assistant', content, isThinking: false })
    }
  }
}

function scrollToBottom() {
  setTimeout(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  }, 50)
}

onMounted(() => {
  loadKnowledgeBases()
  loadSessions()
  window.addEventListener('beforeunload', handleBeforeUnload)
})

onUnmounted(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload)
})

// Archive on SPA route change (switch page in-app)
onBeforeRouteLeave(async (_to, _from, next) => {
  await archiveCurrentSession()
  next()
})
</script>

<style scoped>
.assistant-page { height: 100%; display: flex; background: #f8fafc; }
.chat-container { display: flex; width: 100%; height: 100%; }
.chat-sidebar { width: 280px; min-width: 280px; background: white; border-right: 1px solid #e2e8f0; display: flex; flex-direction: column; }
@media (max-width: 768px) {
  .chat-sidebar { width: 100%; min-width: 0; max-height: 40vh; overflow-y: auto; }
  .chat-container { flex-direction: column; }
  .chat-header { padding: 12px 16px; }
  .header-info h4 { font-size: 14px; }
  .messages-container { padding: 16px; }
  .message-content { max-width: 80%; }
  .chat-input-area { padding: 12px 16px; }
}

@media (max-width: 480px) {
  .chat-header { padding: 10px 12px; }
  .header-info h4 { font-size: 14px; }
  .header-sub { font-size: 11px; }
  .messages-container { padding: 12px; }
  .message-item { margin-bottom: 12px; }
  .avatar { margin: 0 8px; }
  .message-content { max-width: 85%; }
  .message-text { padding: 10px 12px; font-size: 13px; }
  .chat-input-area { padding: 10px 12px; }
}
.sidebar-header { padding: 16px; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; }
.sidebar-header h3 { margin: 0; font-size: 16px; font-weight: 600; }
.knowledge-select { padding: 12px 16px; }
.kb-select { width: 100%; }
.session-list { flex: 1; overflow-y: auto; padding: 8px; }
.session-item { display: flex; align-items: center; padding: 10px 12px; border-radius: 8px; cursor: pointer; transition: background 0.2s; }
.session-item:hover { background: #f1f5f9; }
.session-item.active { background: #eff6ff; }
.session-icon { margin-right: 10px; }
.session-info { flex: 1; min-width: 0; }
.session-name { font-size: 13px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.session-count { font-size: 11px; color: #94a3b8; }
.sidebar-footer { padding: 12px 16px; border-top: 1px solid #e2e8f0; }
.thinking-toggle { display: flex; justify-content: space-between; align-items: center; font-size: 13px; color: #64748b; }
.chat-main { flex: 1; display: flex; flex-direction: column; background: white; min-width: 0; }
.chat-header { padding: 16px 24px; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; }
.header-info { display: flex; align-items: center; gap: 10px; }
.header-info h4 { margin: 0 0 2px; font-size: 16px; font-weight: 600; }
.header-sub { font-size: 12px; color: #94a3b8; margin: 0; }
.messages-container { flex: 1; overflow-y: auto; padding: 24px; }
.empty-chat { display: flex; flex-direction: column; align-items: center; justify-content: center; flex: 1; color: #94a3b8; }
.empty-chat p { margin: 8px 0 0; }
.empty-hint { font-size: 12px; margin-top: 4px !important; }
.message-item { display: flex; margin-bottom: 20px; }
.message-item.user { flex-direction: row-reverse; }
.message-item.user .message-content { align-items: flex-end; }
.avatar { flex-shrink: 0; margin: 0 12px; }
.message-content { display: flex; flex-direction: column; max-width: 70%; }
.message-text { padding: 12px 16px; border-radius: 12px; font-size: 14px; line-height: 1.6; white-space: pre-wrap; }
.message-item.user .message-text { background: #3b82f6; color: white; border-bottom-right-radius: 4px; }
.message-item.assistant .message-text { background: #f1f5f9; color: #1e293b; border-bottom-left-radius: 4px; }
.thinking-tag { background: #fbbf24; color: #78350f; padding: 2px 6px; border-radius: 4px; font-size: 11px; margin-right: 4px; }
.thinking-badge { background: #fef3c7; color: #92400e; padding: 4px 10px; border-radius: 12px; font-size: 12px; margin-bottom: 8px; display: inline-block; }
.sources-info { margin-top: 8px; }
.thinking-indicator, .typing-indicator { display: flex; align-items: center; padding: 12px 16px; background: #f1f5f9; border-radius: 12px; width: fit-content; }
.thinking-dots, .typing-dots { display: flex; gap: 4px; margin-right: 8px; }
.thinking-dots span, .typing-dots span { width: 6px; height: 6px; background: #f59e0b; border-radius: 50%; animation: blink 1.4s infinite ease-in-out both; }
.typing-dots span { background: #3b82f6; }
.thinking-dots span:nth-child(2) { animation-delay: 0.2s; }
.thinking-dots span:nth-child(3) { animation-delay: 0.4s; }
.typing-dots span:nth-child(2) { animation-delay: 0.2s; }
.typing-dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes blink {
  0%, 80%, 100% { opacity: 0; }
  40% { opacity: 1; }
}
.thinking-text, .typing-text { font-size: 13px; color: #64748b; }
.chat-input-area { padding: 16px 24px; border-top: 1px solid #e2e8f0; background: #fafafa; flex-shrink: 0; }
.chat-input { resize: none; border-radius: 8px; }
.input-actions { display: flex; justify-content: flex-end; margin-top: 8px; }
</style>
