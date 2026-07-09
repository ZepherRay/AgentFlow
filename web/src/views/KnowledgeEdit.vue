<template>
  <div class="kb-edit-container">
    <div class="edit-sidebar">
      <div class="sidebar-header" @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        <div class="header-info">
          <div class="kb-icon-sm" :style="{ background: iconColor }">
            <el-icon><Folder /></el-icon>
          </div>
          <div class="kb-info">
            <div class="kb-name">{{ kbInfo.name }}</div>
            <div class="kb-desc">{{ kbInfo.description }}</div>
          </div>
        </div>
      </div>
      <div class="sidebar-menu">
        <div :class="{ active: activeTab === 'documents' }" @click="activeTab = 'documents'; selectedDoc = null">
          <el-icon><FileText /></el-icon>
          <span>文档列表</span>
        </div>
        <div :class="{ active: activeTab === 'search' }" @click="activeTab = 'search'">
          <el-icon><Search /></el-icon>
          <span>知识检索</span>
        </div>
        <div :class="{ active: activeTab === 'config' }" @click="activeTab = 'config'">
          <el-icon><Setting /></el-icon>
          <span>配置</span>
        </div>
      </div>
    </div>

    <div class="edit-content">
      <template v-if="activeTab === 'documents'">
        <template v-if="!selectedDoc">
          <div class="tab-header">
            <div class="header-left">
              <h3>文档列表</h3>
              <span class="doc-count">共 {{ documents.length }} 个文档</span>
            </div>
            <div class="header-right">
              <el-button type="primary" @click="showImportDialog = true">
                <el-icon><Plus /></el-icon>
                导入文档
              </el-button>
            </div>
          </div>
          <div v-if="documents.length === 0" class="empty-state">
            <el-icon :size="48" color="#909399"><FolderOpened /></el-icon>
            <p>暂无文档，点击上方按钮导入文档</p>
          </div>
          <el-table v-else :data="documents" style="width: 100%">
            <el-table-column prop="filename" label="文件名" min-width="200">
              <template #default="{ row }">
                <span class="doc-link" @click="handleViewChunks(row)">{{ row.filename }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="file_type" label="类型" width="80" />
            <el-table-column prop="file_size" label="大小" width="100">
              <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
            </el-table-column>
            <el-table-column prop="char_count" label="字符数" width="100">
              <template #default="{ row }">{{ row.char_count.toLocaleString() }}</template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="chunk_count" label="分片数" width="80" />
            <el-table-column prop="created_at" label="上传时间" width="160">
              <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="180">
              <template #default="{ row }">
                <el-button size="small" @click="handleViewChunks(row)">查看分段</el-button>
                <el-button size="small" type="danger" @click="handleDeleteDocument(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </template>
        <template v-else>
          <div class="tab-header">
            <div class="header-left">
              <el-button type="text" @click="selectedDoc = null">
                <el-icon><ArrowLeft /></el-icon>返回文档列表
              </el-button>
              <span class="doc-title">{{ selectedDoc.filename }}</span>
              <span class="chunk-count">共 {{ chunks.length }} 个分段</span>
            </div>
          </div>
          <div v-if="chunks.length === 0" class="empty-state">
            <el-icon :size="48" color="#909399"><FileText /></el-icon>
            <p>暂无分段数据</p>
          </div>
          <el-table v-else :data="chunks" style="width: 100%">
            <el-table-column prop="chunk_index" label="序号" width="80" />
            <el-table-column prop="content" label="内容" min-width="500">
              <template #default="{ row }">
                <div class="chunk-preview">{{ row.content }}</div>
              </template>
            </el-table-column>
            <el-table-column prop="token_count" label="字符数" width="100" />
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button size="small" @click="handleEditChunk(row)">编辑</el-button>
                <el-button size="small" type="danger" @click="handleDeleteChunk(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </template>
      </template>

      <template v-else-if="activeTab === 'search'">
        <div class="search-section">
          <div class="search-config-panel">
            <h4>知识检索配置</h4>
            <el-form :model="searchConfig" label-width="140px">
              <el-form-item label="召回最大条数">
                <el-input-number v-model="searchConfig.top_k" :min="1" :max="20" />
              </el-form-item>
              <el-form-item label="向量相似度权重">
                <el-input-number v-model="searchConfig.vector_weight" :min="0" :max="1" :step="0.1" />
              </el-form-item>
              <el-form-item label="关键词相似度权重">
                <el-input-number v-model="searchConfig.keyword_weight" :min="0" :max="1" :step="0.1" />
              </el-form-item>
              <el-form-item label="权重总和">
                <el-tag type="info">{{ (searchConfig.vector_weight + searchConfig.keyword_weight).toFixed(2) }}</el-tag>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :loading="saveConfigLoading" @click="handleSaveSearchConfig">保存配置</el-button>
              </el-form-item>
            </el-form>
          </div>
          <div class="search-input-panel">
            <el-input v-model="searchQuery" placeholder="输入检索关键词" style="width: 400px; margin-bottom: 20px">
              <template #prefix><el-icon><Search /></el-icon></template>
              <template #append>
                <el-button @click="handleSearch">检索</el-button>
              </template>
            </el-input>
            <div v-if="searchResults.length">
              <h4>文档预览</h4>
              <div class="result-summary">共 {{ searchResults.length }} 个分段</div>
              <div v-for="(result, idx) in searchResults" :key="idx" class="search-result-item">
                <div class="result-header">
                  <span class="result-index">{{ idx + 1 }}</span>
                  <span class="result-score">相似度: {{ (result.score * 100).toFixed(1) }}%</span>
                </div>
                <div class="result-content">{{ result.content }}</div>
                <div class="result-source">来源: {{ result.filename }}</div>
              </div>
            </div>
          </div>
        </div>
      </template>

      <template v-else-if="activeTab === 'config'">
        <div class="config-section">
          <div class="icon-upload">
            <div class="icon-circle" :style="{ background: iconColor }">
              <el-icon :size="32"><Folder /></el-icon>
            </div>
            <el-button type="text" size="small">更换图标</el-button>
          </div>
          <el-form ref="configFormRef" :model="configForm" :rules="configRules" label-width="80px">
            <el-form-item label="名称" prop="name">
              <el-input v-model="configForm.name" />
            </el-form-item>
            <el-form-item label="描述" prop="description">
              <el-input v-model="configForm.description" type="textarea" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="saveLoading" @click="handleSave">保存</el-button>
            </el-form-item>
          </el-form>
        </div>
      </template>
    </div>

    <el-dialog v-model="showImportDialog" title="导入文档" width="700px" :close-on-click-modal="false">
      <el-steps :active="importStep" align-center>
        <el-step title="上传文件" />
        <el-step title="参数设置" />
        <el-step title="分段预览" />
        <el-step title="确认导入" />
      </el-steps>
      <template v-if="importStep === 0">
        <div class="import-step-content">
          <el-upload ref="uploadRef" :action="`/api/v1/knowledge/bases/${kbId}/documents`" :headers="{ Authorization: `Bearer ${api.getToken()}` }" :on-success="handleUploadSuccess" :on-error="handleUploadError" :before-upload="beforeUpload" :file-list="uploadedFiles" accept=".pdf,.doc,.docx,.txt,.xlsx,.xls" drag multiple :auto-upload="false">
            <el-icon :size="48"><Upload /></el-icon>
            <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
            <div class="el-upload__tip" slot="tip">支持 PDF、Word、Excel、TXT 格式，可多选</div>
          </el-upload>
          <div v-if="uploadedFiles.length" class="upload-actions">
            <el-button type="primary" @click="submitFiles">确认上传</el-button>
          </div>
        </div>
      </template>
      <template v-else-if="importStep === 1">
        <div class="import-step-content">
          <el-form :model="importConfig" label-width="120px">
            <el-form-item label="分段大小(字符)">
              <el-input-number v-model="importConfig.chunk_size" :min="64" :max="4096" :step="64" />
              <span class="form-hint">建议512-1024</span>
            </el-form-item>
            <el-form-item label="重叠大小(字符)">
              <el-input-number v-model="importConfig.chunk_overlap" :min="0" :max="512" :step="16" />
              <span class="form-hint">建议64-256</span>
            </el-form-item>
            <el-form-item label="分段方式">
              <el-radio-group v-model="importConfig.splitter_type">
                <el-radio label="simple">简单分段</el-radio>
                <el-radio label="recursive">递归分段</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-form>
        </div>
      </template>
      <template v-else-if="importStep === 2">
        <div class="import-step-content">
          <div v-if="previewLoading" class="preview-loading">
            <el-spinner />
            <p>正在分析文档...</p>
          </div>
          <div v-else>
            <div class="preview-summary">
              <el-alert title="共 {{ previewResults.length }} 个文档，预计生成 {{ totalChunks }} 个分段" type="info" :closable="false" />
            </div>
            <div v-for="(result, idx) in previewResults" :key="idx" class="preview-doc">
              <div class="preview-doc-header">
                <span class="doc-title">{{ result.filename }}</span>
                <span class="doc-stats">{{ result.total_chunks }} 个分段</span>
              </div>
              <el-collapse>
                <el-collapse-item v-for="(chunk, cIdx) in result.chunks.slice(0, 3)" :key="cIdx" :title="`分段 ${chunk.index} (${chunk.char_count} 字符)`">
                  <div class="chunk-content">{{ chunk.content }}</div>
                </el-collapse-item>
                <div v-if="result.chunks.length > 3" class="more-chunks">还有 {{ result.chunks.length - 3 }} 个分段未显示...</div>
              </el-collapse>
            </div>
          </div>
        </div>
      </template>
      <template v-else-if="importStep === 3">
        <div class="import-step-content">
          <el-card>
            <div class="confirm-info">
              <div class="info-item"><span class="info-label">待导入文档:</span><span class="info-value">{{ uploadedDocIds.length }} 个</span></div>
              <div class="info-item"><span class="info-label">分段大小:</span><span class="info-value">{{ importConfig.chunk_size }} 字符</span></div>
              <div class="info-item"><span class="info-label">重叠大小:</span><span class="info-value">{{ importConfig.chunk_overlap }} 字符</span></div>
              <div class="info-item"><span class="info-label">预计分段数:</span><span class="info-value">{{ totalChunks }} 个</span></div>
            </div>
            <el-alert title="导入后将自动进行文档解析和向量化，此过程可能需要几分钟" type="warning" :closable="false" />
          </el-card>
        </div>
      </template>
      <template #footer>
        <el-button v-if="importStep > 0" @click="importStep--">上一步</el-button>
        <el-button v-if="importStep < 2" type="primary" @click="nextStep">下一步</el-button>
        <el-button v-if="importStep === 2" type="primary" @click="doConfirmImport">确认导入</el-button>
        <el-button v-if="importStep === 3" type="primary" @click="closeImportDialog">完成</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showEditDialog" title="编辑分段" width="600px">
      <el-form :model="editForm" label-width="60px">
        <el-form-item label="内容">
          <el-input v-model="editForm.content" type="textarea" :rows="10" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveChunk">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showDetailDialog" title="文档详情" width="500px">
      <div v-if="selectedDoc" class="doc-detail">
        <div class="detail-item"><span class="detail-label">文件名:</span><span class="detail-value">{{ selectedDoc.filename }}</span></div>
        <div class="detail-item"><span class="detail-label">类型:</span><span class="detail-value">{{ selectedDoc.file_type }}</span></div>
        <div class="detail-item"><span class="detail-label">大小:</span><span class="detail-value">{{ formatSize(selectedDoc.file_size) }}</span></div>
        <div class="detail-item"><span class="detail-label">字符数:</span><span class="detail-value">{{ selectedDoc.char_count.toLocaleString() }}</span></div>
        <div class="detail-item"><span class="detail-label">状态:</span><el-tag :type="getStatusType(selectedDoc.status)">{{ getStatusLabel(selectedDoc.status) }}</el-tag></div>
        <div class="detail-item"><span class="detail-label">分片数:</span><span class="detail-value">{{ selectedDoc.chunk_count }}</span></div>
        <div class="detail-item"><span class="detail-label">上传时间:</span><span class="detail-value">{{ formatDate(selectedDoc.created_at) }}</span></div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Folder, FileText, Search, Setting, Plus, Upload, FolderOpened } from '@element-plus/icons-vue'
