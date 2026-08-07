<template>
  <div class="kb-detail-layout">
    <!-- ========== Left Sidebar (collapsible) ========== -->
    <aside class="kb-detail-sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="kb-detail-header" @click="goBack">
        <div class="back-row">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>
          <span v-show="!sidebarCollapsed">返回</span>
        </div>
        <div class="kb-info-row" v-show="!sidebarCollapsed">
          <div class="kb-icon-sm" v-if="!kbInfo.icon" :style="{ background: iconColor }">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
          </div>
          <img v-else :src="getIconUrl(kbInfo.icon)" class="kb-icon-sm-img" />
          <div style="min-width:0">
            <div class="name">{{ kbInfo.name }}</div>
            <div class="desc">{{ kbInfo.description }}</div>
          </div>
        </div>
      </div>

      <div class="detail-tabs">
        <div :class="{ active: activeTab === 'documents' }" class="detail-tab" @click="activeTab = 'documents'; selectedDoc = null">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          <span v-show="!sidebarCollapsed">文档列表</span>
          <span class="tab-badge" v-show="!sidebarCollapsed">{{ documents.length }}</span>
        </div>
        <div :class="{ active: activeTab === 'search' }" class="detail-tab" @click="activeTab = 'search'">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
          <span v-show="!sidebarCollapsed">知识检索</span>
        </div>
        <div :class="{ active: activeTab === 'graph' }" class="detail-tab" @click="activeTab = 'graph'">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="2"/><circle cx="5" cy="5" r="2"/><circle cx="19" cy="5" r="2"/><circle cx="5" cy="19" r="2"/><circle cx="19" cy="19" r="2"/><line x1="6.5" y1="6.5" x2="10.5" y2="10.5"/><line x1="17.5" y1="6.5" x2="13.5" y2="10.5"/><line x1="6.5" y1="17.5" x2="10.5" y2="13.5"/><line x1="17.5" y1="17.5" x2="13.5" y2="13.5"/></svg>
          <span v-show="!sidebarCollapsed">知识图谱</span>
        </div>
        <div :class="{ active: activeTab === 'config' }" class="detail-tab" @click="activeTab = 'config'">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
          <span v-show="!sidebarCollapsed">配置</span>
        </div>
      </div>

      <!-- Collapse toggle button -->
      <button class="sidebar-toggle" :title="sidebarCollapsed ? '展开' : '收起'" @click="sidebarCollapsed = !sidebarCollapsed">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :style="{ transform: sidebarCollapsed ? 'rotate(180deg)' : '' }">
          <line x1="17" y1="12" x2="7" y2="12"/><polyline points="10 15 7 12 10 9"/>
        </svg>
      </button>
    </aside>

    <!-- ========== Right Content ========== -->
    <div class="kb-detail-content">

      <!-- ========== Documents Tab ========== -->
      <div v-if="activeTab === 'documents'">
        <!-- Document List -->
        <div v-if="!selectedDoc">
          <div class="doc-panel">
            <div class="doc-toolbar">
              <div class="doc-toolbar-left">
                <div class="search-box">
                  <span class="ico">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
                  </span>
                  <el-input v-model="searchText" placeholder="搜索文档名称..." clearable class="search-input-native" @keyup.enter="loadDocuments" />
                </div>
                <button class="link-btn" @click="loadDocuments">查询</button>
                <button class="link-btn" @click="searchText = ''; loadDocuments()">重置</button>
              </div>
              <button class="btn btn-primary" @click="showImportDialog = true">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                <span>导入文件</span>
              </button>
            </div>
            <table class="doc-table">
              <thead>
                <tr>
                  <th>文件名</th>
                  <th style="width:80px">大小</th>
                  <th style="width:70px">段数</th>
                  <th style="width:110px">状态</th>
                  <th style="width:150px">更新时间</th>
                  <th style="width:200px">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in documents" :key="row.id">
                  <td>
                    <div class="file-name-cell">
                      <div :class="'file-type-icon ' + (row.filename.toLowerCase().endsWith('.pdf') ? 'ft-pdf' : row.filename.toLowerCase().endsWith('.docx') || row.filename.toLowerCase().endsWith('.doc') ? 'ft-docx' : row.filename.toLowerCase().endsWith('.md') ? 'ft-md' : row.filename.toLowerCase().endsWith('.txt') ? 'ft-txt' : row.filename.toLowerCase().endsWith('.ppt') || row.filename.toLowerCase().endsWith('.pptx') ? 'ft-ppt' : 'ft-txt')">
                        {{ row.filename.toLowerCase().endsWith('.pdf') ? 'PDF' : row.filename.toLowerCase().endsWith('.docx') || row.filename.toLowerCase().endsWith('.doc') ? 'DOC' : row.filename.toLowerCase().endsWith('.md') ? 'MD' : row.filename.toLowerCase().endsWith('.txt') ? 'TXT' : row.filename.toLowerCase().endsWith('.ppt') || row.filename.toLowerCase().endsWith('.pptx') ? 'PPT' : 'TXT' }}
                      </div>
                      <span>{{ row.filename }}</span>
                    </div>
                  </td>
                  <td><span class="metric-pill">{{ formatChars(row.char_count) }}</span></td>
                  <td><span class="metric-pill">{{ row.chunk_count }}</span></td>
                  <td>
                    <span :class="'status-badge ' + (row.status === 'completed' ? 'st-completed' : row.status === 'processing' ? 'st-processing' : 'st-failed')">
                      <span class="dot"></span>{{ row.status === 'completed' ? '已完成' : row.status === 'processing' ? '处理中' : row.status === 'failed' ? '失败' : row.status }}
                    </span>
                  </td>
                  <td style="font-size:12px;color:var(--t-3)">{{ formatDateTime(row.updated_at || row.created_at) }}</td>
                  <td>
                    <div class="action-cell">
                      <button class="link-btn" @click="handleViewChunks(row)">查看分段</button>
                      <button class="link-btn" @click="handleShowDocGraph(row)">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:-2px;"><circle cx="12" cy="12" r="2"/><circle cx="5" cy="5" r="2"/><circle cx="19" cy="5" r="2"/><line x1="7" y1="7" x2="10" y2="10"/></svg>
                        图谱
                      </button>
                      <el-dropdown trigger="click" @command="(cmd) => handleDocAction(cmd, row)">
                        <button class="link-btn">
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/></svg>
                        </button>
                        <template #dropdown>
                          <el-dropdown-menu>
                            <el-dropdown-item command="download">
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:-2px;margin-right:6px"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                              下载
                            </el-dropdown-item>
                            <el-dropdown-item command="delete">
                              <span style="color:var(--rose)">删除</span>
                            </el-dropdown-item>
                          </el-dropdown-menu>
                        </template>
                      </el-dropdown>
                    </div>
                  </td>
                </tr>
                <tr v-if="documents.length === 0">
                  <td colspan="6" style="text-align:center;padding:40px 0;color:var(--t-3);font-size:13px">
                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin:0 auto 12px;opacity:0.4;display:block"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                    暂无文档数据
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Chunks View -->
        <div v-else>
          <div class="chunks-panel">
            <div class="chunks-header">
              <button class="back-btn" @click="selectedDoc = null">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>
                返回文档列表
              </button>
              <span class="doc-name">{{ selectedDoc.filename }}</span>
              <span class="chunks-count">{{ chunksTotal }} 个分段</span>
            </div>
            <div v-if="chunks.length === 0" class="empty-state-box">
              <div class="icon-box">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
              </div>
              <p>暂无分段数据</p>
            </div>
            <div v-else>
              <div v-for="chunk in chunks" :key="chunk.id" class="chunk-card">
                <div class="chunk-card-body">
                  <span class="chunk-index">#{{ chunk.chunk_index }}</span>
                  <div class="chunk-content">{{ chunk.content }}</div>
                </div>
                <div class="chunk-actions">
                  <button class="link-btn" @click="handleEditChunk(chunk)">编辑</button>
                  <button class="link-btn danger" @click="handleDeleteChunk(chunk)">删除</button>
                </div>
              </div>
            </div>
            <div class="chunks-pagination">
              <div class="page-info">
                <span>共 {{ chunksTotal }} 条</span>
                <select v-model="chunksPageSize" class="page-size-select" @change="handleChunksSizeChange(chunksPageSize)">
                  <option :value="10">10条/页</option>
                  <option :value="20">20条/页</option>
                  <option :value="50">50条/页</option>
                </select>
              </div>
              <div class="page-controls">
                <button class="page-btn" :disabled="chunksCurrentPage <= 1" @click="handleChunksPageChange(chunksCurrentPage - 1)">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
                </button>
                <span class="page-info" style="margin:0 8px">{{ chunksCurrentPage }} / {{ Math.ceil(chunksTotal / chunksPageSize) || 1 }}</span>
                <button class="page-btn" :disabled="chunksCurrentPage >= Math.ceil(chunksTotal / chunksPageSize)" @click="handleChunksPageChange(chunksCurrentPage + 1)">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ========== Search/RAG Tab ========== -->
      <div v-else-if="activeTab === 'search'" class="rag-tab">
        <!-- Query Input -->
        <div class="rag-query-card">
          <div class="rag-query-header">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
            知识检索
          </div>
          <textarea v-model="ragQuery" placeholder="输入你的问题，AI 将从知识库中检索并生成答案..." :disabled="ragLoading" class="rag-query-input"></textarea>
          <div class="rag-query-footer">
            <div class="rag-model-selects">
              <select v-model="ragModel" class="qa-param-select">
                <option v-for="m in availableModels" :key="m" :value="m">{{ m }}</option>
              </select>
              <select v-model="ragEmbedModel" class="qa-param-select" style="max-width:220px">
                <option value="text-embedding-v4">text-embedding-v4</option>
                <option value="text-embedding-async-v2">text-embedding-async-v2</option>
                <option value="text-embedding-async-v1">text-embedding-async-v1</option>
                <option value="qwen3-vl-rerank">qwen3-vl-rerank</option>
                <option value="gte-rerank-v2">gte-rerank-v2</option>
                <option value="tongyi-embedding-vision-plus-2026-03-06">tongyi-embedding-vision-plus-2026-03-06</option>
                <option value="tongyi-embedding-vision-plus">tongyi-embedding-vision-plus</option>
              </select>
            </div>
            <div class="rag-query-actions">
              <button class="btn btn-ghost btn-sm" @click="showAdvancedSearch = !showAdvancedSearch">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 1v6m0 6v6"/></svg>
                高级
              </button>
              <button class="btn btn-primary" @click="handleRagQuery" :disabled="ragLoading">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
                {{ ragLoading ? '查询中...' : '智能问答' }}
              </button>
            </div>
          </div>
        </div>

        <!-- Advanced Search Params (collapsible) -->
        <div v-if="showAdvancedSearch" class="rag-advanced-card">
          <div class="rag-advanced-grid">
            <div class="adv-field">
              <label>召回条数</label>
              <el-input-number v-model="searchConfig.top_k" :min="1" :max="50" controls-position="right" class="config-number-input" />
            </div>
            <div class="adv-field">
              <label>向量权重</label>
              <el-input-number v-model="searchConfig.vector_weight" :min="0" :max="1" :step="0.1" :precision="1" controls-position="right" class="config-number-input" />
            </div>
            <div class="adv-field">
              <label>关键词权重</label>
              <el-input-number v-model="searchConfig.keyword_weight" :min="0" :max="1" :step="0.1" :precision="1" controls-position="right" class="config-number-input" />
            </div>
            <div class="adv-field">
              <label>重排序保留</label>
              <el-input-number v-model="ragRerankTopN" :min="1" :max="20" controls-position="right" class="config-number-input" />
            </div>
            <div class="adv-field">
              <label>生成温度</label>
              <el-input-number v-model="ragTemperature" :min="0" :max="2" :step="0.1" :precision="1" controls-position="right" class="config-number-input" />
            </div>
            <div class="adv-field">
              <label>查询优化</label>
              <select v-model="ragOptimizer" class="qa-param-select" style="width:100%;height:32px">
                <option value="none">无优化 (默认)</option>
                <option value="hyde">HyDE 假设文档</option>
                <option value="rewrite">查询改写</option>
                <option value="multi_query">多查询扩展</option>
              </select>
            </div>
          </div>
          <button class="btn btn-ghost btn-sm" style="margin-top:12px" :loading="saveConfigLoading" @click="handleSaveSearchConfig">保存默认</button>
        </div>

        <!-- Answer -->
        <div v-if="ragAnswer" class="rag-answer-card">
          <div class="rag-answer-header">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
            AI 回答
            <span class="qa-latency" v-if="ragLatency">{{ (ragLatency / 1000).toFixed(2) }}s</span>
            <div class="rag-answer-actions">
              <button class="btn btn-ghost btn-sm" :disabled="answerGraphLoading" @click="handleAnswerGraph">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="2"/><circle cx="5" cy="5" r="2"/><circle cx="19" cy="5" r="2"/><line x1="7" y1="7" x2="10" y2="10"/></svg>
                知识图谱
              </button>
            </div>
          </div>
          <div class="rag-answer-body">{{ ragAnswer }}</div>
        </div>

        <!-- Sources -->
        <div v-if="ragSources.length" class="rag-sources-card">
          <div class="rag-sources-header" @click="showSources = !showSources">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            参考来源 ({{ ragSources.length }})
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :style="{ transform: showSources ? 'rotate(180deg)' : '' }" style="margin-left:auto;transition:transform .2s"><polyline points="6 9 12 15 18 9"/></svg>
          </div>
          <div v-if="showSources" class="rag-sources-body">
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
          </div>
        </div>

        <!-- Empty State -->
        <div v-if="!ragAnswer && !ragLoading" class="rag-empty-state">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          <p>输入问题，AI 自动检索知识库并生成回答</p>
        </div>
        <div v-if="ragLoading" class="rag-loading">
          <div class="loading-dots"><span></span><span></span><span></span></div>
          <p>正在检索知识库...</p>
        </div>
      </div>

      <!-- ========== Graph Tab ========== -->
      <div v-else-if="activeTab === 'graph'">
        <div class="doc-panel" style="padding:0;overflow:hidden">
          <div class="graph-toolbar">
            <div class="graph-toolbar-left">
              <select v-model="graphMethod" class="qa-param-select" style="width:140px">
                <option value="simple">Simple 抽取</option>
                <option value="schema">Schema 抽取</option>
              </select>
              <button class="btn btn-primary btn-sm" :loading="graphLoading" @click="handleExtractGraph">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3z"/></svg>
                抽取知识图谱
              </button>
              <button class="btn btn-ghost btn-sm" @click="handleRefreshGraph">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 4v6h-6"/><path d="M1 20v-6h6"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
                刷新
              </button>
            </div>
            <div class="graph-toolbar-right">
              <span class="graph-stat">节点: <span class="num">{{ graphStats.nodes }}</span></span>
              <span class="graph-stat">关系: <span class="num">{{ graphStats.edges }}</span></span>
            </div>
          </div>
          <div class="graph-canvas-container" ref="graphContainerRef">
            <div v-if="graphNodes.length === 0 && !graphLoading" class="graph-empty">
              <div class="empty-icon-box">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="2"/><circle cx="5" cy="5" r="2"/><circle cx="19" cy="5" r="2"/><line x1="7" y1="7" x2="10" y2="10"/></svg>
              </div>
              <p>暂无图谱数据，点击"抽取知识图谱"生成</p>
            </div>
            <div v-if="graphLoading" class="graph-empty">
              <div class="empty-icon-box">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="2"/><circle cx="5" cy="5" r="2"/><circle cx="19" cy="5" r="2"/><line x1="7" y1="7" x2="10" y2="10"/></svg>
              </div>
              <p>抽取中...</p>
            </div>
            <div v-show="graphNodes.length > 0" id="graphCanvas" class="graph-canvas"></div>
          </div>
        </div>
      </div>

      <!-- ========== Config Tab ========== -->
      <div v-else-if="activeTab === 'config'">
        <div class="config-section">
          <div class="field-group">
            <label class="field-label">知识库图标</label>
            <div class="icon-upload-area">
              <div class="icon-preview-box" @click="triggerIconUpload">
                <img v-if="configForm.icon" :src="getIconUrl(configForm.icon)" class="icon-preview-img" />
                <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
              </div>
              <span class="icon-upload-tip">点击上传图标</span>
              <input type="file" ref="iconInput" accept="image/*" class="hidden-input" @change="handleIconUpload" />
            </div>
          </div>
          <div class="field-group">
            <label class="field-label">名称</label>
            <el-input v-model="configForm.name" placeholder="请输入知识库名称" class="field-input-el" />
          </div>
          <div class="field-group">
            <label class="field-label">描述</label>
            <el-input v-model="configForm.description" type="textarea" :rows="4" placeholder="请输入知识库描述" class="field-input-el" />
          </div>
          <button class="btn btn-primary btn-lg" :loading="saveLoading" @click="handleSave">保存配置</button>
        </div>
      </div>

    </div>

    <!-- ========== Import Modal ========== -->
    <div class="modal-overlay" :class="{ show: showImportDialog }" @click.self="closeImportDialog">
      <div class="modal modal-import">
        <button class="modal-close" @click="closeImportDialog">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
        <div class="modal-header">
          <div class="modal-title">导入文件</div>
          <div class="modal-subtitle">支持 TXT / PDF / DOCX / MD / PPT / PPTX 格式，单个文件不超过 20MB</div>
        </div>
        <div class="wizard-steps">
          <div :class="'wizard-step' + (importStep === 0 ? ' active' : '') + (importStep > 0 ? ' done' : '')">
            <div class="wizard-step-num"><span>1</span></div>
            文件上传
          </div>
          <div :class="'wizard-step-line' + (importStep > 0 ? ' done' : '')"></div>
          <div :class="'wizard-step' + (importStep === 1 ? ' active' : '') + (importStep > 1 ? ' done' : '')">
            <div class="wizard-step-num"><span>2</span></div>
            参数设置
          </div>
          <div :class="'wizard-step-line' + (importStep > 1 ? ' done' : '')"></div>
          <div :class="'wizard-step' + (importStep === 2 ? ' active' : '') + (importStep > 2 ? ' done' : '')">
            <div class="wizard-step-num"><span>3</span></div>
            分段预览
          </div>
          <div :class="'wizard-step-line' + (importStep > 2 ? ' done' : '')"></div>
          <div :class="'wizard-step' + (importStep === 3 ? ' active' : '') + (importStep > 3 ? ' done' : '')">
            <div class="wizard-step-num"><span>4</span></div>
            确认导入
          </div>
        </div>
        <div class="modal-body">
          <!-- Step 0: Upload -->
          <div v-if="importStep === 0" class="import-step">
            <div class="upload-zone" @click="triggerUpload" @drop.prevent="handleDrop" @dragover.prevent>
              <div class="upload-icon-large">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
              </div>
              <p class="upload-title">点击或将文件拖拽到这里上传</p>
              <p class="upload-hint">支持 TXT / PDF / DOCX / MD / PPT / PPTX 格式</p>
            </div>
            <input type="file" ref="fileInput" accept=".txt,.pdf,.doc,.docx,.md,.ppt,.pptx" multiple class="hidden-input" @change="handleFileSelect" />
            <div v-if="uploadedFiles.length" class="upload-file-list">
              <div v-for="file in uploadedFiles" :key="file.id" class="upload-file-item">
                <div :class="'file-type-icon ' + (file.name.toLowerCase().endsWith('.pdf') ? 'ft-pdf' : file.name.toLowerCase().endsWith('.docx') || file.name.toLowerCase().endsWith('.doc') ? 'ft-docx' : file.name.toLowerCase().endsWith('.md') ? 'ft-md' : file.name.toLowerCase().endsWith('.txt') ? 'ft-txt' : file.name.toLowerCase().endsWith('.ppt') || file.name.toLowerCase().endsWith('.pptx') ? 'ft-ppt' : 'ft-txt')">{{ file.name.toLowerCase().endsWith('.pdf') ? 'PDF' : file.name.toLowerCase().endsWith('.docx') || file.name.toLowerCase().endsWith('.doc') ? 'DOC' : file.name.toLowerCase().endsWith('.md') ? 'MD' : file.name.toLowerCase().endsWith('.txt') ? 'TXT' : file.name.toLowerCase().endsWith('.ppt') || file.name.toLowerCase().endsWith('.pptx') ? 'PPT' : 'TXT' }}</div>
                <div class="upload-file-info">
                  <div class="upload-file-name">{{ file.name }}</div>
                  <div class="upload-file-size">{{ formatSize(file.size) }}</div>
                </div>
                <div v-if="file.status === 'uploading'" class="file-status">
                  <div class="upload-progress-bar"><div class="upload-progress-fill" :style="{ width: file.progress + '%' }"></div></div>
                </div>
                <div v-else-if="file.status === 'done'" class="file-status">
                  <span class="status-badge st-completed"><span class="dot"></span>已上传</span>
                </div>
                <div v-else class="file-status">
                  <span class="status-badge st-processing"><span class="dot"></span>待上传</span>
                </div>
                <button class="link-btn danger" @click="removeUploadedFile(file.id)">移除</button>
              </div>
            </div>
          </div>

          <!-- Step 1: Config -->
          <div v-else-if="importStep === 1" class="import-step">
            <div class="import-config-form">
              <div class="import-config-row">
                <label>加载方式</label>
                <select v-model="importConfig.reader_type" class="config-input-select">
                  <option v-for="opt in readerOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                </select>
                <div class="import-config-hint">PDF 可选 PyMuPDF / PyPDF2 / Unstructured，其他类型自动</div>
              </div>
              <div class="import-config-row">
                <label>分割器</label>
                <select v-model="importConfig.splitter_type" class="config-input-select">
                  <option value="token">Token 切分器</option>
                  <option value="sentence">句子切分器</option>
                  <option value="semantic">语义切分器</option>
                </select>
              </div>
              <div class="import-config-row">
                <label>分段长度</label>
                <div class="config-row-slider">
                  <el-slider v-model="importConfig.chunk_size" :min="128" :max="2048" :step="64" style="flex:1" />
                  <input class="slider-val" type="number" :value="importConfig.chunk_size" disabled />
                </div>
              </div>
              <div class="import-config-row">
                <label>分段重叠</label>
                <div class="config-row-slider">
                  <el-slider v-model="importConfig.chunk_overlap" :min="0" :max="512" :step="16" style="flex:1" />
                  <input class="slider-val" type="number" :value="importConfig.chunk_overlap" disabled />
                </div>
              </div>
              <div class="import-config-row">
                <label>嵌入模型</label>
                <select v-model="importConfig.embed_model" class="config-input-select">
                  <option value="text-embedding-v4">text-embedding-v4</option>
                  <option value="text-embedding-async-v2">text-embedding-async-v2</option>
                  <option value="text-embedding-async-v1">text-embedding-async-v1</option>
                  <option value="gte-rerank-v2">gte-rerank-v2</option>
                  <option value="qwen3-vl-rerank">qwen3-vl-rerank</option>
                  <option value="tongyi-embedding-vision-plus-2026-03-06">tongyi-embedding-vision-plus-2026-03-06</option>
                  <option value="tongyi-embedding-vision-plus">tongyi-embedding-vision-plus</option>
                </select>
              </div>
            </div>
          </div>

          <!-- Step 2: Preview -->
          <div v-else-if="importStep === 2" class="import-step">
            <div class="preview-layout">
              <div class="preview-sidebar">
                <div class="preview-file-list">
                  <div
                    v-for="file in uploadedFiles"
                    :key="file.id"
                    :class="{ active: selectedPreviewFile === file.tempId }"
                    class="preview-file-tab"
                    @click="selectedPreviewFile = file.tempId"
                  >
                    <div :class="'file-type-icon ' + (file.name.toLowerCase().endsWith('.pdf') ? 'ft-pdf' : file.name.toLowerCase().endsWith('.docx') || file.name.toLowerCase().endsWith('.doc') ? 'ft-docx' : file.name.toLowerCase().endsWith('.md') ? 'ft-md' : file.name.toLowerCase().endsWith('.txt') ? 'ft-txt' : file.name.toLowerCase().endsWith('.ppt') || file.name.toLowerCase().endsWith('.pptx') ? 'ft-ppt' : 'ft-txt')" style="width:24px;height:24px;font-size:9px">{{ file.name.toLowerCase().endsWith('.pdf') ? 'PDF' : file.name.toLowerCase().endsWith('.docx') || file.name.toLowerCase().endsWith('.doc') ? 'DOC' : file.name.toLowerCase().endsWith('.md') ? 'MD' : file.name.toLowerCase().endsWith('.txt') ? 'TXT' : file.name.toLowerCase().endsWith('.ppt') || file.name.toLowerCase().endsWith('.pptx') ? 'PPT' : 'TXT' }}</div>
                    <span>{{ file.name }}</span>
                  </div>
                </div>
              </div>
              <div class="preview-main">
                <div class="preview-header">
                  <span style="font-size:14px;font-weight:600;color:var(--t-0)">文档预览</span>
                  <span style="font-size:12px;color:var(--t-3)">共 {{ currentPreviewChunks.length }} 个分段</span>
                </div>
                <div class="preview-chunk-list">
                  <div v-for="(chunk, idx) in pagedPreviewChunks" :key="idx" class="preview-chunk">
                    <span class="preview-chunk-num">#{{ previewPageStart + idx }}</span>
                    <span class="preview-chunk-text">{{ chunk.content }}</span>
                  </div>
                </div>
                <div class="chunks-pagination" style="border-top:none;padding-top:12px;margin-top:0">
                  <span class="page-info">共 {{ currentPreviewChunks.length }} 条</span>
                  <div class="page-controls">
                    <button class="page-btn" :disabled="previewCurrentPage <= 1" @click="previewCurrentPage--">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
                    </button>
                    <span class="page-info" style="margin:0 8px">{{ previewCurrentPage }} / {{ Math.ceil(currentPreviewChunks.length / PAGE_SIZE) || 1 }}</span>
                    <button class="page-btn" :disabled="previewCurrentPage >= Math.ceil(currentPreviewChunks.length / PAGE_SIZE)" @click="previewCurrentPage++">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Step 3: Confirm -->
          <div v-else-if="importStep === 3" class="import-step">
            <div class="confirm-list">
              <div v-for="file in confirmFiles" :key="file.name" class="confirm-item">
                <div :class="'file-type-icon ' + (file.name.toLowerCase().endsWith('.pdf') ? 'ft-pdf' : file.name.toLowerCase().endsWith('.docx') || file.name.toLowerCase().endsWith('.doc') ? 'ft-docx' : file.name.toLowerCase().endsWith('.md') ? 'ft-md' : file.name.toLowerCase().endsWith('.txt') ? 'ft-txt' : file.name.toLowerCase().endsWith('.ppt') || file.name.toLowerCase().endsWith('.pptx') ? 'ft-ppt' : 'ft-txt')" style="width:28px;height:28px;font-size:10px">{{ file.name.toLowerCase().endsWith('.pdf') ? 'PDF' : file.name.toLowerCase().endsWith('.docx') || file.name.toLowerCase().endsWith('.doc') ? 'DOC' : file.name.toLowerCase().endsWith('.md') ? 'MD' : file.name.toLowerCase().endsWith('.txt') ? 'TXT' : file.name.toLowerCase().endsWith('.ppt') || file.name.toLowerCase().endsWith('.pptx') ? 'PPT' : 'TXT' }}</div>
                <div class="info">
                  <div class="name">{{ file.name }}</div>
                  <div class="status">待导入</div>
                </div>
                <span class="status-badge st-completed"><span class="dot"></span>就绪</span>
              </div>
            </div>
            <div style="margin-top:16px;padding:14px;background:rgba(99,102,241,0.06);border:1px solid rgba(99,102,241,0.15);border-radius:8px;font-size:13px;color:var(--t-2);display:flex;gap:10px;align-items:flex-start">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--ac-2)" stroke-width="2" style="flex-shrink:0;margin-top:1px"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
              <span>确认后将启动后台导入任务，系统将自动解析文档、分段处理并生成向量嵌入。处理完成后可在文档列表查看状态。</span>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="closeImportDialog">取消</button>
          <button v-if="importStep > 0" class="btn btn-ghost" @click="importStep--">上一步</button>
          <button v-if="importStep === 0 && uploadedFiles.length" class="btn btn-primary" @click="submitUpload">下一步</button>
          <button v-if="importStep === 1" class="btn btn-primary" @click="loadPreview">下一步</button>
          <button v-if="importStep === 2" class="btn btn-primary" @click="importStep++">下一步</button>
          <button v-if="importStep === 3" class="btn btn-primary" :disabled="importLoading" @click="doConfirmImport">开始导入</button>
        </div>
      </div>
    </div>

    <!-- ========== Edit Chunk Modal ========== -->
    <div class="modal-overlay" :class="{ show: showEditDialog }" @click.self="showEditDialog = false">
      <div class="modal modal-edit-chunk">
        <button class="modal-close" @click="showEditDialog = false">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
        <div class="modal-header">
          <div class="modal-title">编辑分段</div>
        </div>
        <div class="modal-body">
          <textarea v-model="editForm.content" class="edit-chunk-textarea" placeholder="请输入分段内容"></textarea>
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="showEditDialog = false">取消</button>
          <button class="btn btn-primary" @click="handleSaveChunk">保存</button>
        </div>
      </div>
    </div>

    <!-- ========== Doc Graph Modal ========== -->
    <div class="modal-overlay" :class="{ show: showDocGraphDialog }" @click.self="showDocGraphDialog = false">
      <div class="modal modal-graph">
        <button class="modal-close" @click="showDocGraphDialog = false">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
        <div class="modal-header">
          <div class="modal-title">文档知识图谱</div>
          <div class="modal-subtitle" v-if="selectedDocForGraph">{{ selectedDocForGraph.filename }}</div>
        </div>
        <div class="graph-toolbar">
          <div class="graph-toolbar-left">
            <span style="font-size:13px;font-weight:600;color:var(--t-0)" v-if="selectedDocForGraph">{{ selectedDocForGraph.filename }}</span>
          </div>
          <div class="graph-toolbar-right">
            <span class="graph-stat">节点: <span class="num">{{ docGraphStats.nodes }}</span></span>
            <span class="graph-stat">关系: <span class="num">{{ docGraphStats.edges }}</span></span>
          </div>
        </div>
        <div class="graph-canvas-area">
          <div v-if="docGraphLoading" class="graph-empty-state">
            <div class="icon">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="2"/><circle cx="5" cy="5" r="2"/><circle cx="19" cy="5" r="2"/><line x1="7" y1="7" x2="10" y2="10"/></svg>
            </div>
            <p>抽取中...</p>
          </div>
          <div v-else-if="docGraphNodes.length === 0" class="graph-empty-state">
            <div class="icon">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="2"/><circle cx="5" cy="5" r="2"/><circle cx="19" cy="5" r="2"/><line x1="7" y1="7" x2="10" y2="10"/></svg>
            </div>
            <p>暂无图谱数据</p>
          </div>
          <div v-show="docGraphNodes.length > 0" id="docGraphCanvas" class="graph-canvas"></div>
        </div>
      </div>
    </div>

    <!-- ========== Answer Graph Modal ========== -->
    <div class="modal-overlay" :class="{ show: showAnswerGraphDialog }" @click.self="showAnswerGraphDialog = false">
      <div class="modal modal-graph">
        <button class="modal-close" @click="showAnswerGraphDialog = false">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
        <div class="modal-header">
          <div class="modal-title">答案知识图谱</div>
          <div class="modal-subtitle">基于 AI 回答抽取的实体关系</div>
        </div>
        <div class="graph-toolbar">
          <div class="graph-toolbar-left">
            <span style="font-size:13px;font-weight:600;color:var(--t-0)">基于 AI 回答抽取的实体关系</span>
          </div>
          <div class="graph-toolbar-right">
            <span class="graph-stat">节点: <span class="num">{{ answerGraphStats.nodes }}</span></span>
            <span class="graph-stat">关系: <span class="num">{{ answerGraphStats.edges }}</span></span>
          </div>
        </div>
        <div class="graph-canvas-area">
          <div v-if="answerGraphLoading" class="graph-empty-state">
            <div class="icon">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="2"/><circle cx="5" cy="5" r="2"/><circle cx="19" cy="5" r="2"/><line x1="7" y1="7" x2="10" y2="10"/></svg>
            </div>
            <p>抽取中...</p>
          </div>
          <div v-else-if="answerGraphNodes.length === 0" class="graph-empty-state">
            <div class="icon">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="2"/><circle cx="5" cy="5" r="2"/><circle cx="19" cy="5" r="2"/><line x1="7" y1="7" x2="10" y2="10"/></svg>
            </div>
            <p>未从回答中抽取到实体关系</p>
          </div>
          <div v-show="answerGraphNodes.length > 0" id="answerGraphCanvas" class="graph-canvas"></div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Folder, Document, Search, Setting, Plus, MoreFilled, UploadFilled, Download, ChatDotSquare, Connection, MagicStick } from '@element-plus/icons-vue'
