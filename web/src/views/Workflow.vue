<template>
  <div class="workflow-page">
    <!-- ====== Editor Mode (full page) ====== -->
    <template v-if="showEditor">
      <div class="wf-editor">
        <div class="editor-topbar">
          <div class="topbar-left">
            <el-button text @click="closeEditor" icon="ArrowLeft">返回</el-button>
            <div class="topbar-divider"></div>
            <el-input v-model="formData.name" placeholder="工作流名称" class="editor-title-input" size="large" />
          </div>
          <div class="topbar-center">
            <el-button-group>
              <el-button size="small" @click="zoomOut" icon="ZoomOut" />
              <el-button size="small" @click="resetZoom" plain>适应</el-button>
              <el-button size="small" @click="zoomIn" icon="ZoomIn" />
            </el-button-group>
          </div>
          <div class="topbar-right">
            <span class="node-badge">节点 {{ formData.nodes.length }}</span>
            <el-button v-if="isEdit" type="danger" text @click="confirmDelete(formData)" icon="Delete">删除</el-button>
            <el-button type="primary" @click="saveWorkflow" :loading="isSaving" icon="Select">保存</el-button>
          </div>
        </div>

        <div class="editor-body">
          <div class="editor-left">
            <div class="palette-title">节点类型</div>
            <div class="palette-list">
              <div v-for="nt in nodeTypeList" :key="nt.type" class="palette-item" @click="addNode(nt.type)">
                <div class="palette-dot" :style="{ background: nt.color }"></div>
                <div class="palette-info">
                  <span class="palette-label">{{ nt.label }}</span>
                  <span class="palette-desc">{{ nt.desc }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="editor-center" @contextmenu.prevent>
            <div ref="graphContainer" class="editor-canvas"></div>
          </div>

          <div class="editor-right">
            <div v-if="edgeSourceNode" class="edge-mode-bar">
              <el-icon :size="16"><Link /></el-icon>
              <span>从 <strong>{{ getNodeName(edgeSourceNode) }}</strong> 连线 → 单击目标节点完成</span>
              <el-button text size="small" @click="cancelEdgeCreation" icon="Close" />
            </div>
            <template v-if="selectedNode">
              <div class="config-header">
                <h4>节点配置</h4>
                <el-button text size="small" @click="selectedNode = null" icon="Close" />
              </div>
              <div class="config-type-badge" :style="{ background: getNodeColor(selectedNode.type) + '20', color: getNodeColor(selectedNode.type), borderColor: getNodeColor(selectedNode.type) }">
                <el-icon :size="14"><component :is="getNodeIcon(selectedNode.type)" /></el-icon>
                {{ getNodeTypeName(selectedNode.type) }}
              </div>
              <el-form :model="selectedNode" label-width="80px" size="small" class="config-form">
                <el-form-item label="名称"><el-input v-model="selectedNode.name" placeholder="节点名称" /></el-form-item>
                <el-form-item label="类型">
                  <el-select v-model="selectedNode.type" disabled>
                    <el-option v-for="nt in nodeTypeList" :key="nt.type" :label="nt.label" :value="nt.type" />
                  </el-select>
                </el-form-item>
                <template v-if="selectedNode.type === 'agent'">
                  <el-form-item label="智能体">
                    <el-select v-model="selectedNode.agent_id" placeholder="选择智能体" clearable>
                      <el-option v-for="a in agents" :key="a.id" :label="a.name" :value="a.id" />
                    </el-select>
                  </el-form-item>
                </template>
                <template v-if="selectedNode.type === 'tool'">
                  <el-form-item label="工具"><el-input v-model="selectedNode.tool_name" placeholder="工具名称" /></el-form-item>
                </template>
                <template v-if="selectedNode.type === 'condition'">
                  <el-form-item label="条件"><el-input v-model="selectedNode.condition" placeholder="如: result === 'success'" /></el-form-item>
                </template>
                <el-form-item label="描述"><el-input v-model="selectedNode.description" type="textarea" :rows="3" placeholder="节点描述" /></el-form-item>
              </el-form>
            </template>
            <template v-else>
              <div class="config-empty">
                <el-icon :size="40" color="#cbd5e1"><Connection /></el-icon>
                <p>点击画布上的节点进行配置</p>
                <p class="config-hint">或从左侧面板添加新节点</p>
              </div>
            </template>
          </div>
        </div>
      </div>
    </template>

    <!-- ====== Detail View ====== -->
    <template v-else-if="isDetail">
      <div class="detail-header">
        <el-button @click="goBack" icon="ArrowLeft">返回列表</el-button>
        <div class="detail-title">
          <h2>{{ workflowDetail?.name }}</h2>
          <p class="page-desc">{{ workflowDetail?.description || '暂无描述' }}</p>
        </div>
        <div class="header-actions">
          <el-button @click="editWorkflow(workflowDetail)" icon="Edit" :disabled="!workflowDetail">编辑</el-button>
          <el-button type="danger" @click="confirmDelete(workflowDetail)" icon="Delete" :disabled="!workflowDetail">删除</el-button>
        </div>
      </div>
      <div v-if="!workflowDetail" class="loading-tip">加载中...</div>
      <div v-else class="detail-content">
        <div class="detail-card">
          <h3>工作流信息</h3>
          <div class="info-row"><span class="label">关联智能体</span><span class="value">{{ getAgentName(workflowDetail.agent_id) || '未关联' }}</span></div>
          <div class="info-row"><span class="label">节点数量</span><span class="value">{{ workflowDetail.nodes?.length || 0 }} 个</span></div>
          <div class="info-row"><span class="label">连接数量</span><span class="value">{{ workflowDetail.edges?.length || 0 }} 条</span></div>
        </div>
        <div class="detail-card">
          <h3>工作流图</h3>
          <div ref="previewContainer" class="graph-preview"></div>
        </div>
        <div class="detail-card">
          <h3>节点列表</h3>
          <div v-if="workflowDetail.nodes?.length > 0" class="node-list">
            <div v-for="(node, index) in workflowDetail.nodes" :key="index" class="node-item">
              <div class="node-dot" :style="{ background: getNodeColor(node.type) }"></div>
              <div class="node-info">
                <span class="node-name">{{ node.name || `节点 ${index + 1}` }}</span>
                <span class="node-type">{{ getNodeTypeName(node.type) }}</span>
              </div>
            </div>
          </div>
          <p v-else class="empty-text">暂无节点</p>
        </div>
      </div>
    </template>

    <!-- ====== List View ====== -->
    <template v-else>
      <div class="page-header">
        <div>
          <h2>工作流管理</h2>
          <p class="page-desc">编排和管理您的 AI 工作流</p>
        </div>
        <div class="header-actions">
          <el-input v-model="searchQuery" placeholder="搜索工作流..." class="search-input" @keyup.enter="loadWorkflows">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <el-button type="primary" @click="openNewEditor" icon="Plus">新建工作流</el-button>
        </div>
      </div>

      <div class="kb-grid">
        <div v-for="wf in filteredWorkflows" :key="wf.id" class="kb-card" :style="{ '--card-color': getCardColor(wf.id) }" @click="goToDetail(wf.id)">
          <div class="card-header">
            <div class="kb-icon" :style="{ background: getCardColor(wf.id) }">
              <el-icon :size="24"><Connection /></el-icon>
            </div>
            <div class="card-actions" @click.stop>
              <el-dropdown @command="(cmd) => { cmd === 'edit' ? editWorkflow(wf) : confirmDelete(wf) }">
                <el-button link class="more-btn"><el-icon :size="18"><MoreFilled /></el-icon></el-button>
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
            <h3 class="kb-name">{{ wf.name }}</h3>
            <p class="kb-meta">创建于 {{ formatDate(wf.created_at) }}</p>
            <p class="kb-desc">{{ wf.description || '暂无描述' }}</p>
          </div>
          <div class="card-footer">
            <span class="stat-item">
              <el-icon><Check /></el-icon>
              <span>{{ wf.nodes?.length || 0 }} 节点</span>
            </span>
            <span class="stat-item">
              <el-icon><Link /></el-icon>
              <span>{{ wf.edges?.length || 0 }} 连线</span>
            </span>
          </div>
        </div>
        <div v-if="filteredWorkflows.length === 0" class="kb-card add-card" @click="openNewEditor">
          <div class="card-body" style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:180px;">
            <el-icon :size="40" color="#cbd5e1"><Plus /></el-icon>
            <p style="color:#94a3b8;margin-top:12px;">创建第一个工作流</p>
          </div>
        </div>
      </div>
    </template>

    <el-dialog v-model="showDeleteConfirm" title="确认删除" width="400px">
      <p>确定要删除工作流「{{ deleteWorkflow?.name }}」吗？此操作不可撤销。</p>
      <template #footer>
        <el-button @click="showDeleteConfirm = false">取消</el-button>
        <el-button type="danger" @click="deleteWorkflowConfirm">确认删除</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Search, Plus, Connection, Check, Cpu, Setting, Link, VideoPlay, Delete, ArrowLeft, ZoomOut, ZoomIn, Select, Close, MoreFilled } from '@element-plus/icons-vue'
