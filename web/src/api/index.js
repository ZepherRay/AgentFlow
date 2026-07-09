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
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers
  }
  const token = getToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  const response = await fetch(`${BASE_URL}${url}`, {
    ...options,
    headers
  })
  const data = await response.json()
  if (!response.ok) {
    throw new Error(data.message || data.detail || '请求失败')
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
    getMe: () => request('/users/me'),
    updateMe: (data) => request('/users/me', {
      method: 'PUT',
      body: JSON.stringify(data)
    }),
    changePassword: (data) => request('/users/me/change-password', {
      method: 'POST',
      body: JSON.stringify(data)
    })
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
    })
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
    })
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
    listChunks: (docId) => request(`/knowledge/documents/${docId}/chunks`),
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
    })
  },
  getToken,
  setToken,
  clearToken,
  logout: () => {
    clearToken()
  }
}