import { api } from '../api'

const route = useRoute()
const router = useRouter()

const kbId = computed(() => parseInt(route.params.id))

const kbInfo = reactive({ name: '', description: '', icon: '' })
const activeTab = ref(route.query.tab || 'documents')
const sidebarCollapsed = ref(false)
const documents = ref([])
const searchText = ref('')
const ragQuery = ref('')
const ragAnswer = ref('')
const ragSources = ref([])
const ragLatency = ref(0)
const ragLoading = ref(false)
const ragOptimizer = ref('none')
const ragModel = ref('qwen3.7-plus')
const ragEmbedModel = ref('text-embedding-v4')
const ragTemperature = ref(0.7)
const ragRerankTopN = ref(5)
const availableModels = ref(['qwen3.7-plus', 'qwen-math-turbo', 'qwen3-vl-235b-a22b-thinking', 'qwen3-vl-32b-thinking'])
const showSources = ref(true)
const showAdvancedSearch = ref(false)
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
const isUploading = ref(false)
const importCancelled = ref(false)
const uploadedFiles = ref([])
const uploadedTempIds = ref([])
const previewResults = ref([])
const importLoading = ref(false)
const selectedPreviewFile = ref(null)
const previewCurrentPage = ref(1)

const importConfig = reactive({ file_type: 'document', chunk_size: 512, chunk_overlap: 128, splitter_type: 'sentence', reader_type: null, embed_model: 'text-embedding-v4' })

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
      { value: 'pymupdf4llm', label: 'PyMuPDF4LLM' },
    ]
  }
  // Mixed or single non-PDF type
  return [
    { value: null, label: '自动检测' },
  ]
})
const searchConfig = reactive({ top_k: 5, vector_weight: 0.7, keyword_weight: 0.3 })
const weightSum = computed(() => searchConfig.vector_weight + searchConfig.keyword_weight)
const savedSearchConfig = reactive({ top_k: 5, vector_weight: 0.7, keyword_weight: 0.3 })
const editForm = reactive({ content: '', chunkId: null })