import { api } from '../api'

const router = useRouter()
const route = useRoute()
const workflows = ref([])
const agents = ref([])
const workflowDetail = ref(null)
const searchQuery = ref('')
const showEditor = ref(false)
const showDeleteConfirm = ref(false)
const isEdit = ref(false)
const isSaving = ref(false)
const deleteWorkflow = ref(null)

const graphContainer = ref(null)
const previewContainer = ref(null)
const selectedNode = ref(null)
const edgeSourceNode = ref(null) // double-click source node ID for edge creation
let network = null
let previewNetwork = null

const isDetail = computed(() => !!route.params.id)

const formData = ref({ id: null, name: '', description: '', agent_id: null, nodes: [], edges: [] })

const filteredWorkflows = computed(() => {
  if (!searchQuery.value) return workflows.value
  const q = searchQuery.value.toLowerCase()
  return workflows.value.filter(w =>
    w.name.toLowerCase().includes(q) || w.description?.toLowerCase().includes(q)
  )
})

const nodeTypeList = [
  { type: 'start',  label: '开始',     desc: '工作流入口',   color: '#8b5cf6' },
  { type: 'agent',  label: '智能体',   desc: 'AI 处理节点',  color: '#3b82f6' },
  { type: 'tool',   label: '工具',     desc: '调用外部工具', color: '#10b981' },
  { type: 'condition', label: '条件',  desc: '分支判断',     color: '#f59e0b' },
  { type: 'end',    label: '结束',     desc: '工作流出口',   color: '#ef4444' },
]
const nodeTypes = Object.fromEntries(nodeTypeList.map(n => [n.type, n]))

