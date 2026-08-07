const BASE_URL = '/api/v1'

function getToken() {
  return localStorage.getItem('token')
}

function setToken(token) {
  localStorage.setItem('token', token)
}

function clearToken() {
  localStorage.removeItem('token')
}

async function request(url, options = {}) {
  const headers = { ...options.headers }
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json'
  }
  const token = getToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  const response = await fetch(`${BASE_URL}${url}`, {
    ...options,
    headers
  })
  if (response.status === 401) {
    clearToken()
    if (!window.location.pathname.startsWith('/login')) {
      window.location.href = '/login'
    }
    throw new Error('登录已失效，请重新登录')
  }
  const data = await response.json()
  if (!response.ok) {
    console.error('API error response:', data)
    // Handle custom format: { code, message, data: [...] } — e.g. ValidationError
    if (Array.isArray(data.data)) {
      const detail = data.data.map(d => `${d.loc?.slice(1).join('.') || ''}: ${d.msg}`).join('; ')
      throw new Error(data.message + ': ' + detail)
    }
    const detail = Array.isArray(data.detail)
      ? data.detail.map(d => `${d.loc?.slice(1).join('.') || ''}: ${d.msg}`).join('; ')
      : (data.detail || data.message || JSON.stringify(data) || '请求失败')
    throw new Error(detail)
  }
  return data
}