const showGraphDialog = ref(false)
const graphMethod = ref('simple')
const graphLoading = ref(false)
const graphNodes = ref([])
const graphEdges = ref([])
const graphStats = ref({ nodes: 0, edges: 0 })
const graphContainerRef = ref(null)

// ── Doc Graph ──
const showDocGraphDialog = ref(false)
const docGraphLoading = ref(false)
const docGraphNodes = ref([])
const docGraphEdges = ref([])
const docGraphStats = ref({ nodes: 0, edges: 0 })
const selectedDocForGraph = ref(null)
const docGraphMethod = ref('schema')

// ── Answer Graph ──
const showAnswerGraphDialog = ref(false)
const answerGraphLoading = ref(false)
const answerGraphNodes = ref([])
const answerGraphEdges = ref([])
const answerGraphStats = ref({ nodes: 0, edges: 0 })

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
  return `/uploads/kb_icons/${icon}`
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

onMounted(() => { loadKbInfo(); loadSearchConfig(); loadDocuments() })

watch(activeTab, (tab) => {
  if (tab === 'documents') { loadDocuments() }
})

watch(selectedPreviewFile, () => { previewCurrentPage.value = 1 })

async function loadKbInfo() {
  try {
    if (isNaN(kbId.value)) {
      router.push('/knowledge')
      return
    }
    const res = await api.knowledge.get(kbId.value)
    Object.assign(kbInfo, res.data)
    Object.assign(configForm, { name: res.data.name, description: res.data.description, icon: res.data.icon || '' })
  } catch (error) { ElMessage.error(error.message || '加载失败') }
}