function getNodeTypeName(type) { return nodeTypes[type]?.label || '未知' }
function getNodeColor(type)    { return nodeTypes[type]?.color || '#64748b' }
function getNodeIcon(type) {
  const map = { start: 'VideoPlay', agent: 'Cpu', tool: 'Setting', condition: 'Link', end: 'Check' }
  return map[type] || 'Connection'
}

function getAgentName(id) { return agents.value.find(a => a.id === id)?.name }

function goToDetail(id) { router.push(`/workflows/${id}`) }
function goBack()       { router.push('/workflows') }

function formatDate(d) {
  if (!d) return ''
  try { return new Date(d).toLocaleDateString('zh-CN') } catch { return '' }
}

async function loadWorkflows() {
  try { const r = await api.workflows.list(); workflows.value = r.data || [] }
  catch (e) { console.error('加载工作流失败:', e) }
}
async function loadWorkflowDetail(id) {
  try {
    const r = await api.workflows.get(id)
    workflowDetail.value = r.data
    nextTick(() => initPreviewGraph())
  } catch (e) {
    console.error('加载详情失败:', e)
    workflowDetail.value = null
  }
}
async function loadAgents() {
  try { const r = await api.agents.list(); agents.value = r.data || [] }
  catch (e) { console.error('加载智能体失败:', e) }
}