import { api } from '../api'

const route = useRoute()
const router = useRouter()
const kbId = computed(() => parseInt(route.params.id))

const kbInfo = reactive({ name: '', description: '' })
const activeTab = ref('documents')
const documents = ref([])
const searchQuery = ref('')
const searchResults = ref([])
const showImportDialog = ref(false)
const showDetailDialog = ref(false)
const showEditDialog = ref(false)
const selectedDoc = ref(null)
const chunks = ref([])
const configFormRef = ref(null)
const uploadRef = ref(null)
const saveLoading = ref(false)
const saveConfigLoading = ref(false)

const importStep = ref(0)
const uploadedFiles = ref([])
const uploadedDocIds = ref([])
const previewResults = ref([])
const previewLoading = ref(false)

const importConfig = reactive({ chunk_size: 512, chunk_overlap: 128, splitter_type: 'simple' })
const searchConfig = reactive({ top_k: 5, vector_weight: 0.7, keyword_weight: 0.3 })
const editForm = reactive({ content: '', chunkId: null })

const configForm = reactive({ name: '', description: '' })
const configRules = { name: [{ required: true, message: '请输入名称', trigger: 'blur' }], description: [{ required: true, message: '请输入描述', trigger: 'blur' }] }

const colors = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399']
const iconColor = computed(() => colors[kbId.value % colors.length])
const totalChunks = computed(() => previewResults.value.reduce((sum, r) => sum + r.total_chunks, 0))