async function loadDocuments() {
  try {
    if (isNaN(kbId.value)) return
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
  if (cmd === 'graph') { handleShowDocGraph(doc) }
  else if (cmd === 'download') { handleDownload(doc) }
  else if (cmd === 'delete') { handleDeleteDocument(doc) }
}

function handleShowDocGraph(doc) {
  selectedDocForGraph.value = doc
  docGraphNodes.value = []
  docGraphEdges.value = []
  docGraphStats.value = { nodes: 0, edges: 0 }
  showDocGraphDialog.value = true
  docGraphLoading.value = true
  handleLoadDocGraph()
}

async function handleLoadDocGraph() {
  const doc = selectedDocForGraph.value
  if (!doc) return
  try {
    const res = await api.knowledge.getDocGraph(kbId.value, doc.id)
    if (res.data.nodes?.length) {
      docGraphNodes.value = res.data.nodes
      docGraphEdges.value = res.data.edges || []
      docGraphStats.value = { nodes: docGraphNodes.value.length, edges: docGraphEdges.value.length }
      nextTick(() => initDocGraphNetwork())
    } else {
      await doExtractDocGraph()
    }
  } catch {
    await doExtractDocGraph()
  } finally {
    docGraphLoading.value = false
  }
}

async function doExtractDocGraph() {
  const doc = selectedDocForGraph.value
  if (!doc) return
  docGraphLoading.value = true
  try {
    const res = await api.knowledge.extractDocGraph(kbId.value, doc.id)
    docGraphNodes.value = res.data.nodes || []
    docGraphEdges.value = res.data.edges || []
    docGraphStats.value = { nodes: docGraphNodes.value.length, edges: docGraphEdges.value.length }
    ElMessage.success(`抽取完成：${docGraphStats.value.nodes} 节点，${docGraphStats.value.edges} 关系`)
    nextTick(() => initDocGraphNetwork())
  } catch (error) {
    ElMessage.error(error.message || '抽取失败')
  } finally {
    docGraphLoading.value = false
  }
}

async function handleExtractDocGraph() {
  const doc = selectedDocForGraph.value
  if (!doc) return
  docGraphLoading.value = true
  await doExtractDocGraph()
  docGraphLoading.value = false
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
    selectedDoc.value = null
    chunks.value = []
    showDocGraphDialog.value = false
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
      embed_model: ragEmbedModel.value,
      top_k: savedSearchConfig.top_k,
      rerank_top_n: ragRerankTopN.value,
      temperature: ragTemperature.value
    })
    ragAnswer.value = res.data.answer
    ragSources.value = res.data.sources || []
    ragLatency.value = res.data.latency_ms || 0
  } catch (error) { ElMessage.error(error.message || '查询失败') }
  finally { ragLoading.value = false }
}

async function loadRagModels(provider = 'dashscope') {
  try {
    const res = await api.rag.models(provider)
    if (res.data?.llm?.length) { availableModels.value = res.data.llm }
    if (!availableModels.value.includes(ragModel.value)) {
      ragModel.value = availableModels.value[0] || 'glm-4'
    }
  } catch { /* keep defaults */ }
}

async function loadSearchConfig() {
  try {
    const res = await api.knowledge.getSearchConfig(kbId.value)
    Object.assign(searchConfig, res.data)
    Object.assign(savedSearchConfig, res.data)
  } catch (error) { /* silent */ }
}

async function handleSaveSearchConfig() {
  saveConfigLoading.value = true
  try {
    await api.knowledge.saveSearchConfig(kbId.value, searchConfig)
    Object.assign(savedSearchConfig, searchConfig)
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
      tempId: null,
      name: file.name, size: file.size, raw: file,
      status: 'pending', progress: 0
    })
  }
}

function removeUploadedFile(id) { uploadedFiles.value = uploadedFiles.value.filter(f => f.id !== id) }

async function submitUpload() {
  isUploading.value = true
  importCancelled.value = false
  for (const file of uploadedFiles.value) {
    if (importCancelled.value) break
    file.status = 'uploading'; file.progress = 0
    try {
      const res = await api.knowledge.uploadDocument(kbId.value, file.raw)
      if (importCancelled.value) break
      file.tempId = res.data.temp_id
      uploadedTempIds.value.push(res.data.temp_id)
      file.status = 'done'; file.progress = 100
    } catch (error) {
      file.status = 'error'
      ElMessage.error(`上传 ${file.name} 失败: ${error.message}`)
    }
  }
  isUploading.value = false
  if (!importCancelled.value) importStep.value = 1
}

async function loadPreview() {
  try {
    const res = await api.knowledge.importPreview(kbId.value, { temp_ids: uploadedTempIds.value, config: importConfig })
    previewResults.value = res.data
    if (uploadedTempIds.value.length) { selectedPreviewFile.value = uploadedTempIds.value[0] }
    importStep.value = 2
  } catch (error) { ElMessage.error('预览失败: ' + error.message) }
}