const cardColors = ['#3b82f6','#10b981','#f59e0b','#8b5cf6','#ef4444','#06b6d4','#ec4899','#14b8a6']
function getCardColor(id) { return cardColors[(id || 0) % cardColors.length] }

// ---- Route watcher: handle list↔detail navigation within same component ----
watch(() => route.params.id, async (id) => {
  if (!showEditor.value) {
    workflowDetail.value = null
    if (id) await loadWorkflowDetail(id)
    else await loadWorkflows()
  }
})

// ---- Editor ----
function openNewEditor() {
  isEdit.value = false
  formData.value = { id: null, name: '', description: '', agent_id: null, nodes: [], edges: [] }
  selectedNode.value = null
  network = null
  showEditor.value = true
}

function closeEditor() {
  showEditor.value = false
  isEdit.value = false
  selectedNode.value = null
  network = null
}

function editWorkflow(workflow) {
  if (!workflow) return
  isEdit.value = true
  formData.value = {
    id: workflow.id, name: workflow.name, description: workflow.description,
    agent_id: workflow.agent_id,
    nodes: JSON.parse(JSON.stringify(workflow.nodes || [])),
    edges: JSON.parse(JSON.stringify(workflow.edges || []))
  }
  selectedNode.value = null
  network = null
  showEditor.value = true
}

function initGraph() {
  if (!graphContainer.value || !window.vis) return
  const nodes = formData.value.nodes.map((n, i) => ({
    id: n.id || `node_${i}`, label: n.name || getNodeTypeName(n.type),
    color: { background: getNodeColor(n.type), border: '#ffffff40', highlight: { background: getNodeColor(n.type), border: '#fff' } },
    shape: 'box',
    borderWidth: 2,
    shapeProperties: { borderRadius: 8 },
    font: { color: '#fff', size: 13, face: 'sans-serif' },
    margin: { top: 10, bottom: 10, left: 14, right: 14 },
    x: n.x || 200 + (i % 3) * 200, y: n.y || 100 + Math.floor(i / 3) * 130, data: n
  }))
  const edges = formData.value.edges.map((e, i) => ({
    id: e.id || `edge_${i}`, from: e.from, to: e.to, arrows: 'to',
    smooth: { enabled: false }
  }))
  const data = { nodes: new window.vis.DataSet(nodes), edges: new window.vis.DataSet(edges) }
  const options = {
    interaction: { hover: true, tooltipDelay: 100, zoomView: true, dragView: true, dragNodes: true },
    edges: {
      color: { color: '#64748b', highlight: '#3b82f6' },
      width: 2,
      arrows: { to: { scaleFactor: 1.2 } },
      smooth: { enabled: false }
    },
    physics: { enabled: false },
    manipulation: { enabled: true, addNode: false, addEdge: true, deleteNode: true, deleteEdge: true }
  }
  network = new window.vis.Network(graphContainer.value, data, options)
  network.on('click', (p) => {
    // If in edge creation mode
    if (edgeSourceNode.value) {
      const targetId = p.nodes[0]
      if (targetId && targetId !== edgeSourceNode.value) {
        // Complete edge: source → target
        const edgeId = `edge_${Date.now()}`
        formData.value.edges.push({ id: edgeId, from: edgeSourceNode.value, to: targetId })
        network.body.data.edges.add({ id: edgeId, from: edgeSourceNode.value, to: targetId, arrows: 'to', smooth: { enabled: false } })
        resetEdgeCreation()
      } else if (!targetId) {
        // Clicked empty space → cancel
        resetEdgeCreation()
      }
      // target === source → ignore (part of double-click)
      return
    }

    // Normal mode: single click shows node details
    const nd = p.nodes[0] ? network.body.nodes[p.nodes[0]]?.options?.data : null
    if (nd) selectedNode.value = { ...nd }
    else selectedNode.value = null
  })
  network.on('doubleClick', (p) => {
    const nodeId = p.nodes[0]
    if (nodeId) {
      // Enter edge creation mode
      edgeSourceNode.value = nodeId
      // Highlight source node with amber border
      network.body.data.nodes.update({ id: nodeId, color: { background: getNodeColor(network.body.nodes[nodeId]?.options?.data?.type), border: '#f59e0b' } })
      // Clear detail panel
      selectedNode.value = null
    }
  })
  network.on('selectEdge', () => { selectedNode.value = null })
  network.on('deselectNode', () => {
    if (!edgeSourceNode.value) selectedNode.value = null
  })
  network.on('dragEnd', () => { const pos = network.getPositions(); formData.value.nodes.forEach(n => { if (pos[n.id]) { n.x = pos[n.id].x; n.y = pos[n.id].y } }) })
  network.on('addEdge', (p) => { formData.value.edges.push({ id: `edge_${Date.now()}`, from: p.from, to: p.to }) })
  network.on('deleteNode', (p) => {
    formData.value.nodes = formData.value.nodes.filter(n => !p.nodes.includes(n.id))
    formData.value.edges = formData.value.edges.filter(e => !p.nodes.includes(e.from) && !p.nodes.includes(e.to))
    selectedNode.value = null
  })
  network.on('deleteEdge', (p) => { formData.value.edges = formData.value.edges.filter((_, i) => !p.edges.includes(i)) })
}