function goBack() { router.push('/knowledge') }

function formatSize(bytes) {
  if (!bytes) return '0 B'
  const k = 1024
  if (bytes < k) return bytes + ' B'
  if (bytes < k * k) return (bytes / k).toFixed(1) + ' KB'
  return (bytes / (k * k)).toFixed(1) + ' MB'
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

function getStatusType(status) {
  const types = { uploaded: 'warning', parsing: 'info', chunking: 'info', embedding: 'info', completed: 'success', failed: 'danger' }
  return types[status] || 'info'
}

function getStatusLabel(status) {
  const labels = { uploaded: '已上传', parsing: '解析中', chunking: '切分中', embedding: '向量化中', completed: '完成', failed: '失败' }
  return labels[status] || status
}

onMounted(() => { loadKbInfo(); loadSearchConfig() })

watch(activeTab, (tab) => {
  if (tab === 'documents') { loadDocuments() }
})

async function loadKbInfo() {
  try {
    const res = await api.knowledge.get(kbId.value)
    Object.assign(kbInfo, res.data)
    Object.assign(configForm, { name: res.data.name, description: res.data.description })
  } catch (error) { ElMessage.error(error.message || '加载失败') }
}

async function loadDocuments() {
  try {
    const res = await api.knowledge.listDocuments(kbId.value)
    documents.value = res.data
  } catch (error) { ElMessage.error(error.message || '加载失败') }
}

async function handleViewChunks(doc) {
  selectedDoc.value = doc
  try {
    const res = await api.knowledge.listChunks(doc.id)
    chunks.value = res.data
  } catch (error) { ElMessage.error(error.message || '加载失败') }
}

async function handleDeleteDocument(doc) {
  try {
    await ElMessageBox.confirm(`确定删除文档 "${doc.filename}" 吗？`, '确认删除', { type: 'warning' })
    await api.knowledge.deleteDocument([doc.id])
    ElMessage.success('删除成功')
    loadDocuments()
  } catch (error) { if (error !== 'cancel') { ElMessage.error(error.message || '删除失败') } }
}

async function handleEditChunk(chunk) {
  editForm.content = chunk.content
  editForm.chunkId = chunk.id
  showEditDialog.value = true
}

async function handleSaveChunk() {
  try {
    await api.knowledge.updateChunk(editForm.chunkId, { content: editForm.content })
    ElMessage.success('保存成功')
    showEditDialog.value = false
    if (selectedDoc.value) { await handleViewChunks(selectedDoc.value) }
  } catch (error) { ElMessage.error(error.message || '保存失败') }
}

async function handleDeleteChunk(chunk) {
  try {
    await ElMessageBox.confirm('确定删除该分段吗？', '确认删除', { type: 'warning' })
    await api.knowledge.deleteChunk([chunk.id])
    ElMessage.success('删除成功')
    if (selectedDoc.value) { await handleViewChunks(selectedDoc.value) }
  } catch (error) { if (error !== 'cancel') { ElMessage.error(error.message || '删除失败') } }
}

async function handleSearch() {
  if (!searchQuery.value.trim()) return
  try {
    const res = await api.knowledge.search({ query: searchQuery.value, kb_id: kbId.value, top_k: searchConfig.top_k })
    searchResults.value = res.data
  } catch (error) { ElMessage.error(error.message || '检索失败') }
}

async function loadSearchConfig() {
  try {
    const res = await api.knowledge.getSearchConfig(kbId.value)
    Object.assign(searchConfig, res.data)
  } catch (error) { console.log('Load config error:', error) }
}

async function handleSaveSearchConfig() {
  saveConfigLoading.value = true
  try {
    await api.knowledge.saveSearchConfig(kbId.value, searchConfig)
    ElMessage.success('保存成功')
  } catch (error) { ElMessage.error(error.message || '保存失败') } finally { saveConfigLoading.value = false }
}

async function handleSave() {
  await configFormRef.value.validate()
  saveLoading.value = true
  try {
    await api.knowledge.update(kbId.value, configForm)
    Object.assign(kbInfo, configForm)
    ElMessage.success('保存成功')
  } catch (error) { ElMessage.error(error.message || '保存失败') } finally { saveLoading.value = false }
}

function beforeUpload(file) {
  const types = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword', 'text/plain', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel']
  if (!types.includes(file.type)) { ElMessage.error('不支持的文件类型'); return false }
  return true
}