async function doConfirmImport() {
  importLoading.value = true
  try {
    await api.knowledge.confirmImport(kbId.value, { temp_ids: uploadedTempIds.value, config: importConfig })
    ElMessage.success('导入任务已启动，正在解析...')
    showImportDialog.value = false
    importStep.value = 0
    uploadedFiles.value = []
    uploadedTempIds.value = []
    previewResults.value = []
    isUploading.value = false
    await loadDocuments()
    // 后台轮询刷新文档列表
    let pollCount = 0
    const pollTimer = setInterval(async () => {
      pollCount++
      await loadDocuments()
      // 检查所有文档是否都已完成
      const docs = documents.value
      const allCompleted = docs.length > 0 && docs.every(d => d.status === 'completed' || d.status === 'failed')
      if (allCompleted) {
        clearInterval(pollTimer)
        const failedCount = docs.filter(d => d.status === 'failed').length
        if (failedCount > 0) {
          ElMessage.warning(`${docs.length - failedCount} 个文档导入成功，${failedCount} 个文档导入失败`)
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

async function closeImportDialog() {
  showImportDialog.value = false
  importStep.value = 0
  importCancelled.value = true
  uploadedFiles.value = []
  uploadedTempIds.value = []
  previewResults.value = []
  isUploading.value = false
}

// ── Graph RAG ──────────────────────────────────────────────────

function initGraphNetwork() {
  const container = document.getElementById('graphCanvas')
  if (!container) return

  const nodes = graphNodes.value.map(n => ({
    id: n.id,
    label: n.label,
    title: `${n.label}\n类型: ${n.type}`,
    color: {
      background: getNodeColor(n.type),
      border: '#3b82f6',
      highlight: { background: getNodeColor(n.type), border: '#60a5fa' }
    },
    font: { color: '#f1f5f9', size: 14, face: 'Arial', strokeWidth: 2, strokeColor: '#0b1121' },
    borderWidth: 2,
    size: 22,
    shadow: { enabled: true, color: 'rgba(59,130,246,0.3)', size: 6 }
  }))

  const edges = graphEdges.value.map(e => ({
    from: e.from_id,
    to: e.to_id,
    label: e.label,
    arrows: 'to',
    color: { color: '#475569', highlight: '#60a5fa', hover: '#60a5fa' },
    font: { align: 'middle', color: '#94a3b8', size: 11, strokeWidth: 2, strokeColor: '#0b1121' },
    smooth: { type: 'curvedCW', roundness: 0.1 },
    width: 1.5
  }))

  const data = { nodes: new vis.DataSet(nodes), edges: new vis.DataSet(edges) }
  const options = {
    physics: {
      solver: 'forceAtlas2Based',
      forceAtlas2Based: { gravitationalConstant: -40, centralGravity: 0.005, springLength: 120, springConstant: 0.08 },
      stabilization: { iterations: 100 }
    },
    interaction: {
      hover: true, tooltipDelay: 200,
      navigationButtons: true, keyboard: true
    },
    layout: { improvedLayout: true },
    edges: { smooth: { type: 'curvedCW' } }
  }

  if (window._graphNetwork) window._graphNetwork.destroy()
  window._graphNetwork = new vis.Network(container, data, options)
}

function initDocGraphNetwork() {
  const container = document.getElementById('docGraphCanvas')
  if (!container) return
  const nodes = docGraphNodes.value.map(n => ({
    id: n.id, label: n.label,
    title: `${n.label}\n类型: ${n.type}`,
    color: { background: getNodeColor(n.type), border: '#3b82f6', highlight: { background: getNodeColor(n.type), border: '#60a5fa' } },
    font: { color: '#f1f5f9', size: 14, face: 'Arial', strokeWidth: 2, strokeColor: '#0b1121' },
    borderWidth: 2, size: 22,
    shadow: { enabled: true, color: 'rgba(59,130,246,0.3)', size: 6 }
  }))
  const edges = docGraphEdges.value.map(e => ({
    from: e.from_id, to: e.to_id, label: e.label, arrows: 'to',
    color: { color: '#475569', highlight: '#60a5fa', hover: '#60a5fa' },
    font: { align: 'middle', color: '#94a3b8', size: 11, strokeWidth: 2, strokeColor: '#0b1121' },
    smooth: { type: 'curvedCW', roundness: 0.1 }, width: 1.5
  }))
  const data = { nodes: new vis.DataSet(nodes), edges: new vis.DataSet(edges) }
  const options = {
    physics: { solver: 'forceAtlas2Based', forceAtlas2Based: { gravitationalConstant: -40, centralGravity: 0.005, springLength: 120, springConstant: 0.08 }, stabilization: { iterations: 100 } },
    interaction: { hover: true, tooltipDelay: 200, navigationButtons: true, keyboard: true },
    layout: { improvedLayout: true },
    edges: { smooth: { type: 'curvedCW' } }
  }
  if (window._docGraphNetwork) window._docGraphNetwork.destroy()
  window._docGraphNetwork = new vis.Network(container, data, options)
}

function initAnswerGraphNetwork() {
  const container = document.getElementById('answerGraphCanvas')
  if (!container) return
  const nodes = answerGraphNodes.value.map(n => ({
    id: n.id, label: n.label,
    title: `${n.label}\n类型: ${n.type}`,
    color: { background: getNodeColor(n.type), border: '#3b82f6', highlight: { background: getNodeColor(n.type), border: '#60a5fa' } },
    font: { color: '#f1f5f9', size: 14, face: 'Arial', strokeWidth: 2, strokeColor: '#0b1121' },
    borderWidth: 2, size: 22,
    shadow: { enabled: true, color: 'rgba(59,130,246,0.3)', size: 6 }
  }))
  const edges = answerGraphEdges.value.map(e => ({
    from: e.from_id, to: e.to_id, label: e.label, arrows: 'to',
    color: { color: '#475569', highlight: '#60a5fa', hover: '#60a5fa' },
    font: { align: 'middle', color: '#94a3b8', size: 11, strokeWidth: 2, strokeColor: '#0b1121' },
    smooth: { type: 'curvedCW', roundness: 0.1 }, width: 1.5
  }))
  const data = { nodes: new vis.DataSet(nodes), edges: new vis.DataSet(edges) }
  const options = {
    physics: { solver: 'forceAtlas2Based', forceAtlas2Based: { gravitationalConstant: -40, centralGravity: 0.005, springLength: 120, springConstant: 0.08 }, stabilization: { iterations: 100 } },
    interaction: { hover: true, tooltipDelay: 200, navigationButtons: true, keyboard: true },
    layout: { improvedLayout: true },
    edges: { smooth: { type: 'curvedCW' } }
  }
  if (window._answerGraphNetwork) window._answerGraphNetwork.destroy()
  window._answerGraphNetwork = new vis.Network(container, data, options)
}

function getNodeColor(type) {
  const colors = {
    '人物': '#1e3a5f', '组织': '#1a4a4a', '地点': '#2a3f5f',
    '时间': '#3a2a5f', '事件': '#1e3a5f', '概念': '#2a3f5f',
    '技术': '#1a4a5f', '产品': '#2a3a4f'
  }
  return colors[type] || '#1e293b'
}

async function handleExtractGraph() {
  graphLoading.value = true
  try {
    const res = await api.knowledge.extractGraph(kbId.value, graphMethod.value)
    ElMessage.success(res.data.message || '抽取完成')
    await handleRefreshGraph()
  } catch (error) {
    ElMessage.error(error.message || '抽取失败')
  } finally {
    graphLoading.value = false
  }
}

async function handleRefreshGraph() {
  try {
    const res = await api.knowledge.getGraph(kbId.value)
    graphNodes.value = res.data.nodes || []
    graphEdges.value = res.data.edges || []
    graphStats.value = { nodes: graphNodes.value.length, edges: graphEdges.value.length }
    // Wait for DOM update then init vis
    nextTick(() => initGraphNetwork())
  } catch (error) {
    ElMessage.error(error.message || '获取图谱数据失败')
  }
}

async function handleAnswerGraph() {
  if (!ragAnswer.value.trim()) return
  answerGraphLoading.value = true
  try {
    const res = await api.rag.answerGraph(ragAnswer.value)
    answerGraphNodes.value = res.data.nodes || []
    answerGraphEdges.value = res.data.edges || []
    answerGraphStats.value = { nodes: answerGraphNodes.value.length, edges: answerGraphEdges.value.length }
    showAnswerGraphDialog.value = true
    nextTick(() => initAnswerGraphNetwork())
  } catch (error) {
    ElMessage.error(error.message || '抽取答案图谱失败')
  } finally {
    answerGraphLoading.value = false
  }
}

// Watch dialog open to load graph data
watch(showGraphDialog, (val) => {
  if (val) handleRefreshGraph()
})

// Clean up answer graph data when dialog closes
watch(showAnswerGraphDialog, (val) => {
  if (!val) {
    answerGraphNodes.value = []
    answerGraphEdges.value = []
    answerGraphStats.value = { nodes: 0, edges: 0 }
    if (window._answerGraphNetwork) {
      window._answerGraphNetwork.destroy()
      window._answerGraphNetwork = null
    }
  }
})
</script>

<style scoped>
/* ═══ HUD CSS Variables ═══ */
.kb-detail-layout {
  --hud-panel-bg: rgba(255,255,255,0.03);
  --hud-panel-border: rgba(59,130,246,0.15);
  --hud-glow: rgba(59,130,246,0.08);
  --hud-accent: #3b82f6;
  --hud-font-mono: 'SF Mono', 'Cascadia Code', 'JetBrains Mono', monospace;
}

/* HUD Grid Background Overlay */
.kb-detail-content {
  position: relative;
}
.kb-detail-content::before {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background-image:
    repeating-linear-gradient(0deg, transparent, transparent 40px, rgba(59,130,246,0.015) 40px, rgba(59,130,246,0.015) 41px),
    repeating-linear-gradient(90deg, transparent, transparent 40px, rgba(59,130,246,0.015) 40px, rgba(59,130,246,0.015) 41px);
}

/* Subtle scan-line overlay */
.kb-detail-content::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px);
}

/* HUD Corner Bracket mixin — applied to panels via shared class or direct */
.hud-panel {
  position: relative;
  background: var(--hud-panel-bg);
  border: 1px solid var(--hud-panel-border);
  border-radius: var(--r-md);
}
.hud-panel::before {
  content: '';
  position: absolute;
  top: -1px; left: -1px;
  width: 14px; height: 14px;
  border-top: 2px solid rgba(59,130,246,0.25);
  border-left: 2px solid rgba(59,130,246,0.25);
  pointer-events: none;
  border-radius: 0;
}
.hud-panel::after {
  content: '';
  position: absolute;
  bottom: -1px; right: -1px;
  width: 14px; height: 14px;
  border-bottom: 2px solid rgba(59,130,246,0.25);
  border-right: 2px solid rgba(59,130,246,0.25);
  pointer-events: none;
  border-radius: 0;
}

/* ═══ Collapsible Sidebar Layout ═══ */
.kb-detail-layout { display: flex; height: 100%; overflow: hidden; }

.kb-detail-sidebar {
  width: 240px; flex-shrink: 0;
  background: rgba(255,255,255,0.04);
  border-right: 1px solid rgba(255,255,255,0.08);
  display: flex; flex-direction: column;
  transition: width 0.2s ease;
  overflow: hidden;
  position: relative;
}
.kb-detail-sidebar.collapsed { width: 56px; }

.kb-detail-header {
  padding: 16px 14px 12px;
  cursor: pointer;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  flex-shrink: 0;
}
.kb-detail-sidebar.collapsed .kb-detail-header { padding: 16px 10px; display: flex; justify-content: center; }

.back-row {
  display: flex; align-items: center; gap: 6px;
  font-size: 13px; color: var(--t-3); margin-bottom: 10px;
  transition: color 0.15s;
}
.back-row:hover { color: var(--t-0); }
.kb-detail-sidebar.collapsed .back-row { margin-bottom: 0; }

.kb-info-row { display: flex; gap: 10px; align-items: center; }
.kb-icon-sm {
  width: 36px; height: 36px;
  border-radius: var(--r-sm);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.kb-icon-sm-img { width: 36px; height: 36px; border-radius: var(--r-sm); object-fit: cover; flex-shrink: 0; }
.kb-info-row .name { font-size: 14px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.kb-info-row .desc { font-size: 11px; color: var(--t-3); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.detail-tabs { flex: 1; overflow-y: auto; padding: 8px 6px; display: flex; flex-direction: column; gap: 2px; }
.kb-detail-sidebar.collapsed .detail-tabs { padding: 8px 4px; align-items: center; }

.detail-tab {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 12px;
  border-radius: var(--r-sm);
  cursor: pointer;
  transition: all 0.15s;
  color: var(--t-2); font-size: 13px;
  white-space: nowrap;
}
.detail-tab:hover { background: rgba(255,255,255,0.06); color: var(--t-0); }
.detail-tab.active { background: rgba(59,130,246,0.12); color: var(--ac); }
.kb-detail-sidebar.collapsed .detail-tab { padding: 10px; justify-content: center; }

.detail-tab svg { flex-shrink: 0; color: currentColor; }

.tab-badge {
  margin-left: auto;
  background: rgba(255,255,255,0.08);
  padding: 0 7px; height: 18px;
  border-radius: 9px;
  font-size: 11px; display: flex; align-items: center; justify-content: center;
  color: var(--t-3); font-family: var(--font-mono);
}
.detail-tab.active .tab-badge { background: rgba(59,130,246,0.2); color: var(--ac); }

/* ═══ Toggle Button ═══ */
.sidebar-toggle {
  position: absolute;
  bottom: 12px; right: -18px;
  width: 28px; height: 28px;
  border-radius: 50%;
  background: rgba(59,130,246,0.15);
  border: 1px solid rgba(59,130,246,0.3);
  color: var(--t-2);
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.2s ease;
  z-index: 10;
  font-family: inherit;
  box-shadow: 0 0 0 0 var(--hud-glow);
}
.sidebar-toggle:hover {
  background: rgba(59,130,246,0.25);
  border-color: rgba(59,130,246,0.5);
  color: var(--t-0);
  box-shadow: 0 0 12px 2px var(--hud-glow);
}
.kb-detail-sidebar.collapsed .sidebar-toggle { right: -14px; }
.sidebar-toggle svg { transition: transform 0.2s ease; }

/* ═══ Right Content ═══ */
.kb-detail-content {
  flex: 1; overflow-y: auto;
  padding: 24px 28px;
  min-width: 0;
  position: relative;
  z-index: 0;
}
.kb-detail-content > * {
  position: relative;
  z-index: 1;
}

/* ═══ RAG Tab — redesigned full-width card layout ═══ */
.rag-tab { display: flex; flex-direction: column; gap: 16px; }

.rag-query-card {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: var(--r-md);
  padding: 20px;
}
.rag-query-header {
  display: flex; align-items: center; gap: 8px;
  font-size: 14px; font-weight: 600; color: var(--t-0);
  margin-bottom: 14px;
}
.rag-query-header svg { opacity: .6; }
.rag-query-input {
  width: 100%; min-height: 80px; resize: vertical;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: var(--r-sm);
  color: var(--t-0); font-size: 13px; line-height: 1.6;
  padding: 12px 14px; font-family: inherit;
  transition: border-color .2s;
}
.rag-query-input:focus { outline: none; border-color: var(--ac); }
.rag-query-input::placeholder { color: var(--t-3); }
.rag-query-footer {
  display: flex; align-items: center; justify-content: space-between;
  margin-top: 12px; gap: 12px;
}
.rag-model-selects { display: flex; gap: 8px; }
.rag-model-selects .qa-param-select { height: 32px; font-size: 12px; max-width: 160px; }
.rag-query-actions { display: flex; gap: 8px; flex-shrink: 0; }

/* Advanced card */
.rag-advanced-card {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: var(--r-md);
  padding: 16px 20px;
}
.rag-advanced-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
}
.adv-field { display: flex; flex-direction: column; gap: 4px; }
.adv-field label { font-size: 11px; color: var(--t-3); font-weight: 500; }
.adv-field .config-number-input { width: 100%; }
.adv-field .config-number-input:deep(.el-input-number) { width: 100%; }
.adv-field .config-number-input:deep(.el-input__wrapper) { background: rgba(255,255,255,0.04) !important; }
.adv-field .config-number-input:deep(.el-input__inner) { color: var(--t-0) !important; font-size: 12px !important; }

/* Answer card */
.rag-answer-card {
  background: rgba(16,185,129,0.04);
  border: 1px solid rgba(16,185,129,0.12);
  border-radius: var(--r-md);
}
.rag-answer-header {
  display: flex; align-items: center; gap: 8px;
  padding: 14px 18px;
  border-bottom: 1px solid rgba(16,185,129,0.08);
  font-size: 13px; font-weight: 600; color: var(--t-0);
}
.rag-answer-header svg { stroke: var(--emerald); }
.rag-answer-actions { margin-left: auto; }
.rag-answer-body {
  padding: 16px 18px;
  font-size: 13px; line-height: 1.7; color: var(--t-1);
  white-space: pre-wrap;
}
.qa-latency { font-size: 11px; color: var(--t-3); font-family: var(--font-mono); margin-left: 8px; }

/* Sources card */
.rag-sources-card {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: var(--r-md);
  overflow: hidden;
}
.rag-sources-header {
  display: flex; align-items: center; gap: 8px;
  padding: 12px 16px;
  cursor: pointer; user-select: none;
  font-size: 13px; font-weight: 500; color: var(--t-2);
  transition: color .15s;
}
.rag-sources-header:hover { color: var(--t-0); }
.rag-sources-header svg { flex-shrink: 0; }
.rag-sources-body { border-top: 1px solid rgba(255,255,255,0.04); }
.qa-source-item { display: flex; gap: 12px; padding: 14px 16px; align-items: flex-start; }
.qa-source-item + .qa-source-item { border-top: 1px solid rgba(255,255,255,0.04); }
.source-rank {
  width: 24px; height: 24px; border-radius: 6px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700; color: var(--t-3);
  background: rgba(255,255,255,0.06);
}
.source-body { flex: 1; min-width: 0; }
.source-meta { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.source-score { font-size: 11px; color: var(--ac); font-weight: 600; font-family: var(--font-mono); }
.source-filename { font-size: 11px; color: var(--t-3); }
.source-content { font-size: 12px; color: var(--t-2); line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }

/* Empty & Loading states */
.rag-empty-state {
  display: flex; flex-direction: column; align-items: center;
  padding: 60px 0; color: var(--t-3); gap: 12px;
}
.rag-empty-state svg { opacity: .3; }
.rag-empty-state p { font-size: 13px; }
.rag-loading {
  display: flex; flex-direction: column; align-items: center;
  padding: 40px 0; color: var(--t-3); gap: 12px;
}
.rag-loading p { font-size: 13px; }
.loading-dots { display: flex; gap: 6px; }
.loading-dots span {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--ac); animation: dot-bounce 1.2s infinite ease-in-out;
}
.loading-dots span:nth-child(2) { animation-delay: .16s; }
.loading-dots span:nth-child(3) { animation-delay: .32s; }
@keyframes dot-bounce {
  0%, 80%, 100% { transform: scale(.6); opacity: .4; }
  40% { transform: scale(1); opacity: 1; }
}

/* ═══════════════════════════════════════════
   Task 3: Documents Tab — HUD Styling
   ═══════════════════════════════════════════ */

/* Doc Panel — HUD card with corner brackets */
.doc-panel {
  position: relative;
  background: var(--hud-panel-bg);
  border: 1px solid var(--hud-panel-border);
  border-radius: var(--r-md);
  padding: 20px 24px;
  overflow: hidden;
}
.doc-panel::before {
  content: '';
  position: absolute;
  top: -1px; left: -1px;
  width: 14px; height: 14px;
  border-top: 2px solid rgba(59,130,246,0.25);
  border-left: 2px solid rgba(59,130,246,0.25);
  pointer-events: none;
}
.doc-panel::after {
  content: '';
  position: absolute;
  bottom: -1px; right: -1px;
  width: 14px; height: 14px;
  border-bottom: 2px solid rgba(59,130,246,0.25);
  border-right: 2px solid rgba(59,130,246,0.25);
  pointer-events: none;
}

/* Doc toolbar */
.doc-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  gap: 12px;
}
.doc-toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Table HUD styling */
.doc-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.doc-table thead th {
  padding: 10px 12px;
  text-align: left;
  font-weight: 500;
  font-size: 12px;
  color: var(--t-3);
  border-bottom: 1px solid rgba(255,255,255,0.06);
  white-space: nowrap;
}
.doc-table tbody tr {
  transition: all 0.15s ease;
}
.doc-table tbody tr:hover {
  box-shadow: 0 0 12px 0 var(--hud-glow);
  background: rgba(59,130,246,0.04);
}
.doc-table tbody td {
  padding: 10px 12px;
  border-bottom: 1px solid rgba(255,255,255,0.04);
  color: var(--t-1);
}
.doc-table tbody tr:last-child td {
  border-bottom: none;
}

/* File name cell */
.file-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}
.file-type-icon {
  width: 28px; height: 28px;
  border-radius: 4px;
  display: flex; align-items: center; justify-content: center;
  font-size: 9px; font-weight: 700;
  letter-spacing: 0.5px;
  flex-shrink: 0;
  font-family: var(--hud-font-mono);
}
.ft-pdf { background: rgba(239,68,68,0.15); color: #ef4444; }
.ft-docx { background: rgba(59,130,246,0.15); color: #3b82f6; }
.ft-md { background: rgba(99,102,241,0.15); color: #6366f1; }
.ft-txt { background: rgba(148,163,184,0.15); color: #94a3b8; }
.ft-ppt { background: rgba(245,158,11,0.15); color: #f59e0b; }

/* Metric pill */
.metric-pill {
  font-family: var(--hud-font-mono);
  font-size: 12px;
  color: var(--t-2);
  background: rgba(255,255,255,0.04);
  padding: 2px 8px;
  border-radius: 4px;
}

/* Status badge HUD */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  font-weight: 500;
  padding: 2px 10px;
  border-radius: 10px;
  font-family: var(--hud-font-mono);
}
.status-badge .dot {
  width: 5px; height: 5px;
  border-radius: 50%;
  display: inline-block;
}
.st-completed { background: rgba(16,185,129,0.1); color: #10b981; }
.st-completed .dot { background: #10b981; }
.st-processing {
  background: rgba(59,130,246,0.1);
  color: #3b82f6;
  box-shadow: 0 0 6px 0 rgba(59,130,246,0.2);
}
.st-processing .dot { background: #3b82f6; animation: pulse-dot 1.5s infinite; }
.st-failed { background: rgba(239,68,68,0.1); color: #ef4444; }
.st-failed .dot { background: #ef4444; }

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

/* Action buttons */
.action-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}
.link-btn {
  background: transparent;
  border: 1px solid rgba(59,130,246,0.15);
  color: var(--ac);
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 4px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  transition: all 0.15s;
  font-family: inherit;
}
.link-btn:hover {
  background: rgba(59,130,246,0.1);
  border-color: rgba(59,130,246,0.3);
  box-shadow: 0 0 8px 0 var(--hud-glow);
}
.link-btn.danger {
  color: #ef4444;
  border-color: rgba(239,68,68,0.2);
}
.link-btn.danger:hover {
  background: rgba(239,68,68,0.1);
  border-color: rgba(239,68,68,0.3);
}

/* Chunks Panel HUD */
.chunks-panel {
  position: relative;
  background: var(--hud-panel-bg);
  border: 1px solid var(--hud-panel-border);
  border-radius: var(--r-md);
  padding: 20px 24px;
}
.chunks-panel::before {
  content: '';
  position: absolute;
  top: -1px; left: -1px;
  width: 14px; height: 14px;
  border-top: 2px solid rgba(59,130,246,0.25);
  border-left: 2px solid rgba(59,130,246,0.25);
  pointer-events: none;
}
.chunks-panel::after {
  content: '';
  position: absolute;
  bottom: -1px; right: -1px;
  width: 14px; height: 14px;
  border-bottom: 2px solid rgba(59,130,246,0.25);
  border-right: 2px solid rgba(59,130,246,0.25);
  pointer-events: none;
}
.chunks-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.back-btn {
  background: transparent;
  border: 1px solid rgba(255,255,255,0.1);
  color: var(--t-2);
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 4px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  transition: all 0.15s;
  font-family: inherit;
}
.back-btn:hover {
  background: rgba(255,255,255,0.06);
  color: var(--t-0);
}
.chunks-header .doc-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--t-0);
}
.chunks-header .chunks-count {
  margin-left: auto;
  font-size: 12px;
  color: var(--t-3);
  font-family: var(--hud-font-mono);
}

/* Chunk card HUD */
.chunk-card {
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: var(--r-sm);
  padding: 14px 16px;
  margin-bottom: 8px;
  transition: all 0.15s;
}
.chunk-card:hover {
  border-color: rgba(59,130,246,0.2);
  box-shadow: 0 0 8px 0 var(--hud-glow);
}
.chunk-card-body {
  display: flex;
  gap: 10px;
  margin-bottom: 8px;
}
.chunk-index {
  font-family: var(--hud-font-mono);
  font-size: 12px;
  color: var(--ac);
  font-weight: 600;
  flex-shrink: 0;
  min-width: 40px;
}
.chunk-content {
  font-size: 13px;
  color: var(--t-1);
  line-height: 1.6;
  word-break: break-word;
}
.chunk-actions {
  display: flex;
  gap: 6px;
  justify-content: flex-end;
}

/* Pagination HUD */
.chunks-pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 14px;
  margin-top: 8px;
  border-top: 1px solid rgba(255,255,255,0.06);
}
.page-info {
  font-size: 12px;
  color: var(--t-3);
  font-family: var(--hud-font-mono);
}
.page-size-select {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 4px;
  color: var(--t-1);
  font-size: 12px;
  padding: 2px 6px;
  margin-left: 8px;
  outline: none;
  font-family: inherit;
  cursor: pointer;
}
.page-size-select:focus {
  border-color: rgba(59,130,246,0.3);
}
.page-controls {
  display: flex;
  align-items: center;
}
.page-btn {
  width: 28px; height: 28px;
  border-radius: 4px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  color: var(--t-2);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
  font-family: inherit;
}
.page-btn:hover:not(:disabled) {
  background: rgba(59,130,246,0.1);
  border-color: rgba(59,130,246,0.3);
  color: var(--ac);
}
.page-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

/* ═══════════════════════════════════════════
   Task 4: RAG Tab — HUD Styling
   ═══════════════════════════════════════════ */

/* Query card HUD */
.rag-query-card {
  position: relative;
  background: var(--hud-panel-bg);
  border: 1px solid var(--hud-panel-border);
  border-radius: var(--r-md);
  padding: 24px;
}
.rag-query-card::before {
  content: '';
  position: absolute;
  top: -1px; left: -1px;
  width: 14px; height: 14px;
  border-top: 2px solid rgba(59,130,246,0.25);
  border-left: 2px solid rgba(59,130,246,0.25);
  pointer-events: none;
}
.rag-query-card::after {
  content: '';
  position: absolute;
  bottom: -1px; right: -1px;
  width: 14px; height: 14px;
  border-bottom: 2px solid rgba(59,130,246,0.25);
  border-right: 2px solid rgba(59,130,246,0.25);
  pointer-events: none;
}
.rag-query-input {
  width: 100%; min-height: 80px; resize: vertical;
  background: rgba(0,0,0,0.2);
  border: 1px solid rgba(59,130,246,0.15);
  border-radius: var(--r-sm);
  color: var(--t-0); font-size: 13px; line-height: 1.6;
  padding: 12px 14px; font-family: inherit;
  transition: border-color .2s;
}
.rag-query-input:focus { outline: none; border-color: var(--ac); box-shadow: 0 0 8px 0 var(--hud-glow); }
.rag-query-input::placeholder { color: var(--t-3); }

/* Select / Number input HUD */
.qa-param-select {
  background: rgba(0,0,0,0.25);
  border: 1px solid rgba(59,130,246,0.15);
  border-radius: 4px;
  color: var(--t-0);
  font-size: 12px;
  padding: 4px 8px;
  outline: none;
  font-family: inherit;
  cursor: pointer;
  height: 32px;
  transition: border-color .2s;
}
.qa-param-select:focus {
  border-color: var(--ac);
  box-shadow: 0 0 6px 0 var(--hud-glow);
}

/* Advanced card HUD */
.rag-advanced-card {
  position: relative;
  background: var(--hud-panel-bg);
  border: 1px solid var(--hud-panel-border);
  border-radius: var(--r-md);
  padding: 20px 24px;
}
.rag-advanced-card::before {
  content: '';
  position: absolute;
  top: -1px; left: -1px;
  width: 14px; height: 14px;
  border-top: 2px solid rgba(59,130,246,0.25);
  border-left: 2px solid rgba(59,130,246,0.25);
  pointer-events: none;
}
.rag-advanced-card::after {
  content: '';
  position: absolute;
  bottom: -1px; right: -1px;
  width: 14px; height: 14px;
  border-bottom: 2px solid rgba(59,130,246,0.25);
  border-right: 2px solid rgba(59,130,246,0.25);
  pointer-events: none;
}

/* Answer card HUD */
.rag-answer-card {
  position: relative;
  background: rgba(16,185,129,0.04);
  border: 1px solid rgba(16,185,129,0.15);
  border-radius: var(--r-md);
  overflow: hidden;
}
.rag-answer-card::before {
  content: '';
  position: absolute;
  top: -1px; left: -1px;
  width: 14px; height: 14px;
  border-top: 2px solid rgba(16,185,129,0.3);
  border-left: 2px solid rgba(16,185,129,0.3);
  pointer-events: none;
}
.rag-answer-card::after {
  content: '';
  position: absolute;
  bottom: -1px; right: -1px;
  width: 14px; height: 14px;
  border-bottom: 2px solid rgba(16,185,129,0.3);
  border-right: 2px solid rgba(16,185,129,0.3);
  pointer-events: none;
}
.rag-answer-header {
  display: flex; align-items: center; gap: 8px;
  padding: 14px 18px;
  border-bottom: 1px solid rgba(16,185,129,0.08);
  font-size: 13px; font-weight: 600; color: var(--t-0);
  background: rgba(16,185,129,0.03);
  box-shadow: 0 0 8px 0 rgba(16,185,129,0.05);
}

/* Sources card HUD */
.rag-sources-card {
  position: relative;
  background: var(--hud-panel-bg);
  border: 1px solid var(--hud-panel-border);
  border-radius: var(--r-md);
  overflow: hidden;
}
.rag-sources-card::before {
  content: '';
  position: absolute;
  top: -1px; left: -1px;
  width: 14px; height: 14px;
  border-top: 2px solid rgba(59,130,246,0.25);
  border-left: 2px solid rgba(59,130,246,0.25);
  pointer-events: none;
  z-index: 1;
}
.rag-sources-card::after {
  content: '';
  position: absolute;
  bottom: -1px; right: -1px;
  width: 14px; height: 14px;
  border-bottom: 2px solid rgba(59,130,246,0.25);
  border-right: 2px solid rgba(59,130,246,0.25);
  pointer-events: none;
  z-index: 1;
}
.qa-source-item {
  transition: all 0.15s;
}
.qa-source-item:hover {
  background: rgba(59,130,246,0.04);
  box-shadow: 0 0 8px 0 var(--hud-glow);
}

/* Empty & Loading states HUD */
.rag-empty-state {
  display: flex; flex-direction: column; align-items: center;
  padding: 60px 0; color: var(--t-3); gap: 12px;
  background: var(--hud-panel-bg);
  border: 1px dashed var(--hud-panel-border);
  border-radius: var(--r-md);
}
.rag-empty-state svg { opacity: .3; }
.rag-empty-state p { font-size: 13px; }
.rag-loading {
  display: flex; flex-direction: column; align-items: center;
  padding: 40px 0; color: var(--t-3); gap: 12px;
  background: var(--hud-panel-bg);
  border: 1px dashed var(--hud-panel-border);
  border-radius: var(--r-md);
}
.rag-loading p { font-size: 13px; }

/* ═══════════════════════════════════════════
   Task 5: Graph Tab — HUD Styling
   ═══════════════════════════════════════════ */

/* Graph tab wrapper inside doc-panel already has ::before/::after from .doc-panel */
.graph-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 18px;
  background: rgba(0,0,0,0.15);
  border-bottom: 1px solid rgba(59,130,246,0.1);
  position: relative;
}
.graph-toolbar::after {
  content: '';
  position: absolute;
  bottom: -1px; left: 18px; right: 18px;
  height: 1px;
  background: repeating-linear-gradient(90deg, rgba(59,130,246,0.15) 0, rgba(59,130,246,0.15) 4px, transparent 4px, transparent 8px);
}
.graph-toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.graph-toolbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.graph-stat {
  font-size: 12px;
  color: var(--t-3);
  display: flex;
  align-items: center;
  gap: 4px;
}
.graph-stat .num {
  font-family: var(--hud-font-mono);
  font-size: 14px;
  font-weight: 700;
  color: var(--ac);
}

/* Graph canvas container HUD */
.graph-canvas-container {
  position: relative;
  background: rgba(0,0,0,0.3);
  border: 1px solid rgba(59,130,246,0.1);
  min-height: 480px;
  border-radius: 0 0 var(--r-md) var(--r-md);
  box-shadow: inset 0 0 20px 0 rgba(59,130,246,0.03);
}
.graph-canvas {
  width: 100%;
  height: 480px;
}
.graph-empty {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--t-3);
  font-size: 13px;
}
.empty-icon-box {
  opacity: .3;
}

/* Graph modal toolbar */
.modal-graph .graph-toolbar {
  border-bottom: 1px solid rgba(59,130,246,0.1);
  background: rgba(0,0,0,0.15);
  padding: 12px 20px;
}
.graph-canvas-area {
  background: rgba(0,0,0,0.3);
  border: 1px solid rgba(59,130,246,0.1);
  min-height: 400px;
  border-radius: 0;
  position: relative;
}
.graph-empty-state {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--t-3);
  font-size: 13px;
}
.graph-empty-state .icon { opacity: .3; }

/* ═══════════════════════════════════════════
   Task 6: Config Tab — HUD Styling
   ═══════════════════════════════════════════ */

.config-section {
  position: relative;
  background: var(--hud-panel-bg);
  border: 1px solid var(--hud-panel-border);
  border-radius: var(--r-md);
  padding: 28px 32px;
  max-width: 600px;
}
.config-section::before {
  content: '';
  position: absolute;
  top: -1px; left: -1px;
  width: 14px; height: 14px;
  border-top: 2px solid rgba(59,130,246,0.25);
  border-left: 2px solid rgba(59,130,246,0.25);
  pointer-events: none;
}
.config-section::after {
  content: '';
  position: absolute;
  bottom: -1px; right: -1px;
  width: 14px; height: 14px;
  border-bottom: 2px solid rgba(59,130,246,0.25);
  border-right: 2px solid rgba(59,130,246,0.25);
  pointer-events: none;
}
.field-group {
  margin-bottom: 28px;
}
.field-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--ac);
  margin-bottom: 8px;
}
.icon-upload-area {
  display: flex;
  align-items: center;
  gap: 12px;
}
.icon-preview-box {
  width: 48px; height: 48px;
  border-radius: var(--r-sm);
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(59,130,246,0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--t-3);
  transition: all 0.15s;
}
.icon-preview-box:hover {
  border-color: rgba(59,130,246,0.4);
  box-shadow: 0 0 8px 0 var(--hud-glow);
}
.icon-preview-img {
  width: 100%; height: 100%;
  object-fit: cover;
  border-radius: var(--r-sm);
}
.icon-upload-tip {
  font-size: 12px;
  color: var(--t-3);
}
.hidden-input { display: none; }

/* Config input fields HUD */
.field-input-el:deep(.el-input__wrapper) {
  background: rgba(0,0,0,0.2) !important;
  border: 1px solid rgba(59,130,246,0.15) !important;
  border-radius: 4px !important;
  box-shadow: none !important;
  transition: border-color .2s;
}
.field-input-el:deep(.el-input__wrapper:hover) {
  border-color: rgba(59,130,246,0.3) !important;
}
.field-input-el:deep(.el-input__wrapper.is-focus) {
  border-color: var(--ac) !important;
  box-shadow: 0 0 6px 0 var(--hud-glow) !important;
}
.field-input-el:deep(.el-input__inner) {
  color: var(--t-0) !important;
  font-size: 13px !important;
  background: transparent !important;
}
.field-input-el:deep(.el-textarea__inner) {
  background: rgba(0,0,0,0.2) !important;
  border: 1px solid rgba(59,130,246,0.15) !important;
  border-radius: 4px !important;
  color: var(--t-0) !important;
  font-size: 13px !important;
  box-shadow: none !important;
  transition: border-color .2s;
}
.field-input-el:deep(.el-textarea__inner:focus) {
  border-color: var(--ac) !important;
  box-shadow: 0 0 6px 0 var(--hud-glow) !important;
}
.field-input-el:deep(.el-textarea__inner::placeholder) {
  color: var(--t-3) !important;
}

/* Save button */
.config-section .btn-primary.btn-lg {
  padding: 10px 32px;
  font-size: 14px;
  border-radius: 6px;
  box-shadow: 0 0 0 0 var(--hud-glow);
  transition: all 0.2s;
}
.config-section .btn-primary.btn-lg:hover {
  box-shadow: 0 0 14px 3px var(--hud-glow);
}

/* ═══════════════════════════════════════════
   Task 7: Modal HUD Styling
   ═══════════════════════════════════════════ */

/* Modal overlay */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  opacity: 0;
  visibility: hidden;
  transition: all 0.2s;
}
.modal-overlay.show {
  opacity: 1;
  visibility: visible;
}

/* Modal HUD panel */
.modal {
  position: relative;
  background: rgba(15,23,42,0.95);
  border: 1px solid rgba(59,130,246,0.2);
  border-radius: var(--r-md);
  box-shadow: 0 0 30px 0 rgba(59,130,246,0.08), 0 8px 40px rgba(0,0,0,0.5);
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.modal::before {
  content: '';
  position: absolute;
  top: -1px; left: -1px;
  width: 16px; height: 16px;
  border-top: 2px solid rgba(59,130,246,0.3);
  border-left: 2px solid rgba(59,130,246,0.3);
  pointer-events: none;
  z-index: 1;
}
.modal::after {
  content: '';
  position: absolute;
  bottom: -1px; right: -1px;
  width: 16px; height: 16px;
  border-bottom: 2px solid rgba(59,130,246,0.3);
  border-right: 2px solid rgba(59,130,246,0.3);
  pointer-events: none;
  z-index: 1;
}

/* Modal header */
.modal-header {
  padding: 18px 24px;
  border-bottom: 1px solid rgba(59,130,246,0.1);
  position: relative;
}
.modal-header::after {
  content: '';
  position: absolute;
  bottom: -1px; left: 24px; right: 24px;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(59,130,246,0.3), transparent);
}
.modal-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--t-0);
}
.modal-subtitle {
  font-size: 12px;
  color: var(--t-3);
  margin-top: 4px;
}

/* Modal close button */
.modal-close {
  position: absolute;
  top: 14px; right: 14px;
  width: 28px; height: 28px;
  border-radius: 50%;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  color: var(--t-3);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
  z-index: 2;
  font-family: inherit;
}
.modal-close:hover {
  background: rgba(239,68,68,0.1);
  border-color: rgba(239,68,68,0.3);
  color: #ef4444;
  box-shadow: 0 0 8px 0 rgba(239,68,68,0.1);
}

/* Modal body */
.modal-body {
  padding: 20px 24px;
  overflow-y: auto;
  flex: 1;
}

/* Modal footer */
.modal-footer {
  padding: 14px 24px;
  border-top: 1px solid rgba(255,255,255,0.06);
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

/* Import modal sizing */
.modal-import {
  width: 680px;
  max-width: 90vw;
}

/* Edit chunk modal */
.modal-edit-chunk {
  width: 560px;
  max-width: 90vw;
}
.edit-chunk-textarea {
  width: 100%;
  min-height: 200px;
  resize: vertical;
  background: rgba(0,0,0,0.2);
  border: 1px solid rgba(59,130,246,0.15);
  border-radius: var(--r-sm);
  color: var(--t-0);
  font-size: 13px;
  line-height: 1.6;
  padding: 12px;
  font-family: inherit;
  transition: border-color .2s;
}
.edit-chunk-textarea:focus {
  outline: none;
  border-color: var(--ac);
  box-shadow: 0 0 8px 0 var(--hud-glow);
}

/* Graph modal */
.modal-graph {
  width: 800px;
  max-width: 90vw;
}
.modal-graph .graph-canvas-area {
  min-height: 450px;
}

/* Modal buttons HUD */
.modal .btn {
  padding: 7px 18px;
  font-size: 13px;
  border-radius: 4px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.15s;
  font-family: inherit;
  border: 1px solid transparent;
}
.modal .btn-primary {
  background: rgba(59,130,246,0.15);
  border-color: rgba(59,130,246,0.3);
  color: var(--ac);
}
.modal .btn-primary:hover {
  background: rgba(59,130,246,0.25);
  border-color: rgba(59,130,246,0.5);
  box-shadow: 0 0 10px 0 var(--hud-glow);
}
.modal .btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow: none;
}
.modal .btn-ghost {
  background: transparent;
  border-color: rgba(255,255,255,0.1);
  color: var(--t-2);
}
.modal .btn-ghost:hover {
  background: rgba(255,255,255,0.06);
  color: var(--t-0);
}

/* Wizard steps HUD */
.wizard-steps {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 18px 24px;
  gap: 0;
  background: rgba(0,0,0,0.1);
  border-bottom: 1px solid rgba(59,130,246,0.08);
}
.wizard-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--t-3);
  position: relative;
}
.wizard-step.active { color: var(--ac); }
.wizard-step.done { color: rgba(16,185,129,0.7); }
.wizard-step-num {
  width: 24px; height: 24px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700;
  font-family: var(--hud-font-mono);
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.1);
  transition: all 0.2s;
}
.wizard-step.active .wizard-step-num {
  background: rgba(59,130,246,0.2);
  border-color: rgba(59,130,246,0.4);
  box-shadow: 0 0 8px 0 var(--hud-glow);
}
.wizard-step.done .wizard-step-num {
  background: rgba(16,185,129,0.15);
  border-color: rgba(16,185,129,0.3);
}
.wizard-step-line {
  width: 40px;
  height: 1px;
  background: rgba(255,255,255,0.08);
  margin: 0 8px;
  margin-bottom: 20px;
  transition: background 0.2s;
}
.wizard-step-line.done { background: rgba(16,185,129,0.3); }