function addNode(type) {
  const newNode = {
    id: `node_${Date.now()}`, type, name: nodeTypes[type]?.label || '新节点',
    x: 200 + Math.random() * 300, y: 100 + Math.random() * 200,
    agent_id: null, tool_name: '', condition: '', description: ''
  }
  formData.value.nodes.push(newNode)
  if (network) {
    network.body.data.nodes.add({
      id: newNode.id, label: newNode.name,
      color: { background: getNodeColor(type), border: '#ffffff40' },
      shape: 'box', borderWidth: 2, shapeProperties: { borderRadius: 8 },
      font: { color: '#fff', size: 13, face: 'sans-serif' },
      margin: { top: 10, bottom: 10, left: 14, right: 14 },
      x: newNode.x, y: newNode.y, data: newNode
    })
  }
}

function zoomIn()  { if (network) { const s = network.getScale(); network.moveTo({ scale: s * 1.2, animation: true }) } }
function zoomOut() { if (network) { const s = network.getScale(); network.moveTo({ scale: s * 0.8, animation: true }) } }
function resetZoom() { if (network) network.fit({ animation: true }) }

function getNodeName(nodeId) {
  const n = formData.value.nodes.find(n => n.id === nodeId)
  return n ? n.name : nodeId
}

function resetEdgeCreation() {
  if (edgeSourceNode.value && network) {
    // Restore original border
    const nd = formData.value.nodes.find(n => n.id === edgeSourceNode.value)
    if (nd) {
      network.body.data.nodes.update({ id: edgeSourceNode.value, color: { background: getNodeColor(nd.type), border: '#ffffff40' } })
    }
  }
  edgeSourceNode.value = null
}

function cancelEdgeCreation() { resetEdgeCreation() }

function initPreviewGraph() {
  if (!previewContainer.value || !window.vis || !workflowDetail.value) return
  const nodes = (workflowDetail.value.nodes || []).map((n, i) => ({
    id: n.id || `node_${i}`, label: n.name || getNodeTypeName(n.type),
    color: { background: getNodeColor(n.type), border: '#ffffff40' },
    shape: 'box', borderWidth: 2, shapeProperties: { borderRadius: 6 },
    font: { color: '#fff', size: 11, face: 'sans-serif' },
    margin: { top: 6, bottom: 6, left: 10, right: 10 },
    x: n.x || 100 + i * 160, y: n.y || 60
  }))
  const edges = (workflowDetail.value.edges || []).map((e, i) => ({ id: e.id || `edge_${i}`, from: e.from, to: e.to, arrows: 'to', smooth: { enabled: false } }))
  previewNetwork = new window.vis.Network(previewContainer.value,
    { nodes: new window.vis.DataSet(nodes), edges: new window.vis.DataSet(edges) },
    { interaction: { hover: true, dragView: true, zoomView: true }, edges: { color: '#64748b', width: 1.5, smooth: { enabled: false } }, physics: { enabled: false } })
}