async function submitFiles() {
  const files = uploadRef.value.uploadFiles
  if (!files.length) { ElMessage.warning('请先选择文件'); return }
  for (const file of files) {
    try {
      const res = await api.knowledge.uploadDocument(kbId.value, file.raw)
      uploadedDocIds.value.push(res.data.id)
    } catch (error) { ElMessage.error(`上传 ${file.name} 失败: ${error.message}`) }
  }
  uploadedFiles.value = files
  importStep.value = 1
}

async function nextStep() {
  if (importStep.value === 1) { await loadPreview() }
  importStep.value++
}

async function loadPreview() {
  previewLoading.value = true
  try {
    const res = await api.knowledge.importPreview(kbId.value, { file_ids: uploadedDocIds.value, config: importConfig })
    previewResults.value = res.data
  } catch (error) { ElMessage.error('预览失败: ' + error.message) } finally { previewLoading.value = false }
}

async function doConfirmImport() {
  try {
    await api.knowledge.confirmImport(kbId.value, { file_ids: uploadedDocIds.value, config: importConfig })
    ElMessage.success('导入任务已启动')
    importStep.value = 3
  } catch (error) { ElMessage.error('导入失败: ' + error.message) }
}

function closeImportDialog() {
  showImportDialog.value = false
  importStep.value = 0
  uploadedFiles.value = []
  uploadedDocIds.value = []
  previewResults.value = []
  loadDocuments()
}
</script>