/* Upload zone HUD */
.upload-zone {
  border: 1px dashed rgba(59,130,246,0.2);
  border-radius: var(--r-md);
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.15s;
  background: rgba(59,130,246,0.02);
}
.upload-zone:hover {
  border-color: rgba(59,130,246,0.4);
  background: rgba(59,130,246,0.04);
  box-shadow: 0 0 12px 0 var(--hud-glow);
}
.upload-icon-large {
  margin-bottom: 12px;
  opacity: 0.5;
}
.upload-title {
  font-size: 14px;
  color: var(--t-1);
  margin-bottom: 4px;
}
.upload-hint {
  font-size: 12px;
  color: var(--t-3);
}

/* Upload file list */
.upload-file-list {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.upload-file-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: var(--r-sm);
}
.upload-file-info {
  flex: 1;
  min-width: 0;
}
.upload-file-name {
  font-size: 13px;
  color: var(--t-0);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.upload-file-size {
  font-size: 11px;
  color: var(--t-3);
}
.file-status {
  flex-shrink: 0;
}
.upload-progress-bar {
  width: 80px; height: 4px;
  background: rgba(255,255,255,0.06);
  border-radius: 2px;
  overflow: hidden;
}
.upload-progress-fill {
  height: 100%;
  background: var(--ac);
  border-radius: 2px;
  transition: width 0.3s;
}

/* Import config form */
.import-config-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.import-config-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.import-config-row label {
  font-size: 12px;
  color: var(--t-3);
  font-weight: 500;
}
.import-config-hint {
  font-size: 11px;
  color: var(--t-3);
  opacity: 0.7;
}
.config-input-select {
  background: rgba(0,0,0,0.2);
  border: 1px solid rgba(59,130,246,0.15);
  border-radius: 4px;
  color: var(--t-0);
  font-size: 13px;
  padding: 6px 10px;
  outline: none;
  font-family: inherit;
  cursor: pointer;
  transition: border-color .2s;
}
.config-input-select:focus {
  border-color: var(--ac);
  box-shadow: 0 0 6px 0 var(--hud-glow);
}
.config-row-slider {
  display: flex;
  align-items: center;
  gap: 12px;
}
.slider-val {
  width: 56px;
  background: rgba(0,0,0,0.2);
  border: 1px solid rgba(59,130,246,0.15);
  border-radius: 4px;
  color: var(--t-0);
  font-size: 12px;
  font-family: var(--hud-font-mono);
  text-align: center;
  padding: 4px;
}

/* Preview layout */
.preview-layout {
  display: flex;
  gap: 16px;
  min-height: 300px;
}
.preview-sidebar {
  width: 200px;
  flex-shrink: 0;
}
.preview-file-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.preview-file-tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: var(--r-sm);
  cursor: pointer;
  font-size: 12px;
  color: var(--t-2);
  transition: all 0.15s;
}
.preview-file-tab:hover {
  background: rgba(255,255,255,0.04);
}
.preview-file-tab.active {
  background: rgba(59,130,246,0.1);
  color: var(--ac);
  border: 1px solid rgba(59,130,246,0.15);
}
.preview-main {
  flex: 1;
  min-width: 0;
}
.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.preview-chunk-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.preview-chunk {
  display: flex;
  gap: 10px;
  padding: 8px 10px;
  background: rgba(255,255,255,0.02);
  border-radius: var(--r-sm);
  font-size: 12px;
  line-height: 1.5;
}
.preview-chunk-num {
  font-family: var(--hud-font-mono);
  color: var(--ac);
  font-weight: 600;
  flex-shrink: 0;
  min-width: 28px;
}
.preview-chunk-text {
  color: var(--t-2);
  word-break: break-word;
}