export const api = {
  auth: {
    login: (username, password) => request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    }),
    register: (username, password, email, nickname) => request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, password, email, nickname })
    }),
    getMe: () => request('/auth/me')
  },
  users: {
    updateMe: (data) => request('/users/me', {
      method: 'PUT',
      body: JSON.stringify(data)
    }),
    uploadAvatar: (file) => {
      const formData = new FormData()
      formData.append('file', file)
      return request('/users/me/avatar', {
        method: 'POST',
        body: formData,
        headers: {}
      })
    }
  },
  knowledge: {
    list: () => request('/knowledge/bases'),
    create: (data) => request('/knowledge/bases', {
      method: 'POST',
      body: JSON.stringify(data)
    }),
    get: (id) => request(`/knowledge/bases/${id}`),
    update: (id, data) => request(`/knowledge/bases/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    }),
    delete: (ids) => request('/knowledge/bases/delete', {
      method: 'POST',
      body: JSON.stringify({ ids })
    }),
    listDocuments: (kbId) => request(`/knowledge/bases/${kbId}/documents`),
    uploadDocument: (kbId, file) => {
      const formData = new FormData()
      formData.append('file', file)
      return request(`/knowledge/bases/${kbId}/documents`, {
        method: 'POST',
        body: formData,
        headers: {}
      })
    },
    deleteDocument: (ids) => request('/knowledge/documents/delete', {
      method: 'POST',
      body: JSON.stringify({ ids })
    }),
    importPreview: (kbId, data) => request(`/knowledge/bases/${kbId}/import/preview`, {
      method: 'POST',
      body: JSON.stringify(data)
    }),
    confirmImport: (kbId, data) => request(`/knowledge/bases/${kbId}/import/confirm`, {
      method: 'POST',
      body: JSON.stringify(data)
    }),
    listChunks: (docId, page, pageSize) => {
      const params = new URLSearchParams()
      params.append('page', page || 1)
      params.append('page_size', pageSize || 10)
      return request(`/knowledge/documents/${docId}/chunks?${params.toString()}`)
    },
    reprocessDocument: (docId) => request(`/knowledge/documents/${docId}/reprocess`, {
      method: 'POST'
    }),
    downloadDocument: async (docId) => {
      const token = getToken()
      const url = `${BASE_URL}/knowledge/documents/${docId}/download`
      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (!response.ok) throw new Error('下载失败')
      const blob = await response.blob()
      const blobUrl = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = blobUrl
      link.style.display = 'none'
      document.body.appendChild(link)
      link.click()
      URL.revokeObjectURL(blobUrl)
      document.body.removeChild(link)
    },
    updateChunk: (chunkId, data) => request(`/knowledge/chunks/${chunkId}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    }),
    deleteChunk: (ids) => request('/knowledge/chunks/delete', {
      method: 'POST',
      body: JSON.stringify({ ids })
    }),
    getSearchConfig: (kbId) => request(`/knowledge/bases/${kbId}/search-config`),
    saveSearchConfig: (kbId, data) => request(`/knowledge/bases/${kbId}/search-config`, {
      method: 'POST',
      body: JSON.stringify(data)
    }),
    search: (data) => request('/knowledge/search', {
      method: 'POST',
      body: JSON.stringify(data)
    }),
    uploadIcon: (kbId, file) => {
      const formData = new FormData()
      formData.append('file', file)
      return request(`/knowledge/bases/${kbId}/icon`, {
        method: 'POST',
        body: formData,
        headers: {}
      })
    },
    uploadTempIcon: (file) => {
      const formData = new FormData()
      formData.append('file', file)
      return request('/knowledge/bases/icon/temp', {
        method: 'POST',
        body: formData,
        headers: {}
      })
    },
    extractGraph: (kbId, method) => request(`/knowledge/bases/${kbId}/graph/extract`, {
      method: 'POST',
      body: JSON.stringify({ method })
    }),
    getGraph: (kbId) => request(`/knowledge/bases/${kbId}/graph`),
    getDocGraph: (kbId, docId) => request(`/knowledge/bases/${kbId}/graph/by_doc/${docId}`),
    extractDocGraph: (kbId, docId) => request(`/knowledge/bases/${kbId}/graph/doc/${docId}/extract`, {
      method: 'POST',
    })
  },
  rag: {
    query: (data) => request('/rag/query', {
      method: 'POST',
      body: JSON.stringify(data)
    }),
    answerGraph: (answerText) => request('/rag/answer-graph', {
      method: 'POST',
      body: JSON.stringify({ answer_text: answerText })
    }),
    models: (provider) => request(`/rag/models?provider=${provider || 'dashscope'}`)
  },
  assistant: {
    chat: async (data) => {
      const token = getToken()
      const response = await fetch('/api/v1/assistant/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': 'Bearer ' + token } : {})
        },
        body: JSON.stringify(data)
      })
      return response
    },
    getHistory: (sessionId) => request(`/assistant/history/${sessionId}`),
    clearHistory: (sessionId) => request(`/assistant/history/${sessionId}`, { method: 'DELETE' }),
    archiveSession: (sessionId) => request(`/assistant/sessions/${sessionId}/archive`, { method: 'POST' }),
    listSessions: () => request('/assistant/sessions')
  },
  agents: {
    list: () => request('/agents'),
    create: (data) => request('/agents', {
      method: 'POST',
      body: JSON.stringify(data)
    }),
    get: (id) => request(`/agents/${id}`),
    update: (id, data) => request(`/agents/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    }),
    delete: (ids) => request('/agents/delete', {
      method: 'POST',
      body: JSON.stringify({ ids })
    }),
    generate: (prompt) => request('/agents/generate', {
      method: 'POST',
      body: JSON.stringify({ prompt })
    }),
    chat: async (agentId, message, history = []) => {
      const token = getToken()
      const response = await fetch(`/api/v1/agents/${agentId}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': 'Bearer ' + token } : {})
        },
        body: JSON.stringify({ message, history })
      })
      return response
    },
    regeneratePrompt: (agentId) => request(`/agents/${agentId}/regenerate-prompt`, {
      method: 'POST'
    }),
    getSkills: (agentId) => request(`/agents/${agentId}/skills`),
    addSkills: (agentId, skillNames) => request(`/agents/${agentId}/skills`, {
      method: 'POST',
      body: JSON.stringify({ skill_names: skillNames })
    }),
    removeSkill: (agentId, skillName) => request(`/agents/${agentId}/skills/${skillName}`, {
      method: 'DELETE'
    }),
    getAvailableTools: (agentId) => request(`/agents/${agentId}/available-tools`),
    uploadAvatar: (agentId, file) => {
      const formData = new FormData()
      formData.append('file', file)
      return request(`/agents/${agentId}/avatar`, {
        method: 'POST',
        body: formData,
        headers: {}
      })
    },
    uploadTempAvatar: (file) => {
      const formData = new FormData()
      formData.append('file', file)
      return request('/agents/avatar/temp', {
        method: 'POST',
        body: formData,
        headers: {}
      })
    }
  },
  skills: {
    list: () => request('/skills'),
    create: (data) => request('/skills', {
      method: 'POST',
      body: JSON.stringify(data)
    }),
    upload: (file, name) => {
      const formData = new FormData()
      formData.append('file', file)
      if (name) formData.append('name', name)
      return request('/skills/upload', {
        method: 'POST',
        body: formData,
        headers: {}
      })
    },
    get: (id) => request(`/skills/${id}`),
    update: (id, data) => request(`/skills/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    }),
    delete: (ids) => request('/skills/delete', {
      method: 'POST',
      body: JSON.stringify({ ids })
    }),
    getAvailableTools: () => request('/skills/available/tools')
  },
  workflows: {
    list: () => request('/workflows'),
    create: (data) => request('/workflows', {
      method: 'POST',
      body: JSON.stringify(data)
    }),
    get: (id) => request(`/workflows/${id}`),
    update: (id, data) => request(`/workflows/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    }),
    delete: (ids) => request('/workflows/delete', {
      method: 'POST',
      body: JSON.stringify({ ids })
    }),
    test: async (id, data) => {
      const token = getToken()
      const response = await fetch(`/api/v1/workflows/${id}/test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': 'Bearer ' + token } : {})
        },
        body: JSON.stringify(data)
      })
      return response
    },
    resume: async (id, data) => {
      const token = getToken()
      const response = await fetch(`/api/v1/workflows/${id}/resume`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': 'Bearer ' + token } : {})
        },
        body: JSON.stringify(data)
      })
      return response
    }
  },
  models: {
    list: () => request('/models'),
  },
  getToken,
  setToken,
  clearToken,
  logout: () => {
    clearToken()
  }
}