function confirmDelete(wf) { deleteWorkflow.value = wf; showDeleteConfirm.value = true }

async function deleteWorkflowConfirm() {
  try {
    await api.workflows.delete([deleteWorkflow.value.id])
    showDeleteConfirm.value = false
    if (showEditor.value) { showEditor.value = false; network = null }
    else if (isDetail.value) goBack()
    else loadWorkflows()
  } catch (e) { console.error('删除失败:', e) }
}

async function saveWorkflow() {
  if (!formData.value.name.trim()) { alert('请输入工作流名称'); return }
  if (network) {
    const pos = network.getPositions()
    formData.value.nodes.forEach(n => { const p = pos[n.id]; if (p) { n.x = p.x; n.y = p.y } })
  }
  isSaving.value = true
  try {
    const saved = isEdit.value
      ? await api.workflows.update(formData.value.id, formData.value)
      : await api.workflows.create(formData.value)

    // Sync local list data immediately with latest nodes/edges
    const savedData = saved.data || saved

    if (!isEdit.value && savedData?.id) {
      // Creating: refresh list from API
      closeEditor()
      await loadWorkflows()
    } else if (isDetail.value) {
      // Editing from detail: update local detail + list simultaneously
      if (workflowDetail.value) {
        workflowDetail.value.nodes = JSON.parse(JSON.stringify(formData.value.nodes))
        workflowDetail.value.edges = JSON.parse(JSON.stringify(formData.value.edges))
      }
      // Also update list cache
      const idx = workflows.value.findIndex(w => w.id === formData.value.id)
      if (idx !== -1) {
        workflows.value[idx].nodes = JSON.parse(JSON.stringify(formData.value.nodes))
        workflows.value[idx].edges = JSON.parse(JSON.stringify(formData.value.edges))
      }
      closeEditor()
    } else {
      // Editing from list: update list inline, no API refetch needed
      const idx = workflows.value.findIndex(w => w.id === formData.value.id)
      if (idx !== -1) {
        workflows.value[idx].nodes = JSON.parse(JSON.stringify(formData.value.nodes))
        workflows.value[idx].edges = JSON.parse(JSON.stringify(formData.value.edges))
      }
      closeEditor()
    }
  } catch (e) { console.error('保存失败:', e) }
  finally { isSaving.value = false }
}

watch(selectedNode, (val) => {
  if (!val || !network) return
  const idx = formData.value.nodes.findIndex(n => n.id === val.id)
  if (idx !== -1) {
    formData.value.nodes[idx] = { ...val }
    network.body.data.nodes.update({ id: val.id, label: val.name, data: val })
  }
}, { deep: true })

watch(showEditor, (val) => { if (val) nextTick(() => initGraph()) })

onMounted(async () => {
  await loadAgents()
  if (route.params.id) await loadWorkflowDetail(route.params.id)
  else await loadWorkflows()
})
</script>

