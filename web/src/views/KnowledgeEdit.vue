<template>
  <div class="kb-edit-container">
    <aside class="edit-sidebar">
      <div class="sidebar-header" @click="goBack">
        <el-icon :size="18"><ArrowLeft /></el-icon>
        <div class="header-info">
          <div class="kb-icon-sm" v-if="!kbInfo.icon" :style="{ background: iconColor }">
            <el-icon :size="16"><Folder /></el-icon>
          </div>
          <img v-else :src="getIconUrl(kbInfo.icon)" class="kb-icon-sm-img" />
          <div class="kb-info">
            <div class="kb-name">{{ kbInfo.name }}</div>
            <div class="kb-desc">{{ kbInfo.description }}</div>
          </div>
        </div>
      </div>
      <nav class="sidebar-menu">
        <div :class="{ active: activeTab === 'documents' }" @click="activeTab = 'documents'; selectedDoc = null">
          <el-icon :size="16"><Document /></el-icon>
          <span>文档列表</span>
        </div>
        <div :class="{ active: activeTab === 'search' }" @click="activeTab = 'search'">
          <el-icon :size="16"><Search /></el-icon>
          <span>知识检索</span>
        </div>
        <div :class="{ active: activeTab === 'config' }" @click="activeTab = 'config'">
          <el-icon :size="16"><Setting /></el-icon>
          <span>配置</span>
        </div>
      </nav>
    </aside>

    <main class="edit-content">
      <!-- ========== 文档列表 ========== -->
      <template v-if="activeTab === 'documents'">
        <div class="doc-page">
          <div class="page-toolbar">
            <div class="toolbar-left">
              <el-input v-model="searchText" placeholder="搜索文档名称..." :prefix-icon="Search" clearable class="search-input" @keyup.enter="loadDocuments" />
              <el-button type="primary" @click="loadDocuments">查询</el-button>
              <el-button @click="searchText = ''; loadDocuments()">重置</el-button>
            </div>
            <el-button type="primary" @click="showImportDialog = true">
              <el-icon><Plus /></el-icon>
              <span>导入文件</span>
            </el-button>
          </div>
          <div class="doc-table-wrapper">
            <el-table :data="documents" class="doc-table" header-cell-class-name="table-header" row-class-name="table-row">
              <el-table-column prop="filename" label="文件名" min-width="240">
                <template #default="{ row }">
                  <div class="doc-name-cell">
                    <el-icon :size="16" color="#6b7280"><Document /></el-icon>
                    <span class="doc-name">{{ row.filename }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="字符数" width="120" align="center">
                <template #default="{ row }">
                  <span class="metric-tag">{{ formatChars(row.char_count) }}</span>
                </template>
              </el-table-column>
              <el-table-column label="知识条数" width="120" align="center">
                <template #default="{ row }">
                  <span class="metric-tag">{{ row.chunk_count }}</span>
                </template>
              </el-table-column>
              <el-table-column label="创建/更新时间" width="180">
                <template #default="{ row }">{{ formatDateTime(row.updated_at || row.created_at) }}</template>
              </el-table-column>
              <el-table-column label="操作" width="200" fixed="right">
                <template #default="{ row }">
                  <div class="action-btns">
                    <el-button link type="primary" size="small" @click="handleViewChunks(row)">查看分段</el-button>
                    <el-dropdown trigger="click" @command="(cmd) => handleDocAction(cmd, row)">
                      <el-button link type="info" size="small">
                        <el-icon :size="16"><MoreFilled /></el-icon>
                      </el-button>
                      <template #dropdown>
                        <el-dropdown-menu>
                          <el-dropdown-item command="download">
                            <el-icon><Download /></el-icon>下载
                          </el-dropdown-item>
                          <el-dropdown-item command="delete" divided>
                            <span class="danger-text">删除</span>
                          </el-dropdown-item>
                        </el-dropdown-menu>
                      </template>
                    </el-dropdown>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>

        <!-- ========== 分段详情 ========== -->
        <template v-if="selectedDoc">
          <div class="chunks-page">
            <div class="chunks-header">
              <el-button link type="primary" @click="selectedDoc = null">
                <el-icon><ArrowLeft /></el-icon>返回文档列表
              </el-button>
              <el-divider direction="vertical" />
              <span class="chunks-title">{{ selectedDoc.filename }}</span>
              <span class="chunks-meta">{{ chunksTotal }} 个分段</span>
            </div>
            <div v-if="chunks.length === 0" class="empty-state">
              <el-icon :size="48" color="#d1d5db"><Document /></el-icon>
              <p>暂无分段数据</p>
            </div>
            <div v-else class="chunks-list-container">
              <div v-for="chunk in chunks" :key="chunk.id" class="chunk-card">
                <div class="chunk-card-body">
                  <span class="chunk-index">#{{ chunk.chunk_index }}</span>
                  <div class="chunk-content">{{ chunk.content }}</div>
                </div>
                <div class="chunk-card-actions">
                  <el-button size="small" text @click="handleEditChunk(chunk)">编辑</el-button>
                  <el-button size="small" text type="danger" @click="handleDeleteChunk(chunk)">删除</el-button>
                </div>
              </div>
              <div class="chunks-pagination">
                <div class="pagination-left">
                  <span class="pagination-total">共 {{ chunksTotal }} 条</span>
                  <el-select v-model="chunksPageSize" class="page-size-select" size="small">
                    <el-option label="10条/页" :value="10" />
                    <el-option label="20条/页" :value="20" />
                    <el-option label="50条/页" :value="50" />
                  </el-select>
                </div>
                <el-pagination
                  v-model:current-page="chunksCurrentPage"
                  :page-size="chunksPageSize"
                  :total="chunksTotal"
                  layout="prev, pager, next"
                  background
                  @current-change="handleChunksPageChange"
                  @size-change="handleChunksSizeChange"
                />
              </div>
            </div>
          </div>
        </template>
      </template>

      <!-- ========== 知识检索 ========== -->
      <template v-else-if="activeTab === 'search'">
        <div class="search-section">
          <div class="search-config-panel">
            <div class="panel-header">
              <el-icon :size="20"><Setting /></el-icon>
              <span>检索配置</span>
            </div>
            <el-form :model="searchConfig" label-position="top" class="search-config-form">
              <el-form-item label="召回最大条数">
                <el-input-number v-model="searchConfig.top_k" :min="1" :max="50" controls-position="right" class="config-input" />
              </el-form-item>
              <el-form-item label="向量相似度权重">
                <el-input-number v-model="searchConfig.vector_weight" :min="0" :max="1" :step="0.1" :precision="1" controls-position="right" class="config-input" />
              </el-form-item>
              <el-form-item label="关键词相似度权重">
                <el-input-number v-model="searchConfig.keyword_weight" :min="0" :max="1" :step="0.1" :precision="1" controls-position="right" class="config-input" />
              </el-form-item>
              <el-form-item label="权重总和">
                <el-input-number :model-value="weightSum" disabled controls-position="right" class="config-input" />
              </el-form-item>
              <div class="panel-divider"></div>
              <div class="panel-subheader">RAG 查询参数</div>
              <el-form-item label="重排序保留条数">
                <el-input-number v-model="ragRerankTopN" :min="1" :max="20" controls-position="right" class="config-input" />
              </el-form-item>
              <el-form-item label="生成温度">
                <el-input-number v-model="ragTemperature" :min="0" :max="2" :step="0.1" :precision="1" controls-position="right" class="config-input" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :loading="saveConfigLoading" @click="handleSaveSearchConfig" class="save-config-btn">保存配置</el-button>
              </el-form-item>
            </el-form>
          </div>
          <div class="qa-panel">
            <div class="qa-input-area">
              <el-input
                v-model="ragQuery"
                type="textarea"
                :rows="3"
                placeholder="输入你的问题，AI 将从知识库中检索并生成答案..."
                :disabled="ragLoading"
              />
              <div class="qa-input-actions">
                <div class="qa-params">
                  <el-select v-model="ragOptimizer" size="small" style="width:140px" placeholder="检索优化">
                    <el-option label="无优化" value="none" />
                    <el-option label="HyDE 假设文档" value="hyde" />
                    <el-option label="查询改写" value="rewrite" />
                    <el-option label="多查询扩展" value="multi_query" />
                  </el-select>
                  <el-select v-model="ragModel" size="small" style="width:140px" placeholder="LLM 模型">
                    <el-option v-for="m in availableModels" :key="m" :label="m" :value="m" />
                  </el-select>
                </div>
                <el-button type="primary" @click="handleRagQuery" :loading="ragLoading" size="large">
                  <el-icon><Search /></el-icon>
                  <span>智能问答</span>
                </el-button>
              </div>
            </div>

            <div v-if="ragAnswer" class="qa-answer">
              <div class="qa-answer-header">
                <el-icon :size="18" color="#2563eb"><ChatDotSquare /></el-icon>
                <span>AI 回答</span>
                <span class="qa-latency" v-if="ragLatency">{{ (ragLatency / 1000).toFixed(2) }}s</span>
              </div>
              <div class="qa-answer-content">{{ ragAnswer }}</div>
            </div>

            <div v-if="ragSources.length" class="qa-sources">
              <div class="qa-sources-header">
                <el-icon :size="18" color="#6b7280"><Document /></el-icon>
                <span>参考来源 ({{ ragSources.length }})</span>
                <el-button text size="small" @click="showSources = !showSources">
                  {{ showSources ? '收起' : '展开' }}
                </el-button>
              </div>
              <template v-if="showSources">
                <div v-for="(src, idx) in ragSources" :key="idx" class="qa-source-item">
                  <div class="source-rank">{{ idx + 1 }}</div>
                  <div class="source-body">
                    <div class="source-meta">
                      <span class="source-score">{{ (src.score * 100).toFixed(1) }}%</span>
                      <span class="source-filename">{{ src.filename || '未知' }}</span>
                    </div>
                    <div class="source-content">{{ src.content }}</div>
                  </div>
                </div>
              </template>
            </div>

            <div v-else-if="!ragAnswer && !ragLoading" class="qa-empty">
              <el-icon :size="48" color="#d1d5db"><ChatDotSquare /></el-icon>
              <p>输入问题，AI 自动检索知识库并生成回答</p>
            </div>
          </div>
        </div>
      </template>

      <!-- ========== 配置 ========== -->
      <template v-else-if="activeTab === 'config'">
        <div class="config-section">
          <div class="config-card">
            <label class="form-label">知识库图标</label>
            <div class="icon-upload">
              <div class="icon-circle" @click="triggerIconUpload">
                <img v-if="configForm.icon" :src="getIconUrl(configForm.icon)" class="icon-img" />
                <div v-else class="icon-placeholder">
                  <el-icon :size="24"><Plus /></el-icon>
                </div>
              </div>
              <span class="icon-hint">点击上传图标</span>
              <input type="file" ref="iconInput" accept="image/*" class="hidden-input" @change="handleIconUpload" />
            </div>
          </div>
          <el-form ref="configFormRef" :model="configForm" :rules="configRules" label-width="80px" class="config-form-wrap">
            <el-form-item label="名称" prop="name">
              <el-input v-model="configForm.name" placeholder="请输入知识库名称" />
            </el-form-item>
            <el-form-item label="描述" prop="description">
              <el-input v-model="configForm.description" type="textarea" :rows="4" placeholder="请输入知识库描述" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="saveLoading" @click="handleSave" size="large">保存配置</el-button>
            </el-form-item>
          </el-form>
        </div>
      </template>
    </main>

    <!-- ========== 导入文件弹窗 ========== -->
    <el-dialog v-model="showImportDialog" width="860px" :close-on-click-modal="false" :before-close="closeImportDialog" class="import-dialog">
      <template #header>
        <div class="dialog-header">
          <span class="dialog-title">导入文件</span>
          <el-steps :active="importStep" align-center class="import-steps">
            <el-step title="文件上传" />
            <el-step title="参数设置" />
            <el-step title="分段预览" />
            <el-step title="确认导入" />
          </el-steps>
        </div>
      </template>

      <template v-if="importStep === 0">
        <div class="import-step-content">
          <div class="upload-zone" @click="triggerUpload" @drop.prevent="handleDrop" @dragover.prevent>
            <el-icon :size="56" color="#3b82f6"><UploadFilled /></el-icon>
            <p class="upload-title">点击或将文件拖拽到这里上传</p>
            <p class="upload-hint">支持 TXT / PDF / DOCX / MD / PPT / PPTX 格式，单个文件不超过 20MB</p>
          </div>
          <input type="file" ref="fileInput" accept=".txt,.pdf,.doc,.docx,.md,.ppt,.pptx" multiple class="hidden-input" @change="handleFileSelect" />
          <div v-if="uploadedFiles.length" class="file-list">
            <el-table :data="uploadedFiles" class="upload-table">
              <el-table-column prop="name" label="文件名称" min-width="220">
                <template #default="{ row }">
                  <div class="upload-file-name">
                    <el-icon :size="16"><Document /></el-icon>
                    <span>{{ row.name }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="状态" width="180">
                <template #default="{ row }">
                  <el-progress v-if="row.status === 'uploading'" :percentage="row.progress" :stroke-width="6" />
                  <el-tag v-else-if="row.status === 'done'" type="success" size="small">已上传</el-tag>
                  <el-tag v-else type="info" size="small">待上传</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="大小" width="100" align="center">
                <template #default="{ row }">{{ formatSize(row.size) }}</template>
              </el-table-column>
              <el-table-column label="操作" width="80" align="center">
                <template #default="{ row }">
                  <el-button size="small" text type="danger" @click="removeUploadedFile(row.id)">移除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </template>

      <template v-else-if="importStep === 1">
        <div class="import-step-content">
          <el-form :model="importConfig" label-width="140px" class="config-form">
            <el-form-item label="加载方式">
              <el-select v-model="importConfig.reader_type" placeholder="自动检测" clearable class="config-select">
                <el-option v-for="opt in readerOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
              </el-select>
              <div class="reader-hint">PDF 可选 PyMuPDF / PyPDF2 / Unstructured，其他类型自动</div>
            </el-form-item>
            <el-form-item label="分割器">
              <el-select v-model="importConfig.splitter_type" class="config-select">
                <el-option label="Token 切分器" value="token" />
                <el-option label="句子切分器" value="sentence" />
                <el-option label="语义切分器" value="semantic" />
              </el-select>
            </el-form-item>
            <el-form-item label="分段长度">
              <div class="slider-row">
                <el-slider v-model="importConfig.chunk_size" :min="128" :max="2048" :step="64" show-input />
              </div>
            </el-form-item>
            <el-form-item label="分段重叠">
              <div class="slider-row">
                <el-slider v-model="importConfig.chunk_overlap" :min="0" :max="512" :step="16" show-input />
              </div>
            </el-form-item>
          </el-form>
        </div>
      </template>

      <template v-else-if="importStep === 2">
        <div class="import-step-content">
          <div class="preview-layout">
            <div class="preview-sidebar">
              <div class="preview-file-list">
                <div
                  v-for="file in uploadedFiles"
                  :key="file.id"
                  :class="{ active: selectedPreviewFile === file.id }"
                  class="preview-file-item"
                  @click="selectedPreviewFile = file.id"
                >
                  <el-icon :size="14"><Document /></el-icon>
                  <span>{{ file.name }}</span>
                </div>
              </div>
            </div>
            <div class="preview-content">
              <div class="preview-header">
                <span class="preview-label">文档预览</span>
                <span class="chunk-count">共 {{ currentPreviewChunks.length }} 个分段</span>
              </div>
              <div class="chunk-list">
                <div v-for="(chunk, idx) in pagedPreviewChunks" :key="idx" :class="{ active: idx === previewCurrentPage - 1 }" class="chunk-item">
                  <span class="chunk-number">{{ previewPageStart + idx }}</span>
                  <div class="chunk-text">{{ chunk.content }}</div>
                </div>
              </div>
              <div class="preview-pagination">
                <span class="pagination-total">共 {{ currentPreviewChunks.length }} 条</span>
                <el-pagination
                  v-model:current-page="previewCurrentPage"
                  :page-size="PAGE_SIZE"
                  :total="currentPreviewChunks.length"
                  layout="prev, pager, next"
                  background
                  small
                />
              </div>
            </div>
          </div>
        </div>
      </template>

      <template v-else-if="importStep === 3">
        <div class="import-step-content">
          <el-table :data="confirmFiles" class="confirm-table">
            <el-table-column prop="name" label="文件名称" min-width="300">
              <template #default="{ row }">
                <div class="upload-file-name">
                  <el-icon :size="16"><Document /></el-icon>
                  <span>{{ row.name }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="120" align="center">
              <template #default="{ row }">
                <el-tag type="info" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </template>

      <template #footer>
        <div class="dialog-footer">
          <el-button v-if="importStep > 0" @click="importStep--">上一步</el-button>
          <el-button v-if="importStep === 0 && uploadedFiles.length" type="primary" @click="submitUpload">下一步</el-button>
          <el-button v-if="importStep === 1" type="primary" @click="loadPreview">下一步</el-button>
          <el-button v-if="importStep === 2" type="primary" @click="importStep++">下一步</el-button>
          <el-button v-if="importStep === 3" type="primary" :loading="importLoading" @click="doConfirmImport">开始导入</el-button>
          <el-button @click="closeImportDialog">取消</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- ========== 编辑分段弹窗 ========== -->
    <el-dialog v-model="showEditDialog" title="编辑分段" width="640px" :close-on-click-modal="false" class="edit-dialog">
      <div class="edit-modal-content">
        <el-input
          v-model="editForm.content"
          type="textarea"
          :rows="14"
          class="edit-textarea"
          placeholder="请输入分段内容"
        />
      </div>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveChunk">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Folder, Document, Search, Setting, Plus, MoreFilled, UploadFilled, Download, ChatDotSquare } from '@element-plus/icons-vue'
import { api } from '../api'

const route = useRoute()
const router = useRouter()

const kbId = computed(() => parseInt(route.params.id))

const kbInfo = reactive({ name: '', description: '', icon: '' })
const activeTab = ref(route.query.tab || 'documents')
const documents = ref([])
const searchText = ref('')
const ragQuery = ref('')
const ragAnswer = ref('')
const ragSources = ref([])
const ragLatency = ref(0)
const ragLoading = ref(false)
const ragOptimizer = ref('hyde')
const ragModel = ref('qwen-plus')
const ragTemperature = ref(0.7)
const ragRerankTopN = ref(5)
const availableModels = ref(['qwen-plus', 'qwen-max', 'qwen-turbo'])
const showSources = ref(true)
const showImportDialog = ref(false)
const showEditDialog = ref(false)
const selectedDoc = ref(null)
const chunks = ref([])
const chunksTotal = ref(0)
const chunksCurrentPage = ref(1)
const chunksPageSize = ref(10)
const configFormRef = ref(null)
const saveLoading = ref(false)
const saveConfigLoading = ref(false)
const iconInput = ref(null)
const fileInput = ref(null)

const importStep = ref(0)
const uploadedFiles = ref([])
const uploadedDocIds = ref([])
const previewResults = ref([])
const importLoading = ref(false)
const selectedPreviewFile = ref(null)
const previewCurrentPage = ref(1)

const importConfig = reactive({ file_type: 'document', chunk_size: 512, chunk_overlap: 128, splitter_type: 'sentence', reader_type: null })

const readerOptions = computed(() => {
  const exts = new Set(uploadedFiles.value.map(f => {
    const i = f.name.lastIndexOf('.')
    return i > 0 ? f.name.slice(i).toLowerCase() : ''
  }))
  // PDF: show three reader choices
  if (exts.size === 1 && exts.has('.pdf')) {
    return [
      { value: null, label: '自动检测 (PyMuPDF)' },
      { value: 'pymupdf', label: 'PyMuPDF' },
      { value: 'pypdf2', label: 'PyPDF2' },
      { value: 'unstructured', label: 'Unstructured' },
    ]
  }
  // Mixed or single non-PDF type
  return [
    { value: null, label: '自动检测' },
  ]
})
const searchConfig = reactive({ top_k: 5, vector_weight: 0.7, keyword_weight: 0.3 })
const weightSum = computed(() => searchConfig.vector_weight + searchConfig.keyword_weight)
const editForm = reactive({ content: '', chunkId: null })

const configForm = reactive({ name: '', description: '', icon: '' })
const configRules = {
  name: [{ required: true, message: '请输入知识库名称', trigger: 'blur' }],
  description: [{ required: true, message: '请输入知识库描述', trigger: 'blur' }]
}

const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#6366f1', '#8b5cf6', '#06b6d4', '#ec4899']
const iconColor = computed(() => colors[kbId.value % colors.length])

const confirmFiles = computed(() => uploadedFiles.value.map(f => ({ name: f.name, status: '待导入' })))

const currentPreviewChunks = computed(() => {
  const fileId = selectedPreviewFile.value
  const result = previewResults.value.find(r => r.file_id === fileId)
  return result?.chunks || []
})

const PAGE_SIZE = 10

const pagedPreviewChunks = computed(() => {
  const start = (previewCurrentPage.value - 1) * PAGE_SIZE
  return currentPreviewChunks.value.slice(start, start + PAGE_SIZE)
})

const previewPageStart = computed(() => (previewCurrentPage.value - 1) * PAGE_SIZE + 1)

function goBack() { router.push('/knowledge') }

function getIconUrl(icon) {
  if (!icon) return ''
  if (icon.startsWith('http')) return icon
  if (icon.startsWith('/uploads/')) return icon
  return icon
}

function formatSize(bytes) {
  if (!bytes) return '0 B'
  const k = 1024
  if (bytes < k) return bytes + ' B'
  if (bytes < k * k) return (bytes / k).toFixed(1) + ' KB'
  return (bytes / (k * k)).toFixed(1) + ' MB'
}

function formatChars(count) {
  if (!count) return '0'
  if (count >= 10000) return (count / 10000).toFixed(1) + 'M'
  if (count >= 1000) return (count / 1000).toFixed(1) + 'K'
  return count.toString()
}

function formatDateTime(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

onMounted(() => { loadKbInfo(); loadSearchConfig(); loadRagModels(); loadDocuments() })

watch(activeTab, (tab) => {
  if (tab === 'documents') { loadDocuments() }
  if (tab === 'search') { loadRagModels() }
})

watch(selectedPreviewFile, () => { previewCurrentPage.value = 1 })

async function loadKbInfo() {
  try {
    const res = await api.knowledge.get(kbId.value)
    Object.assign(kbInfo, res.data)
    Object.assign(configForm, { name: res.data.name, description: res.data.description, icon: res.data.icon || '' })
  } catch (error) { ElMessage.error(error.message || '加载失败') }
}

async function loadDocuments() {
  try {
    const res = await api.knowledge.listDocuments(kbId.value)
    documents.value = searchText.value
      ? res.data.filter(d => d.filename.toLowerCase().includes(searchText.value.toLowerCase()))
      : res.data
  } catch (error) { ElMessage.error(error.message || '加载失败') }
}

async function handleViewChunks(doc) {
  selectedDoc.value = doc
  chunksCurrentPage.value = 1
  await loadChunks()
}

async function loadChunks() {
  try {
    const res = await api.knowledge.listChunks(selectedDoc.value.id, chunksCurrentPage.value, chunksPageSize.value)
    chunks.value = res.data.items || []
    chunksTotal.value = res.data.total || 0
  } catch (error) { ElMessage.error(error.message || '加载失败') }
}

function handleChunksPageChange(page) { chunksCurrentPage.value = page; loadChunks() }
function handleChunksSizeChange(size) { chunksPageSize.value = size; chunksCurrentPage.value = 1; loadChunks() }

async function handleDocAction(cmd, doc) {
  if (cmd === 'download') { handleDownload(doc) }
  else if (cmd === 'delete') { handleDeleteDocument(doc) }
}

async function handleDownload(doc) {
  try { api.knowledge.downloadDocument(doc.id) } catch (error) { ElMessage.error('下载失败') }
}

async function handleDeleteDocument(doc) {
  try {
    await ElMessageBox.confirm(`确定删除文档 "${doc.filename}" 吗？删除后不可恢复。`, '删除确认', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
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
    loadChunks()
  } catch (error) { ElMessage.error(error.message || '保存失败') }
}

async function handleDeleteChunk(chunk) {
  try {
    await ElMessageBox.confirm('确定删除该分段吗？', '删除确认', { type: 'warning' })
    await api.knowledge.deleteChunk([chunk.id])
    ElMessage.success('删除成功')
    loadChunks()
  } catch (error) { if (error !== 'cancel') { ElMessage.error(error.message || '删除失败') } }
}

async function handleRagQuery() {
  if (!ragQuery.value.trim()) return
  ragLoading.value = true
  ragAnswer.value = ''
  ragSources.value = []
  try {
    const res = await api.rag.query({
      query: ragQuery.value,
      kb_id: kbId.value,
      query_optimizer: ragOptimizer.value,
      llm_model: ragModel.value,
      top_k: searchConfig.top_k,
      rerank_top_n: ragRerankTopN.value,
      temperature: ragTemperature.value
    })
    ragAnswer.value = res.data.answer
    ragSources.value = res.data.sources || []
    ragLatency.value = res.data.latency_ms || 0
  } catch (error) { ElMessage.error(error.message || '查询失败') }
  finally { ragLoading.value = false }
}

async function loadRagModels() {
  try {
    const res = await api.rag.models()
    if (res.data?.models?.length) { availableModels.value = res.data.models }
  } catch { /* keep defaults */ }
}

async function loadSearchConfig() {
  try {
    const res = await api.knowledge.getSearchConfig(kbId.value)
    Object.assign(searchConfig, res.data)
  } catch (error) { /* silent */ }
}

async function handleSaveSearchConfig() {
  saveConfigLoading.value = true
  try {
    await api.knowledge.saveSearchConfig(kbId.value, searchConfig)
    ElMessage.success('保存成功')
  } catch (error) { ElMessage.error(error.message || '保存失败') }
  finally { saveConfigLoading.value = false }
}

function triggerIconUpload() { iconInput.value?.click() }

async function handleIconUpload(event) {
  const file = event.target.files?.[0]
  if (!file) return
  if (!file.type.startsWith('image/')) { ElMessage.error('请上传图片文件'); return }
  try {
    const res = await api.knowledge.uploadIcon(kbId.value, file)
    configForm.icon = res.data.url; kbInfo.icon = res.data.url
  } catch (error) { ElMessage.error(error.message || '上传失败') }
  event.target.value = ''
}

async function handleSave() {
  const valid = await configFormRef.value.validate().catch(() => false)
  if (!valid) return
  saveLoading.value = true
  try {
    await api.knowledge.update(kbId.value, configForm)
    Object.assign(kbInfo, configForm)
    ElMessage.success('保存成功')
  } catch (error) { ElMessage.error(error.message || '保存失败') }
  finally { saveLoading.value = false }
}

function triggerUpload() { fileInput.value?.click() }

function handleDrop(event) { addFiles(Array.from(event.dataTransfer.files)) }

function handleFileSelect(event) {
  addFiles(Array.from(event.target.files))
  event.target.value = ''
}

function addFiles(files) {
  for (const file of files) {
    const ext = file.name.split('.').pop().toLowerCase()
    if (!['txt', 'pdf', 'doc', 'docx', 'md', 'ppt', 'pptx'].includes(ext)) {
      ElMessage.error(`${file.name} 格式不支持`)
      continue
    }
    if (file.size > 20 * 1024 * 1024) {
      ElMessage.error(`${file.name} 超过 20MB 限制`)
      continue
    }
    uploadedFiles.value.push({
      id: Date.now() + Math.random(),
      name: file.name, size: file.size, raw: file,
      status: 'pending', progress: 0
    })
  }
}

function removeUploadedFile(id) { uploadedFiles.value = uploadedFiles.value.filter(f => f.id !== id) }

async function submitUpload() {
  for (const file of uploadedFiles.value) {
    file.status = 'uploading'; file.progress = 0
    try {
      const res = await api.knowledge.uploadDocument(kbId.value, file.raw)
      uploadedDocIds.value.push(res.data.id)
      file.status = 'done'; file.progress = 100
    } catch (error) {
      file.status = 'error'
      ElMessage.error(`上传 ${file.name} 失败: ${error.message}`)
    }
  }
  importStep.value = 1
}

async function loadPreview() {
  try {
    const res = await api.knowledge.importPreview(kbId.value, { file_ids: uploadedDocIds.value, config: importConfig })
    previewResults.value = res.data
    if (uploadedDocIds.value.length) { selectedPreviewFile.value = uploadedDocIds.value[0] }
    importStep.value = 2
  } catch (error) { ElMessage.error('预览失败: ' + error.message) }
}

async function doConfirmImport() {
  importLoading.value = true
  try {
    await api.knowledge.confirmImport(kbId.value, { file_ids: uploadedDocIds.value, config: importConfig })
    ElMessage.success('导入任务已启动，正在解析...')
    const pendingIds = [...uploadedDocIds.value]
    closeImportDialog()
    // 后台轮询刷新文档列表
    let pollCount = 0
    const pollTimer = setInterval(async () => {
      pollCount++
      await loadDocuments()
      // 检查所有导入的文档是否已完成
      const importedDocs = documents.value.filter(d => pendingIds.includes(d.id))
      const allCompleted = importedDocs.length === pendingIds.length &&
        importedDocs.every(d => d.status === 'completed' || d.status === 'failed')
      if (allCompleted) {
        clearInterval(pollTimer)
        const failedCount = importedDocs.filter(d => d.status === 'failed').length
        if (failedCount > 0) {
          ElMessage.warning(`${importedDocs.length - failedCount} 个文档导入成功，${failedCount} 个文档导入失败`)
        } else {
          ElMessage.success('所有文档导入完成！')
        }
      }
      // 超过 180 秒停止
      if (pollCount > 36) {
        clearInterval(pollTimer)
        ElMessage.info('文档导入仍在处理中，请稍后手动刷新页面查看状态')
      }
    }, 5000)
  } catch (error) { ElMessage.error('导入失败: ' + error.message) }
  finally { importLoading.value = false }
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
/* ========== Layout ========== */
.kb-edit-container {
  display: flex;
  height: calc(100vh - 56px);
  background: #f1f5f9;
}

/* ========== Sidebar ========== */
.edit-sidebar {
  width: 220px;
  background: #ffffff;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}
.sidebar-header {
  padding: 20px 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid #f1f5f9;
  transition: background 0.15s;
}
.sidebar-header:hover { background: #f8fafc; }
.header-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}
.kb-icon-sm {
  width: 36px; height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}
.kb-icon-sm-img {
  width: 36px; height: 36px;
  border-radius: 8px;
  object-fit: cover;
  flex-shrink: 0;
}
.kb-info { flex: 1; min-width: 0; }
.kb-info .kb-name {
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.kb-info .kb-desc {
  font-size: 12px;
  color: #94a3b8;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 2px;
}
.sidebar-menu {
  flex: 1;
  padding: 12px 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.sidebar-menu div {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #475569;
  transition: all 0.15s;
  font-weight: 500;
}
.sidebar-menu div:hover { background: #f1f5f9; color: #1e293b; }
.sidebar-menu div.active {
  background: #eff6ff;
  color: #2563eb;
  font-weight: 600;
}

/* ========== Content ========== */
.edit-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ========== Document Page ========== */
.doc-page {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}
.page-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.toolbar-left { display: flex; gap: 10px; align-items: center; }
.search-input { width: 280px; }
.doc-table-wrapper { border-radius: 8px; overflow: hidden; }
.doc-table {
  width: 100%;
  --el-table-border-color: #f1f5f9;
}
.doc-table :deep(.table-header) {
  background: #f8fafc;
  color: #475569;
  font-weight: 600;
  font-size: 13px;
  border-bottom: 2px solid #e2e8f0;
}
.doc-table :deep(.table-row) { transition: background 0.1s; }
.doc-table :deep(.table-row:hover) { background: #f8fafc; }
.doc-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}
.doc-name { color: #1e293b; font-weight: 500; }
.metric-tag {
  display: inline-block;
  padding: 2px 10px;
  background: #f1f5f9;
  border-radius: 4px;
  font-size: 13px;
  color: #475569;
  font-weight: 500;
}
.action-btns {
  display: flex;
  align-items: center;
  gap: 4px;
}
.danger-text { color: #ef4444; }

/* ========== Chunks Page ========== */
.chunks-page {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}
.chunks-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f1f5f9;
}
.chunks-title { font-size: 16px; font-weight: 600; color: #0f172a; }
.chunks-meta { font-size: 13px; color: #94a3b8; margin-left: auto; }
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
  color: #94a3b8;
}
.empty-state p { margin-top: 16px; font-size: 14px; }
.chunks-list-container { margin-top: 4px; }
.chunk-card {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 16px 20px;
  border: 1px solid #f1f5f9;
  border-radius: 8px;
  margin-bottom: 8px;
  transition: all 0.15s;
}
.chunk-card:hover { border-color: #e2e8f0; background: #fafbfc; }
.chunk-card-body { flex: 1; min-width: 0; }
.chunk-index {
  display: inline-block;
  font-size: 12px;
  color: #94a3b8;
  font-weight: 600;
  margin-bottom: 8px;
}
.chunk-content {
  font-size: 14px;
  color: #334155;
  line-height: 1.7;
  word-break: break-all;
}
.chunk-card-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
  margin-left: 16px;
}
.chunks-pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 0 4px;
  margin-top: 8px;
  border-top: 1px solid #f1f5f9;
}
.pagination-left { display: flex; align-items: center; gap: 12px; }
.pagination-total { font-size: 13px; color: #94a3b8; }
.page-size-select { width: 100px; }

/* ========== Q&A Panel ========== */
.search-section {
  display: flex;
  gap: 24px;
  flex: 1;
  min-height: 0;
}
.search-config-panel {
  width: 300px;
  background: linear-gradient(160deg, #1e3a5f 0%, #0f2440 100%);
  border-radius: 12px;
  padding: 24px;
  flex-shrink: 0;
}
.panel-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 28px;
}
.search-config-form :deep(.el-form-item__label) {
  color: rgba(255,255,255,0.85);
  font-weight: 500;
  font-size: 13px;
  padding-bottom: 4px;
}
.search-config-form :deep(.el-input-number) { width: 100%; }
.search-config-form :deep(.el-input-number__wrapper) {
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: 6px;
}
.search-config-form :deep(.el-input-number__input) { color: #fff; }
.search-config-form :deep(.el-input-number.is-disabled .el-input-number__wrapper) {
  background: rgba(255,255,255,0.05);
  opacity: 0.6;
}
.save-config-btn {
  width: 100%;
  margin-top: 8px;
  background: #3b82f6;
  border-color: #3b82f6;
  font-weight: 500;
}
.save-config-btn:hover { background: #2563eb; border-color: #2563eb; }

.qa-panel {
  flex: 1;
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  min-height: 0;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
  overflow-y: auto;
}
.qa-input-area {
  margin-bottom: 24px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px;
  background: #fafbfc;
}
.qa-input-area :deep(.el-textarea__inner) {
  border: none;
  background: transparent;
  padding: 0;
  font-size: 14px;
  line-height: 1.6;
  resize: none;
  box-shadow: none;
}
.qa-input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  gap: 12px;
}
.qa-params {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.qa-answer {
  background: linear-gradient(135deg, #eff6ff 0%, #f0fafc 100%);
  border: 1px solid #bfdbfe;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
}
.qa-answer-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 15px;
  color: #1e40af;
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(37,99,235,0.1);
}
.qa-latency {
  margin-left: auto;
  font-size: 12px;
  font-weight: 400;
  color: #64748b;
  background: rgba(255,255,255,0.7);
  padding: 2px 10px;
  border-radius: 4px;
}
.qa-answer-content {
  font-size: 14px;
  line-height: 1.8;
  color: #1e293b;
  white-space: pre-wrap;
}
.qa-sources {
  margin-top: 4px;
}
.qa-sources-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 14px;
  color: #475569;
  margin-bottom: 16px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f1f5f9;
}
.qa-source-item {
  display: flex;
  gap: 14px;
  padding: 16px;
  border: 1px solid #f1f5f9;
  border-radius: 10px;
  margin-bottom: 10px;
  transition: all 0.15s;
}
.qa-source-item:hover {
  border-color: #e2e8f0;
  background: #fafbfc;
}
.source-rank {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px; height: 28px;
  background: #f1f5f9;
  color: #475569;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}
.source-body { flex: 1; min-width: 0; }
.source-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.source-score {
  font-size: 12px;
  color: #2563eb;
  font-weight: 600;
  background: #eff6ff;
  padding: 2px 8px;
  border-radius: 4px;
}
.source-filename { font-size: 12px; color: #94a3b8; }
.source-content {
  font-size: 13px;
  color: #475569;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.qa-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  color: #94a3b8;
  padding: 60px 0;
}
.qa-empty p { margin-top: 16px; font-size: 14px; }
.panel-divider {
  height: 1px;
  background: rgba(255,255,255,0.1);
  margin: 20px 0 16px;
}
.panel-subheader {
  color: rgba(255,255,255,0.7);
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
}

/* ========== Config Section ========== */
.config-section {
  background: #fff;
  padding: 32px;
  border-radius: 12px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
  max-width: 640px;
}
.config-card { margin-bottom: 32px; }
.form-label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 16px;
}
.icon-upload {
  display: flex;
  align-items: center;
  gap: 16px;
}
.icon-circle {
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
.icon-circle:hover { border-color: #3b82f6; background: #eff6ff; }
.icon-img { width: 72px; height: 72px; object-fit: cover; border-radius: 12px; }
.icon-placeholder { color: #94a3b8; }
.icon-hint { font-size: 13px; color: #94a3b8; }
.hidden-input { display: none; }
.config-form-wrap { margin-top: 8px; }
.config-form-wrap :deep(.el-form-item__label) {
  font-weight: 500;
  color: #475569;
}

/* ========== Import Dialog ========== */
.dialog-header {
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 100%;
}
.dialog-title { font-size: 18px; font-weight: 600; color: #0f172a; }
.import-steps { width: 100%; }
.import-step-content { padding: 8px 0; min-height: 300px; }

.upload-zone {
  border: 2px dashed #cbd5e1;
  border-radius: 12px;
  padding: 48px;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  transition: all 0.2s;
  background: #fafbfc;
}
.upload-zone:hover { border-color: #3b82f6; background: #f0f7ff; }
.upload-title { font-size: 16px; color: #334155; margin: 16px 0 8px; font-weight: 500; }
.upload-hint { font-size: 13px; color: #94a3b8; }
.upload-table { margin-top: 20px; }
.upload-file-name { display: flex; align-items: center; gap: 8px; }

.file-list { margin-top: 20px; }

.config-form { max-width: 520px; }
.config-select { width: 100%; }
.reader-hint { font-size: 12px; color: #909399; margin-top: 4px; line-height: 1.4; }
.slider-row { width: 100%; display: flex; align-items: center; gap: 12px; }
.slider-row :deep(.el-slider) { flex: 1; min-width: 200px; }
.slider-row :deep(.el-slider__runway) { margin-right: 16px; }
.slider-row :deep(.el-slider__input) { width: 110px !important; }
.slider-row :deep(.el-input-number) { width: 110px; }

.preview-layout { display: flex; gap: 24px; }
.preview-sidebar { width: 200px; flex-shrink: 0; }
.preview-file-list { display: flex; flex-direction: column; gap: 2px; }
.preview-file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  color: #475569;
  transition: all 0.15s;
}
.preview-file-item:hover { background: #f1f5f9; }
.preview-file-item.active { background: #eff6ff; color: #2563eb; font-weight: 500; }
.preview-content { flex: 1; min-width: 0; }
.preview-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-right: 8px; }
.preview-label { font-size: 15px; font-weight: 600; color: #0f172a; }
.chunk-count { font-size: 13px; color: #94a3b8; flex-shrink: 0; padding-left: 16px; }
.chunk-list { max-height: 380px; overflow-y: auto; padding-right: 6px; }
.chunk-item {
  padding: 16px;
  border: 1px solid #f1f5f9;
  border-radius: 8px;
  margin-bottom: 10px;
  transition: all 0.15s;
}
.chunk-item.active { border-color: #bfdbfe; background: #f8fbff; }
.chunk-number {
  display: inline-block;
  width: 24px; height: 24px;
  border-radius: 6px;
  background: #e2e8f0;
  color: #475569;
  text-align: center;
  line-height: 24px;
  font-size: 12px;
  font-weight: 600;
  margin-right: 12px;
}
.chunk-item.active .chunk-number { background: #2563eb; color: #fff; }
.chunk-text { font-size: 14px; color: #334155; line-height: 1.7; }
.preview-pagination { display: flex; justify-content: space-between; align-items: center; margin-top: 20px; }

.confirm-table { width: 100%; }

.dialog-footer { display: flex; justify-content: flex-end; gap: 8px; }

/* ========== Edit Dialog ========== */
.edit-modal-content { padding: 4px 0; }
.edit-textarea { width: 100%; }
.edit-textarea :deep(.el-textarea__inner) {
  padding: 14px;
  font-size: 14px;
  line-height: 1.7;
  border-radius: 8px;
  resize: none;
}
</style>