<style scoped>
.kb-edit-container { display: flex; height: calc(100vh - 60px) }
.edit-sidebar { width: 240px; background: #fff; border-right: 1px solid #e5e7eb; display: flex; flex-direction: column }
.sidebar-header { padding: 16px; cursor: pointer; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid #f0f0f0 }
.header-info { flex: 1; display: flex; align-items: center; gap: 10px }
.kb-icon-sm { width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #fff; flex-shrink: 0 }
.kb-info { flex: 1; min-width: 0 }
.kb-info .kb-name { font-size: 15px; font-weight: 600; color: #303133; white-space: nowrap; overflow: hidden; text-overflow: ellipsis }
.kb-info .kb-desc { font-size: 12px; color: #909399; white-space: nowrap; overflow: hidden; text-overflow: ellipsis }
.sidebar-menu { flex: 1; padding: 12px; display: flex; flex-direction: column; gap: 4px }
.sidebar-menu div { display: flex; align-items: center; gap: 10px; padding: 10px 12px; border-radius: 8px; cursor: pointer; font-size: 14px; color: #606266; transition: all 0.2s }
.sidebar-menu div:hover { background: #f5f7fa }
.sidebar-menu div.active { background: #ecf5ff; color: #409eff }
.edit-content { flex: 1; padding: 24px; overflow-y: auto; background: #f3f4f6 }
.tab-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px }
.header-left { display: flex; align-items: center; gap: 12px }
.header-left h3 { font-size: 16px; font-weight: 600; margin: 0 }
.doc-count { font-size: 13px; color: #909399 }
.doc-title { font-size: 16px; font-weight: 600; color: #303133 }
.chunk-count { font-size: 13px; color: #909399 }
.doc-link { color: #409eff; cursor: pointer }
.doc-link:hover { text-decoration: underline }
.empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 60px 0; color: #909399 }
.empty-state p { margin-top: 16px; font-size: 14px }
.chunk-preview { font-size: 13px; line-height: 1.5; color: #606266; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden }
.search-section { display: flex; gap: 24px }
.search-config-panel { width: 350px; background: #fff; padding: 24px; border-radius: 8px }
.search-config-panel h4 { font-size: 14px; font-weight: 600; margin: 0 0 16px 0 }
.search-input-panel { flex: 1; background: #fff; padding: 24px; border-radius: 8px }
.search-input-panel h4 { font-size: 14px; font-weight: 600; margin: 0 0 16px 0 }
.result-summary { font-size: 12px; color: #909399; margin-bottom: 12px }
.search-result-item { padding: 16px; border: 1px solid #e5e7eb; border-radius: 6px; margin-bottom: 12px }
.result-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px }
.result-index { font-size: 12px; color: #409eff; font-weight: 500 }
.result-score { font-size: 12px; color: #409eff }
.result-content { font-size: 14px; color: #303133; line-height: 1.6; margin-bottom: 8px }
.result-source { font-size: 12px; color: #909399 }
.config-section { background: #fff; padding: 32px; border-radius: 8px }
.icon-upload { display: flex; flex-direction: column; align-items: center; margin-bottom: 32px }
.icon-circle { width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #fff; margin-bottom: 8px }
.import-step-content { padding: 20px 0 }
.upload-actions { margin-top: 16px; text-align: right }
.form-hint { margin-left: 12px; font-size: 12px; color: #909399 }
.preview-loading { display: flex; flex-direction: column; align-items: center; padding: 40px 0 }
.preview-loading p { margin-top: 16px; color: #909399 }
.preview-summary { margin-bottom: 20px }
.preview-doc { margin-bottom: 16px }
.preview-doc-header { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: #f5f7fa; border-radius: 4px; margin-bottom: 8px }
.preview-doc .doc-title { font-weight: 500; font-size: 14px }
.doc-stats { font-size: 12px; color: #909399 }
.chunk-content { font-size: 13px; line-height: 1.6; color: #606266; padding: 8px; background: #fafafa; border-radius: 4px; word-break: break-all }
.more-chunks { padding: 8px 12px; font-size: 12px; color: #909399; text-align: center }
.confirm-info { display: flex; flex-direction: column; gap: 12px; margin-bottom: 16px }
.info-item { display: flex; justify-content: space-between }
.info-label { font-size: 14px; color: #606266 }
.info-value { font-size: 14px; font-weight: 500; color: #303133 }
.doc-detail { display: flex; flex-direction: column; gap: 12px }
.detail-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #f0f0f0 }
.detail-label { font-size: 14px; color: #606266 }
.detail-value { font-size: 14px; color: #303133 }
</style>