<style scoped>
/* ========== Editor ========== */
.wf-editor { position: fixed; inset: 0; z-index: 2000; display: flex; flex-direction: column; background: #f1f5f9; }
.editor-topbar { display: flex; align-items: center; gap: 12px; padding: 8px 16px; background: #fff; border-bottom: 1px solid #e2e8f0; flex-shrink: 0; height: 56px; }
.topbar-left { display: flex; align-items: center; gap: 8px; flex: 1; min-width: 0; }
.topbar-divider { width: 1px; height: 24px; background: #e2e8f0; }
.editor-title-input { max-width: 320px; }
.editor-title-input :deep(.el-input__inner) { font-weight: 600; font-size: 16px; border: none; background: transparent; }
.editor-title-input :deep(.el-input__inner):focus { background: #f8fafc; }
.topbar-center { flex-shrink: 0; }
.topbar-right { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.node-badge { font-size: 12px; color: #64748b; background: #f1f5f9; padding: 2px 10px; border-radius: 12px; }

.editor-body { flex: 1; display: flex; overflow: hidden; }
.editor-left { width: 200px; min-width: 200px; background: #fff; border-right: 1px solid #e2e8f0; display: flex; flex-direction: column; overflow-y: auto; }
.palette-title { font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; padding: 16px 16px 8px; }
.palette-list { padding: 4px 8px 16px; display: flex; flex-direction: column; gap: 2px; }
.palette-item { display: flex; align-items: center; gap: 10px; padding: 10px; border-radius: 8px; cursor: pointer; transition: all 0.15s; }
.palette-item:hover { background: #f1f5f9; }
.palette-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.palette-info { min-width: 0; }
.palette-label { display: block; font-size: 13px; font-weight: 500; color: #1e293b; line-height: 1.3; }
.palette-desc  { display: block; font-size: 11px; color: #94a3b8; line-height: 1.2; }

.editor-center { flex: 1; position: relative; background: #f8fafc; }
.editor-canvas { position: absolute; inset: 0; }

.editor-right { width: 300px; min-width: 300px; background: #fff; border-left: 1px solid #e2e8f0; display: flex; flex-direction: column; overflow-y: auto; }
.config-header { display: flex; align-items: center; justify-content: space-between; padding: 16px 16px 0; }
.config-header h4 { margin: 0; font-size: 14px; font-weight: 600; color: #1e293b; }
.config-type-badge { display: inline-flex; align-items: center; gap: 4px; margin: 12px 16px; padding: 4px 12px; border-radius: 6px; font-size: 12px; font-weight: 500; border: 1px solid; width: fit-content; }
.config-form { padding: 0 16px 16px; }
.config-empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #94a3b8; padding: 24px; text-align: center; }
.config-empty p { margin: 8px 0 0; font-size: 13px; }
.config-hint { font-size: 12px !important; color: #cbd5e1; }

.edge-mode-bar { display: flex; align-items: center; gap: 8px; padding: 10px 16px; background: #fef3c7; border-bottom: 1px solid #fbbf24; font-size: 13px; color: #b45309; flex-shrink: 0; }
.edge-mode-bar strong { font-weight: 600; }

/* ========== Detail ========== */
.detail-header { display: flex; align-items: center; gap: 24px; margin-bottom: 28px; flex-wrap: wrap; }
.detail-title { flex: 1; min-width: 200px; }
.detail-title h2 { font-size: 24px; font-weight: 700; color: #1e293b; margin: 0 0 8px; }
.loading-tip { text-align: center; color: #94a3b8; padding: 60px 0; font-size: 14px; }
.detail-content { display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 20px; }
.detail-card { background: #fff; border-radius: 14px; padding: 24px; border: 1px solid #e2e8f0; }
.detail-card h3 { font-size: 16px; font-weight: 600; color: #1e293b; margin: 0 0 16px; }
.info-row { display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #f1f5f9; }
.info-row:last-child { border-bottom: none; }
.info-row .label { color: #64748b; font-size: 14px; }
.info-row .value { font-weight: 600; color: #1e293b; }
.node-list { display: flex; flex-direction: column; gap: 8px; }
.node-item { display: flex; align-items: center; gap: 10px; padding: 10px 12px; background: #f8fafc; border-radius: 8px; }
.node-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.node-name { font-weight: 600; color: #1e293b; font-size: 13px; }
.node-type { font-size: 12px; color: #64748b; margin-left: 6px; }
.empty-text { color: #94a3b8; text-align: center; padding: 20px; font-size: 13px; }
.graph-preview { height: 350px; border-radius: 8px; background: #f8fafc; border: 1px solid #e2e8f0; }

/* ========== List (KB style) ========== */
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 28px; flex-wrap: wrap; gap: 16px; }
.page-header h2 { font-size: 24px; font-weight: 700; color: #1e293b; margin: 0 0 8px; }
.page-desc { color: #64748b; font-size: 14px; margin: 0; }
.header-actions { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.search-input { width: 240px; }

/* KB-style card grid */
.kb-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; flex: 1; overflow-y: auto; align-content: start; padding-bottom: 8px; }
.kb-card { background: #fff; border-radius: 16px; padding: 24px; cursor: pointer; transition: all 0.3s; border: 1px solid #f3f4f6; position: relative; overflow: hidden; }
.kb-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, var(--card-color, #3b82f6) 0%, transparent 100%); }
.kb-card:hover { box-shadow: 0 12px 32px rgba(0,0,0,0.08); border-color: #e5e7eb; transform: translateY(-4px); }
.add-card { border: 2px dashed #e2e8f0; }
.add-card:hover { border-color: #3b82f6; }
.add-card::before { display: none; }

.card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.kb-icon { width: 52px; height: 52px; border-radius: 14px; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 24px; flex-shrink: 0; }
.card-actions { opacity: 0; transition: opacity 0.2s; }
.kb-card:hover .card-actions { opacity: 1; }
.more-btn { color: #9ca3af; }
.more-btn:hover { color: #3b82f6; }

.card-body { margin-bottom: 22px; }
.kb-name { font-size: 17px; font-weight: 600; margin: 0 0 10px 0; color: #111827; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.kb-meta { font-size: 13px; color: #9ca3af; margin: 0 0 12px 0; }
.kb-desc { font-size: 14px; color: #6b7280; margin: 0; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; line-height: 1.7; }

.card-footer { display: flex; gap: 24px; padding-top: 20px; border-top: 1px solid #f3f4f6; }
.stat-item { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #9ca3af; }

/* ========== Responsive ========== */
@media (max-width: 1280px) {
  .detail-content { grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); }
  .graph-preview { height: 300px; }
  .editor-right { width: 260px; min-width: 260px; }
}
@media (max-width: 1024px) {
  .page-header h2, .detail-title h2 { font-size: 20px; }
  .kb-grid { grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 16px; }
  .editor-left { width: 160px; min-width: 160px; }
  .editor-right { width: 240px; min-width: 240px; }
  .kb-card { padding: 20px; }
  .card-footer { gap: 16px; }
}
@media (max-width: 768px) {
  .page-header, .detail-header { flex-direction: column; gap: 16px; align-items: stretch; }
  .header-actions { width: 100%; }
  .search-input { flex: 1; width: 100%; }
  .kb-grid, .detail-content { grid-template-columns: 1fr; gap: 16px; }
  .detail-card { padding: 16px; }
  .graph-preview { height: 250px; }
  .kb-card { padding: 20px; }
  .editor-left { display: none; }
  .editor-right { width: 100%; min-width: 0; max-height: 40vh; border-left: none; border-top: 1px solid #e2e8f0; }
  .editor-body { flex-direction: column; }
  .topbar-center { display: none; }
  .editor-title-input { max-width: 160px; }
}
@media (max-width: 480px) {
  .page-header h2, .detail-title h2 { font-size: 18px; }
  .detail-card { padding: 14px; }
  .info-row .label, .info-row .value { font-size: 13px; }
  .detail-header { gap: 12px; }
  .header-actions { flex-wrap: wrap; gap: 8px; }
  .kb-card { padding: 16px; }
  .kb-icon { width: 44px; height: 44px; }
  .kb-name { font-size: 15px; }
  .kb-desc { font-size: 13px; }
  .card-footer { flex-direction: column; gap: 12px; }
  .stat-item { font-size: 12px; }
  .el-dialog { width: 95% !important; margin: 5px !important; }
  .editor-title-input { max-width: 120px; }
}
</style>