/* Confirm list */
.confirm-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.confirm-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: var(--r-sm);
}
.confirm-item .info {
  flex: 1;
}
.confirm-item .name {
  font-size: 13px;
  color: var(--t-0);
}
.confirm-item .status {
  font-size: 11px;
  color: var(--t-3);
}

/* Ensure el-dropdown also gets dark HUD style */
.el-dropdown-menu {
  background: rgba(15,23,42,0.98) !important;
  border: 1px solid rgba(59,130,246,0.15) !important;
}
.el-dropdown-menu__item {
  color: var(--t-2) !important;
  font-size: 13px !important;
}
.el-dropdown-menu__item:hover {
  background: rgba(59,130,246,0.1) !important;
  color: var(--t-0) !important;
}

/* Primary button HUD (reused across tabs) */
.btn-primary {
  background: rgba(59,130,246,0.15);
  border: 1px solid rgba(59,130,246,0.3);
  color: var(--ac);
  padding: 7px 16px;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.15s;
  font-family: inherit;
}
.btn-primary:hover {
  background: rgba(59,130,246,0.25);
  border-color: rgba(59,130,246,0.5);
  box-shadow: 0 0 10px 0 var(--hud-glow);
}
.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow: none;
}
.btn-sm {
  padding: 5px 12px;
  font-size: 12px;
}
.btn-lg {
  padding: 10px 24px;
  font-size: 14px;
}
.btn-ghost {
  background: transparent;
  border: 1px solid rgba(255,255,255,0.1);
  color: var(--t-2);
  padding: 7px 16px;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.15s;
  font-family: inherit;
}
.btn-ghost:hover {
  background: rgba(255,255,255,0.06);
  color: var(--t-0);
}

/* Search box */
.search-box {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(0,0,0,0.15);
  border: 1px solid rgba(59,130,246,0.1);
  border-radius: 4px;
  padding: 0 10px;
  transition: border-color .2s;
}
.search-box:focus-within {
  border-color: rgba(59,130,246,0.3);
  box-shadow: 0 0 6px 0 var(--hud-glow);
}
.search-box .ico {
  display: flex;
  color: var(--t-3);
  flex-shrink: 0;
}
.search-input-native:deep(.el-input__wrapper) {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
}
.search-input-native:deep(.el-input__inner) {
  color: var(--t-0) !important;
  font-size: 13px !important;
  height: 32px !important;
}
.search-input-native:deep(.el-input__inner::placeholder) {
  color: var(--t-3) !important;
}
</style>

