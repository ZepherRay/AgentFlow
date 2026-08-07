<template>
  <div class="workflow-page">
    <!-- ====== Editor Mode (full page) ====== -->
    <template v-if="showEditor">
      <div class="wf-editor">
        <!-- ======================== TOP BAR ======================== -->
        <div class="topbar">
          <div class="topbar-left">
            <button class="btn-back" @click="closeEditor">← 返回</button>
            <div class="topbar-divider"></div>
            <input class="wf-name" v-model="formData.name" placeholder="工作流名称" />
          </div>
          <div class="topbar-center">
            <div class="zoom-group">
              <button class="zoom-btn" @click="resetZoom" style="font-size:11px;padding:0 10px;width:auto;border-radius:0;">适应</button>
              <button class="zoom-btn" @click="zoomOut">−</button>
              <span class="zoom-label">{{ Math.round(canvasZoom * 100) }}%</span>
              <button class="zoom-btn" @click="zoomIn">+</button>
            </div>
            <span class="node-badge">{{ formData.nodes.length }} 节点 · {{ formData.edges.length }} 连线</span>
          </div>
          <div class="topbar-right">
            <button class="btn-test" @click="runTest" :disabled="isRunning || isTesting">
              <span v-if="isRunning || isTesting" class="run-dot-small"></span>
              {{ isRunning || isTesting ? '运行中...' : '▶ 试运行' }}
            </button>
            <button class="btn-save" @click="saveWorkflow()" :disabled="isSaving">保存</button>
          </div>
        </div>

        <!-- ======================== BODY ======================== -->
        <div class="body-area">
          <!-- ---- LEFT: Node Palette ---- -->
          <div class="palette">
            <div class="palette-header">节点类型</div>
            <div class="palette-list">
              <div v-for="nt in nodeTypeList" :key="nt.type" class="palette-item" @click="addNode(nt.type)">
                <div class="palette-dot" :style="{ background: nt.color, color: nt.color }"></div>
                <div class="palette-info">
                  <span class="palette-label">{{ nt.label }}</span>
                  <span class="palette-desc">{{ nt.desc }}</span>
                </div>
              </div>
            </div>
            <div class="palette-footer">
              <div class="palette-tip">
                <strong>提示</strong><br />
                点击节点类型添加到画布<br />
                拖拽节点端口创建连线
              </div>
            </div>
          </div>

          <!-- ---- CENTER: Canvas ---- -->
          <div class="canvas-wrap" ref="canvasWrap" @wheel.prevent="onCanvasWheel" @mousedown="onCanvasMouseDown">
            <div class="canvas-grid" :style="{ backgroundPosition: `${canvasPan.x}px ${canvasPan.y}px`, backgroundSize: (32 * canvasZoom) + 'px ' + (32 * canvasZoom) + 'px' }"></div>
            <div v-if="isRunning || isTesting" class="run-banner">
              <div class="run-dot"></div>
              运行中 · {{ selectedNode?.name || '工作流' }}
            </div>
            <!-- Pan/Zoom transform layer -->
            <div class="canvas-content" :style="{ transform: `translate(${canvasPan.x}px, ${canvasPan.y}px) scale(${canvasZoom})`, transformOrigin: '0 0' }">
              <!-- SVG Edges layer -->
              <svg class="edges-svg">
                <template v-for="edge in edgePaths" :key="edge.id">
                  <path :d="edge.path" class="edge-path" :class="{ active: isEdgeActive(edge) }" @click.stop="onEdgeClick(edge)" @contextmenu.prevent.stop="onEdgeContextMenu($event, edge)" @mousedown.stop />
                  <circle v-if="isEdgeActive(edge)" r="3" class="edge-flow">
                    <animateMotion dur="2s" repeatCount="indefinite" :path="edge.path" />
                  </circle>
                  <text v-if="edge.label" class="edge-label" :x="edge.labelX" :y="edge.labelY">{{ edge.label }}</text>
                </template>
              </svg>
              <!-- Drag connection line -->
              <svg v-if="connectingDrag" class="edges-svg drag-line-svg">
                <path :d="dragPath" class="edge-path active" style="stroke-dasharray: 6 4;" />
                <circle :cx="connectingDrag.toX" :cy="connectingDrag.toY" r="4" fill="#3b82f6" />
              </svg>

              <!-- Nodes -->
              <div v-for="node in formData.nodes" :key="node.id"
                class="wf-node"
                :class="{ selected: selectedNode?.id === node.id, 'connect-source': pendingEdgeSource === node.id }"
                :style="{ left: node.x + 'px', top: node.y + 'px', '--node-color': getNodeColor(node.type) }"
                @mousedown.stop="onNodeMouseDown($event, node)"
                @click.stop="onNodeClick(node)"
                @contextmenu.prevent.stop="onNodeContextMenu($event, node)">
                <div class="node-top-bar"></div>
                <div class="node-body">
                  <div class="node-header">
                    <div class="node-icon">{{ getNodeEmoji(node.type) }}</div>
                    <div class="node-title-row">
                      <span class="node-name">{{ node.name || getNodeTypeName(node.type) }}</span>
                      <span class="node-type-tag">{{ node.type }}</span>
                    </div>
                    <div class="node-status" :class="nodeStates[node.id] || ''"></div>
                  </div>
                  <div v-if="getNodeMeta(node)" class="node-meta">
                    <div class="node-meta-item">{{ getNodeMeta(node) }}</div>
                  </div>
                  <div v-if="node.type === 'condition' && node.branches" class="branch-badges">
                    <span v-for="(b, i) in node.branches" :key="i" class="branch-badge" :class="{ else: b.isElse }">
                      {{ b.isElse ? 'ELSE' : (b.rules && b.rules.length > 0 ? `条件${i+1}` : `分支${i+1}`) }}
                    </span>
                  </div>
                </div>
                <!-- Ports -->
                <div v-if="node.type !== 'start'" class="node-port in"
                  :class="{ 'port-target': connectingDrag && connectingDrag.from !== node.id, 'port-highlight': connectingDrag && connectingDrag.from !== node.id }"
                  @mousedown.stop="onInputPortMouseDown($event, node)"></div>
                <div v-if="node.type !== 'reply'" class="node-port out"
                  :class="{ 'port-source-active': connectingDrag && connectingDrag.from === node.id }"
                  @mousedown.stop="onOutputPortMouseDown($event, node)"></div>
              </div>
            </div>
            <div class="canvas-hint" :class="{ 'hint-error': hintError }">
              {{ hintError || (pendingEdgeSource ? '点击目标节点输入端口创建连线 · 点击空白取消' : '滚轮缩放 · 拖拽空白移动画布 · 拖拽端口创建连线') }}
            </div>
          </div>

          <!-- Context Menu -->
          <teleport to="body">
            <div v-if="contextMenu.show" class="context-menu" :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }" @click.stop>
              <div class="context-menu-item" @click="handleContextDelete">
                <span class="ctx-icon">🗑</span> 删除{{ contextMenu.type === 'node' ? '节点' : '连线' }}
                <span class="ctx-kbd">Del</span>
              </div>
              <div v-if="contextMenu.type === 'node'" class="context-menu-item" @click="handleContextDuplicate">
                <span class="ctx-icon">⎘</span> 复制节点
              </div>
            </div>
          </teleport>
          <div v-if="contextMenu.show" class="context-menu-backdrop" @click="closeContextMenu" @contextmenu.prevent="closeContextMenu"></div>

          <!-- ---- RIGHT: Inspector Panel ---- -->
          <div class="inspector">
            <!-- Node Config -->
            <template v-if="selectedNode">
              <div class="inspector-header">
                <span class="inspector-title">节点配置</span>
                <div class="inspector-header-actions">
                  <button class="inspector-delete" @click="deleteNode(selectedNode.id)" title="删除节点 (Del)">✕ 删除</button>
                  <button class="inspector-close" @click="selectedNode = null">×</button>
                </div>
              </div>
              <div class="inspector-body">
                <div class="type-badge" :style="{ background: getNodeColor(selectedNode.type) + '18', color: getNodeColor(selectedNode.type), borderColor: getNodeColor(selectedNode.type) + '30' }">
                  <span class="badge-icon">●</span>
                  {{ getNodeTypeName(selectedNode.type) }} 节点
                </div>

                <div class="insp-tabs">
                  <div class="insp-tab" :class="{ active: inspectorTab === 'config' }" @click="inspectorTab = 'config'">配置</div>
                  <div class="insp-tab" :class="{ active: inspectorTab === 'input' }" @click="inspectorTab = 'input'">输入映射</div>
                  <div class="insp-tab" :class="{ active: inspectorTab === 'output' }" @click="inspectorTab = 'output'">输出</div>
                </div>

                <!-- Tab: 配置 -->
                <template v-if="inspectorTab === 'config'">
                  <el-form :model="selectedNode" label-width="70px" size="small" class="config-form">
                    <el-form-item label="名称"><el-input v-model="selectedNode.name" placeholder="节点名称" /></el-form-item>

                    <!-- start -->
                    <template v-if="selectedNode.type === 'start'">
                      <div style="width:100%">
                        <div class="start-var-list">
                          <div v-for="(v, i) in startVariables" :key="i" class="start-var-row">
                            <el-input v-model="v.name" placeholder="变量名" size="small" style="width:100px" />
                            <el-select v-model="v.type" size="small" style="width:90px">
                              <el-option label="文本" value="text" />
                              <el-option label="段落" value="paragraph" />
                              <el-option label="数字" value="number" />
                            </el-select>
                            <el-input v-model="v.default" placeholder="默认值(可选)" size="small" style="flex:1" />
                            <el-button text size="small" @click="removeStartVar(i)" icon="Delete" />
                          </div>
                        </div>
                        <el-button size="small" @click="addStartVar" icon="Plus" style="margin-top:6px">添加变量</el-button>
                        <div class="var-hint-row" style="margin-top:6px">
                          <span class="var-hint-label">输出:</span>
                          <span class="var-chip" v-for="v in startVariables" :key="v.name">{{ selectedNode.name }}_{{ v.name }}</span>
                        </div>
                      </div>
                    </template>

                    <!-- agent -->
                    <template v-if="selectedNode.type === 'agent'">
                      <el-form-item label="智能体">
                        <el-select v-model="selectedNode.agent_id" placeholder="选择智能体" clearable filterable @change="loadAgentTools">
                          <el-option v-for="a in agents" :key="a.id" :label="a.name" :value="a.id" />
                        </el-select>
                        <div v-if="!agents.length" style="font-size:11px;color:var(--text-muted);margin-top:2px">请先在「智能体管理」创建智能体</div>
                      </el-form-item>
                      <el-form-item label="工具选择">
                        <el-select v-model="selectedNode.tools" multiple placeholder="可选, 留空用全部" style="width:100%">
                          <el-option v-for="t in agentTools" :key="t.name" :label="t.name" :value="t.name" />
                        </el-select>
                      </el-form-item>
                    </template>

                    <!-- llm -->
                    <template v-if="selectedNode.type === 'llm'">
                      <el-form-item label="模型">
                        <el-select v-model="selectedNode.model" placeholder="选择模型" clearable filterable>
                          <el-option v-for="m in modelsList" :key="m.name" :label="m.name" :value="m.name" />
                        </el-select>
                        <div v-if="!modelsList.length" style="font-size:11px;color:var(--text-muted);margin-top:2px">后端未配置模型</div>
                      </el-form-item>
                      <el-form-item label="系统提示词">
                        <el-select v-model="llmPromptPreset" placeholder="选择预设..." clearable style="width:100%;margin-bottom:4px" @change="onPromptPresetChange">
                          <el-option label="翻译" value="translate" />
                          <el-option label="代码生成" value="code" />
                          <el-option label="文本总结" value="summary" />
                          <el-option label="角色扮演" value="roleplay" />
                          <el-option label="自定义" value="custom" />
                        </el-select>
                        <el-input v-if="llmPromptPreset === 'custom' || !llmPromptPreset" v-model="selectedNode.system_prompt" type="textarea" :rows="3" placeholder="输入系统提示词..." />
                        <div v-else class="preset-prompt-display">{{ getPresetPrompt(llmPromptPreset) }}</div>
                      </el-form-item>
                      <el-form-item label="用户提示词">
                        <el-input v-model="selectedNode.user_prompt" type="textarea" :rows="3" placeholder="输入用户提示词，可用 {{变量名}} 引用上游变量" />
                        <div v-if="variablePool.length > 0" class="var-hint-row">
                          <span class="var-hint-label">可用变量:</span>
                          <span v-for="v in variablePool.slice(0, 4)" :key="v.value" class="var-chip" @click="insertVarToPrompt(v.value)">{{ v.value }}</span>
                        </div>
                      </el-form-item>
                      <el-form-item label="温度">
                        <el-slider v-model="selectedNode.temperature" :min="0" :max="2" :step="0.1" style="width:140px" />
                        <span style="margin-left:8px;font-size:12px;color:var(--text-muted)">{{ selectedNode.temperature ?? 0.7 }}</span>
                      </el-form-item>
                      <el-form-item label="最大Token">
                        <el-input-number v-model="selectedNode.max_tokens" :min="1" :max="8192" :step="256" style="width:140px" />
                      </el-form-item>
                    </template>

                    <!-- condition -->
                    <template v-if="selectedNode.type === 'condition'">
                      <div style="width:100%">
                        <div v-for="(branch, bIdx) in (selectedNode?.branches || [])" :key="branch.id"
                          class="branch-card" :class="{ 'branch-else': branch.isElse }">
                          <div class="branch-header">
                            <span class="branch-tag" :style="{ background: branch.isElse ? '#f1f5f910' : '#3b82f620', color: branch.isElse ? 'var(--text-muted)' : 'var(--accent)' }">
                              {{ branch.isElse ? 'ELSE' : `条件 ${bIdx + 1}` }}
                            </span>
                            <el-button v-if="!branch.isElse && (selectedNode?.branches || []).length > 1" text size="small" @click="removeBranch(bIdx)" icon="Delete" />
                          </div>
                          <div v-for="(rule, rIdx) in (branch.rules || [])" :key="rule.id" class="rule-row">
                            <el-select v-model="rule._var" placeholder="变量" size="small" style="width:70px" @change="syncRuleValue(rule)">
                              <el-option v-for="v in variablePool" :key="v.value" :label="v.label" :value="v.value" />
                            </el-select>
                            <el-select v-model="rule._op" placeholder="运算符" size="small" style="width:90px" @change="syncRuleValue(rule)">
                              <el-option label="等于" value="eq" />
                              <el-option label="不等于" value="ne" />
                              <el-option label="包含" value="in" />
                              <el-option label="不包含" value="not_in" />
                              <el-option label="大于" value="gt" />
                              <el-option label="小于" value="lt" />
                              <el-option label=">=" value="gte" />
                              <el-option label="<=" value="lte" />
                              <el-option label="开头" value="startswith" />
                              <el-option label="结尾" value="endswith" />
                              <el-option label="为空" value="empty" />
                              <el-option label="不为空" value="not_empty" />
                            </el-select>
                            <el-input v-if="!['empty','not_empty'].includes(rule._op)" v-model="rule._val" placeholder="值" size="small" style="flex:1;min-width:50px" @input="syncRuleValue(rule)" />
                            <el-button v-if="rIdx < (branch.rules || []).length - 1" text size="small" @click="removeRule(branch, rIdx)" icon="Delete" />
                            <el-tag v-if="rIdx < (branch.rules || []).length - 1"
                              :type="rule.logic === 'or' ? 'warning' : 'info'"
                              size="small" style="cursor:pointer;margin-left:2px;flex-shrink:0"
                              @click="toggleRuleLogic(rule)">
                              {{ rule.logic === 'or' ? 'OR' : 'AND' }}
                            </el-tag>
                          </div>
                          <div v-if="!branch.isElse" style="margin-top:4px">
                            <el-button size="small" text @click="addRule(branch)" icon="Plus">规则</el-button>
                          </div>
                          <div class="branch-target" style="margin-top:6px">
                            <span style="font-size:11px;color:var(--text-muted);margin-right:4px">→</span>
                            <el-select v-model="branch.target" placeholder="目标节点" size="small" style="width:150px" @change="onBranchTargetChange(branch)">
                              <el-option v-for="n in allUpstreamNodes" :key="n.id" :label="n.name || getNodeTypeName(n.type)" :value="n.id" />
                            </el-select>
                          </div>
                        </div>
                        <el-button size="small" @click="addIfBranch" icon="Plus" style="margin-top:8px">添加 elif 分支</el-button>
                      </div>
                    </template>

                    <!-- human_intervention -->
                    <template v-if="selectedNode.type === 'human_intervention'">
                      <el-form-item label="标题">
                        <el-input v-model="selectedNode.config.title" placeholder="请选择处理方式" />
                      </el-form-item>
                      <el-form-item label="超时(秒)">
                        <el-input-number v-model="selectedNode.config.timeout" :min="30" :max="3600" :step="30" />
                      </el-form-item>
                      <el-form-item label="默认分支">
                        <el-select v-model="selectedNode.config.default_branch" placeholder="超时后走...">
                          <el-option v-for="b in branchList" :key="b.id" :label="b.label || b.id" :value="b.id" />
                        </el-select>
                      </el-form-item>
                      <el-form-item label="分支列表">
                        <div style="width:100%">
                          <div v-for="(branch, idx) in branchList" :key="branch.id" class="branch-row" style="flex-wrap:wrap;gap:4px">
                            <el-input v-model="branch.label" placeholder="分支名(同意/拒绝)" size="small" style="width:100px" />
                            <el-input v-model="branch.desc" placeholder="描述" size="small" style="flex:1;min-width:80px" />
                            <el-button text size="small" @click="removeBranch(idx)" icon="Delete" />
                            <div class="branch-target" style="width:100%;margin-top:2px">
                              <span style="font-size:11px;color:var(--text-muted);margin-right:4px">→</span>
                              <el-select v-model="branch.target" placeholder="目标节点" size="small" style="width:160px" @change="onHumanBranchTargetChange(branch)">
                                <el-option v-for="n in allUpstreamNodes" :key="n.id" :label="n.name || getNodeTypeName(n.type)" :value="n.id" />
                              </el-select>
                            </div>
                          </div>
                          <el-button size="small" @click="addBranch" icon="Plus" style="margin-top:4px">添加分支</el-button>
                        </div>
                      </el-form-item>
                    </template>

                    <!-- reply -->
                    <template v-if="selectedNode.type === 'reply'">
                      <el-form-item label="回复内容">
                        <el-input v-model="selectedNode.inputs.message" type="textarea" :rows="4" placeholder="输入回复内容，可用 {{变量名}} 引用上游变量" />
                        <div v-if="variablePool.length > 0" class="var-hint-row">
                          <span class="var-hint-label">可用变量:</span>
                          <span v-for="v in variablePool.slice(0, 4)" :key="v.value" class="var-chip" @click="insertVarToReply(v.value)">{{ v.value }}</span>
                        </div>
                      </el-form-item>
                      <el-form-item label="模式">
                        <el-radio-group v-model="selectedNode.reply_mode" size="small">
                          <el-radio-button label="template">模板文本</el-radio-button>
                          <el-radio-button label="variable">直接引用变量</el-radio-button>
                        </el-radio-group>
                      </el-form-item>
                    </template>

                    <!-- parallel -->
                    <template v-if="selectedNode.type === 'parallel'">
                      <el-form-item label="分支数">
                        <el-input-number v-model="branchCount" :min="2" :max="10" @change="onBranchCountChange" />
                      </el-form-item>
                      <div v-for="(b, i) in branchList2" :key="b.id" style="margin-bottom:4px;font-size:12px;color:var(--text-muted)">
                        分支 {{ i + 1 }}: {{ b.label }}
                      </div>
                    </template>

                    <!-- join -->
                    <template v-if="selectedNode.type === 'join'">
                      <el-form-item label="说明">
                        <el-input v-model="selectedNode.description" type="textarea" :rows="2" placeholder="汇聚并行分支输出" disabled />
                      </el-form-item>
                    </template>

                    <!-- 错误重试 -->
                    <template v-if="!['start','reply','join'].includes(selectedNode.type)">
                      <div class="collapse" :class="{ open: retryOpen }">
                        <div class="collapse-header" @click="retryOpen = !retryOpen">
                          <span>错误重试</span>
                          <span class="collapse-arrow">▶</span>
                        </div>
                        <div class="collapse-body">
                          <el-form-item label="最大重试">
                            <el-input-number v-model="selectedNode.max_retries" :min="0" :max="5" :step="1" style="width:100px" />
                          </el-form-item>
                          <el-form-item label="间隔(秒)">
                            <el-input-number v-model="selectedNode.retry_interval" :min="1" :max="60" :step="1" style="width:100px" />
                          </el-form-item>
                        </div>
                      </div>
                    </template>

                    <el-form-item label="描述"><el-input v-model="selectedNode.description" type="textarea" :rows="2" placeholder="节点描述" /></el-form-item>
                  </el-form>
                </template>

                <!-- Tab: 输入映射 -->
                <template v-if="inspectorTab === 'input'">
                  <div class="form-group">
                    <label class="form-label">输入映射 <span class="label-hint">变量引用</span></label>
                    <div v-if="variablePool.length > 0" style="display:flex;flex-direction:column;gap:6px;">
                      <div v-for="v in variablePool.slice(0, 5)" :key="v.value" style="display:flex;align-items:center;gap:6px;padding:6px 10px;background:var(--bg-elevated);border:1px solid var(--border-subtle);border-radius:var(--radius-sm);">
                        <span style="font-size:11px;color:var(--text-muted);font-family:var(--font-mono);">prompt</span>
                        <span style="color:var(--text-muted);">→</span>
                        <span class="var-ref"><span class="var-slash">/</span>{{ v.value.slice(1) }}</span>
                      </div>
                    </div>
                    <div v-else class="config-empty-inner">
                      <p style="font-size:12px;color:var(--text-muted);padding:8px 0;">暂无可用变量</p>
                    </div>
                  </div>
                </template>

                <!-- Tab: 输出 -->
                <template v-if="inspectorTab === 'output'">
                  <div class="form-group">
                    <label class="form-label">输出变量</label>
                    <div class="output-preview">
                      <span style="font-size:11px;color:var(--text-muted);">→</span>
                      <span class="output-var">{{ selectedNode.name || getNodeTypeName(selectedNode.type) }}_output</span>
                    </div>
                  </div>
                </template>
              </div>
            </template>

            <!-- Edge Config -->
            <template v-else-if="selectedEdge">
              <div class="inspector-header">
                <span class="inspector-title">连线配置</span>
                <div class="inspector-header-actions">
                  <button class="inspector-delete" @click="deleteEdge(selectedEdge.id)" title="删除连线 (Del)">× 删除</button>
                  <button class="inspector-close" @click="selectedEdge = null">×</button>
                </div>
              </div>
              <div class="inspector-body">
                <div class="form-group">
                  <label class="form-label">来源</label>
                  <div style="padding:6px 10px;background:var(--bg-elevated);border:1px solid var(--border-subtle);border-radius:var(--radius-sm);font-size:13px;color:var(--text-primary);"> {{ getNodeName(selectedEdge.from) }} </div>
                </div>
                <div class="form-group">
                  <label class="form-label">目标</label>
                  <div style="padding:6px 10px;background:var(--bg-elevated);border:1px solid var(--border-subtle);border-radius:var(--radius-sm);font-size:13px;color:var(--text-primary);"> {{ getNodeName(selectedEdge.to) }} </div>
                </div>
              </div>
            </template>

            <!-- Empty State -->
            <template v-else>
              <div class="inspector-header">
                <span class="inspector-title">节点配置</span>
              </div>
              <div class="inspector-body">
                <div class="config-empty">
                  <p>点击画布上的节点进行配置</p>
                  <p class="config-hint">或从左侧面板添加新节点</p>
                </div>

                <!-- Test Area (when no node selected) -->
                <div class="test-area">
                  <div class="test-header">
                    <span>工作流测试</span>
                  </div>
                  <div class="test-messages" ref="testMessagesRef" v-if="messages.length > 0">
                    <div v-for="(msg, i) in messages" :key="i" class="test-msg" :class="'msg-' + msg.role">
                      <div class="msg-label">
                        <template v-if="msg.role === 'user'">用户</template>
                        <template v-else-if="msg.role === 'assistant'">最终回复</template>
                        <template v-else-if="msg.role === 'node'">{{ msg.nodeId }}</template>
                        <template v-else-if="msg.role === 'system'">系统</template>
                        <template v-else-if="msg.role === 'error'">错误</template>
                      </div>
                      <div class="msg-content">{{ msg.content }}</div>
                    </div>
                    <div v-if="interventionData" class="intervention-card">
                      <h4>{{ interventionData.title || '请选择处理方式' }}</h4>
                      <div class="branch-buttons">
                        <el-button v-for="b in interventionData.branches" :key="b.id"
                          @click="selectBranch(b.id)" type="primary" size="small">
                          {{ b.label }}<br><small>{{ b.desc }}</small>
                        </el-button>
                      </div>
                      <div v-if="countdown > 0" class="countdown">⏱️ {{ countdown }}s 后自动选择默认...</div>
                    </div>
                  </div>
                  <div class="test-input-row">
                    <input v-model="testInput" class="form-input" placeholder="输入测试消息..." :disabled="isRunning" @keyup.enter="runTest" />
                    <button class="btn-test" style="flex-shrink:0;padding:6px 12px;font-size:12px;" @click="runTest" :disabled="isRunning">发送</button>
                  </div>
                </div>
              </div>
            </template>
          </div>
        </div>

        <!-- ======================== BOTTOM CONSOLE ======================== -->
        <div class="console">
          <div class="console-header">
            <div class="console-tabs">
              <div class="console-tab" :class="{ active: consoleTab === 'log' }" @click="consoleTab = 'log'">
                执行日志 <span class="tab-count">{{ logEntries.length }}</span>
              </div>
              <div class="console-tab" :class="{ active: consoleTab === 'vars' }" @click="consoleTab = 'vars'">
                变量上下文 <span class="tab-count">{{ Object.keys(variableContext).length }}</span>
              </div>
              <div class="console-tab" :class="{ active: consoleTab === 'output' }" @click="consoleTab = 'output'">
                节点输出 <span class="tab-count">{{ nodeOutputs.length }}</span>
              </div>
            </div>
            <div class="console-actions">
              <button class="console-action" @click="logEntries = []; nodeOutputs = []">清空</button>
            </div>
          </div>
          <div class="console-body" v-if="consoleTab === 'log'">
            <div v-if="logEntries.length === 0" class="log-empty">暂无执行日志，点击「试运行」开始测试</div>
            <div v-for="(entry, i) in logEntries" :key="i" class="log-line">
              <span class="log-time">{{ new Date().toLocaleTimeString() }}</span>
              <span class="log-tag" :class="entry.status === 'running' ? 'node_start' : entry.status === 'done' ? 'node_end' : 'log_update'">{{ entry.status === 'running' ? 'node_start' : entry.status === 'done' ? 'node_end' : entry.status }}</span>
              <span class="log-text">
                <span class="log-node">{{ entry.nodeName }}</span>
                <template v-if="entry.output"> → {{ entry.output }}</template>
                <template v-if="entry.duration"> · {{ entry.duration }}ms</template>
              </span>
            </div>
            <template v-for="(msg, i) in messages" :key="'msg_' + i">
              <div v-if="msg && (msg.role === 'assistant' || msg.role === 'error')" class="log-line">
                <span class="log-time">{{ new Date().toLocaleTimeString() }}</span>
                <span class="log-tag" :class="msg.role === 'error' ? 'error' : 'final'">{{ msg.role === 'error' ? 'error' : 'final' }}</span>
                <span class="log-text">{{ msg.content }}</span>
              </div>
            </template>
          </div>
          <div class="console-body" v-else-if="consoleTab === 'vars'">
            <div v-if="Object.keys(variableContext).length === 0" class="log-empty">暂无变量上下文</div>
            <div v-for="(val, key) in variableContext" :key="key" class="log-line">
              <span class="log-text"><span class="log-var">{{ key }}</span> = <span class="log-val">{{ typeof val === 'object' ? JSON.stringify(val) : val }}</span></span>
            </div>
          </div>
          <div class="console-body" v-else>
            <div v-if="nodeOutputs.length === 0" class="log-empty">暂无节点输出，运行工作流后查看</div>
            <div v-for="(o, i) in nodeOutputs" :key="i" class="log-line">
              <span class="log-time">{{ o.time }}</span>
              <span class="log-text"><span class="log-node">{{ o.nodeName }}</span> → <span class="log-var">{{ o.varKey }}</span> = <span class="log-val">{{ o.output }}</span></span>
            </div>
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
      <div v-else class="detail-view">
        <!-- Left: Workflow Graph (DOM + SVG, same style as editor) -->
        <div class="detail-canvas-wrap">
          <div class="detail-canvas-toolbar">
            <span class="node-badge">{{ workflowDetail.nodes?.length || 0 }} 节点 · {{ workflowDetail.edges?.length || 0 }} 连线</span>
          </div>
          <div class="detail-canvas-grid" ref="detailCanvasGrid">
            <div class="detail-canvas-inner" :style="{ width: detailBounds.w + 'px', height: detailBounds.h + 'px', transform: 'scale(' + detailScale + ')' }">
            <svg class="detail-edges-svg" :viewBox="detailSvgViewBox" preserveAspectRatio="none"
              :style="{ width: detailBounds.w + 'px', height: detailBounds.h + 'px' }">
              <defs>
                <marker id="detail-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="rgba(255,255,255,0.30)" />
                </marker>
              </defs>
              <template v-for="edge in detailEdgePaths" :key="edge.id">
                <path :d="edge.path" class="detail-edge-path" />
              </template>
            </svg>
            <div class="detail-nodes-layer" :style="{ width: detailBounds.w + 'px', height: detailBounds.h + 'px' }">
              <div v-for="node in workflowDetail.nodes" :key="node.id"
                class="wf-node detail-node"
                :style="{ left: (node.x - detailBounds.minX) + 'px', top: (node.y - detailBounds.minY) + 'px', '--node-color': getNodeColor(node.type) }">
              <div class="node-top-bar"></div>
              <div class="node-body">
                <div class="node-header">
                  <div class="node-icon">{{ getNodeEmoji(node.type) }}</div>
                  <div class="node-title-row">
                    <span class="node-name">{{ node.name || getNodeTypeName(node.type) }}</span>
                    <span class="node-type-tag">{{ node.type }}</span>
                  </div>
                </div>
                <div v-if="getNodeMeta(node)" class="node-meta">
                  <div class="node-meta-item">{{ getNodeMeta(node) }}</div>
                </div>
                <div v-if="node.type === 'condition' && node.branches" class="branch-badges">
                  <span v-for="(b, i) in node.branches" :key="i" class="branch-badge" :class="{ else: b.isElse }">
                    {{ b.isElse ? 'ELSE' : (b.rules && b.rules.length > 0 ? `条件${i+1}` : `分支${i+1}`) }}
                  </span>
                </div>
              </div>
            </div>
            </div>
            </div>
            <div v-if="!workflowDetail.nodes?.length" class="detail-empty-canvas">
              <span>暂无节点，点击「编辑」添加</span>
            </div>
          </div>
        </div>

        <!-- Right: Detail Info Panel -->
        <div class="detail-side-panel">
          <div class="detail-side-section">
            <h3>工作流信息</h3>
            <div class="info-row"><span class="label">关联智能体</span><span class="value">{{ getAgentName(workflowDetail.agent_id) || '未关联' }}</span></div>
            <div class="info-row"><span class="label">节点数量</span><span class="value">{{ workflowDetail.nodes?.length || 0 }} 个</span></div>
            <div class="info-row"><span class="label">连接数量</span><span class="value">{{ workflowDetail.edges?.length || 0 }} 条</span></div>
          </div>

          <div class="detail-side-section">
            <h3>节点列表</h3>
            <div v-if="workflowDetail.nodes?.length > 0" class="node-list">
              <div v-for="(node, index) in workflowDetail.nodes" :key="index" class="node-item"
                :style="{ '--node-color': getNodeColor(node.type) }">
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
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Plus, Connection, Check, Cpu, Setting, Link, VideoPlay, Delete, ArrowLeft, ZoomOut, ZoomIn, Select, Close, MoreFilled, ChatDotRound, Promotion, UserFilled } from '@element-plus/icons-vue'
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

const canvasWrap = ref(null)
const previewContainer = ref(null)
const testMessagesRef = ref(null)
const detailCanvasGrid = ref(null)
const detailCanvasSize = ref({ w: 800, h: 400 })
const selectedNode = ref(null)
const selectedEdge = ref(null)
const contextMenu = ref({ show: false, x: 0, y: 0, type: '' })
const nodeStates = ref({})
const activeEdges = ref(new Set())
const executedNodeIds = ref(new Set())
const messages = ref([])
const testInput = ref('')
const isRunning = ref(false)
let previewNetwork = null
const pendingEdgeSource = ref(null)

// Custom canvas state (replaces vis-network)
const canvasPan = ref({ x: 0, y: 0 })
const canvasZoom = ref(1)
const dragNode = ref(null)       // { id, startMouseX, startMouseY, startNodeX, startNodeY }
const connectingDrag = ref(null) // { from, fromX, fromY, toX, toY }
const panning = ref(null)        // { startMouseX, startMouseY, startPanX, startPanY }
const hintError = ref('')
const NODE_WIDTH = 200

// Log entries for debug log tree
const logEntries = ref([])
const consoleTab = ref('log')
const isTesting = ref(false)
const variableContext = ref({})
const nodeOutputs = ref([])

// New refs for human_intervention
const pausedNodeId = ref(null)
const interventionData = ref(null)
const countdown = ref(0)
const agentTools = ref([])
const modelsList = ref([])
const llmPromptPreset = ref('')
let countdownTimer = null

const inspectorTab = ref('config')
const retryOpen = ref(false)

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
  { type: 'start',   label: '开始',     desc: '用户输入 → 变量',   color: '#8b5cf6' },
  { type: 'agent',   label: '智能体',   desc: 'Agent + 工具',       color: '#3b82f6' },
  { type: 'llm',     label: 'LLM',     desc: '大模型调用',         color: '#06b6d4' },
  { type: 'condition', label: '条件',   desc: 'if/elif/else',       color: '#f59e0b' },
  { type: 'parallel', label: '并行',   desc: '分支并行执行',       color: '#14b8a6' },
  { type: 'join',    label: '汇聚',     desc: '合并并行分支',       color: '#8b5cf6' },
  { type: 'human_intervention', label: '人为介入', desc: '人工选择分支', color: '#ec4899' },
  { type: 'reply',   label: '回复/结束', desc: '输出最终回答',      color: '#10b981' },
]
const nodeTypes = Object.fromEntries(nodeTypeList.map(n => [n.type, n]))

function getNodeTypeName(type) { return nodeTypes[type]?.label || '未知' }
function getNodeColor(type)    { return nodeTypes[type]?.color || '#64748b' }
function getNodeIcon(type) {
  const map = { start: 'VideoPlay', agent: 'Cpu', llm: 'ChatDotRound', condition: 'Link', parallel: 'Connection', join: 'Connection', human_intervention: 'UserFilled', reply: 'Check' }
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

// ---- Computed for config panels ----
const conditionsList = computed(() => selectedNode.value?.branches || [])
const branchList = computed(() => selectedNode.value?.config?.branches || [])
const upstreamNodes = computed(() => {
  if (!selectedNode.value) return []
  const result = []
  for (const edge of formData.value.edges) {
    if (edge.to === selectedNode.value.id) {
      const node = formData.value.nodes.find(n => n.id === edge.from)
      if (node) result.push(node)
    }
  }
  return result
})

const allUpstreamNodes = computed(() => {
  // 所有非当前节点的节点
  if (!selectedNode.value) return []
  return formData.value.nodes.filter(n => n.id !== selectedNode.value.id)
})

const variablePool = computed(() => {
  const pool = []
  const seenVars = new Set()
  for (const node of formData.value.nodes) {
    const nodeName = node.name || getNodeTypeName(node.type) || node.id
    if (node.type === 'start') {
      let varArr = []
      if (Array.isArray(node.variables)) {
        varArr = node.variables.map(v => v.name).filter(Boolean)
      } else if (typeof node.variables === 'string') {
        varArr = node.variables.split(',').map(v => v.trim()).filter(Boolean)
      }
      for (const v of varArr) {
        const key = `/${nodeName}_${v}`
        pool.push({ label: key, value: key })
        seenVars.add(key)
      }
    } else {
      const key = `/${nodeName}_output`
      pool.push({ label: key, value: key })
      seenVars.add(key)
    }
  }
  // 排除当前节点自身
  if (selectedNode.value) {
    const selfName = selectedNode.value.name || getNodeTypeName(selectedNode.value.type) || selectedNode.value.id
    if (selectedNode.value.type === 'start') {
      return pool.filter(p => !p.value.startsWith(`/${selfName}_`))
    } else {
      return pool.filter(p => p.value !== `/${selfName}_output`)
    }
  }
  return pool
})

// ---- Node rendering helpers ----
function getNodeEmoji(type) {
  const map = { start: '▶', agent: '🤖', llm: '💬', condition: '⑂', parallel: '☰', join: '⬛', human_intervention: '👤', reply: '✓' }
  return map[type] || '●'
}

function getNodeMeta(node) {
  switch (node.type) {
    case 'start': {
      const vars = Array.isArray(node.variables) ? node.variables.map(v => v.name).filter(Boolean) : (typeof node.variables === 'string' ? node.variables : '')
      return `变量: ${vars || 'input'}`
    }
    case 'agent': {
      const agentName = getAgentName(node.agent_id) || '未绑定'
      const toolCount = node.tools?.length || 0
      return `${agentName} · ${toolCount > 0 ? toolCount + ' 工具' : '全部工具'}`
    }
    case 'llm':
      return `${node.model || '默认模型'} · temp ${node.temperature ?? 0.7}`
    case 'condition':
      return null  // branch badges are shown separately
    case 'parallel':
      return `${(node.branches || []).length} 分支并行`
    case 'human_intervention':
      return `超时 ${(node.config?.timeout || 300)}s · ${(node.config?.branches || []).length} 分支`
    case 'join':
      return '合并并行分支'
    case 'reply':
      return null
    default:
      return node.description || ''
  }
}

function getNodeHeight(node) {
  let h = 72
  if (node.type === 'condition' && node.branches) {
    h += 24
  }
  return h
}

// ---- Edge path computation ----
const edgePaths = computed(() => {
  return formData.value.edges.map(edge => {
    const fromNode = formData.value.nodes.find(n => n.id === edge.from)
    const toNode = formData.value.nodes.find(n => n.id === edge.to)
    if (!fromNode || !toNode) return null
    const x1 = fromNode.x + NODE_WIDTH
    const y1 = fromNode.y + getNodeHeight(fromNode) / 2
    const x2 = toNode.x
    const y2 = toNode.y + getNodeHeight(toNode) / 2
    const dx = Math.max(50, Math.abs(x2 - x1) * 0.4)
    const path = `M ${x1},${y1} C ${x1 + dx},${y1} ${x2 - dx},${y2} ${x2},${y2}`
    // Edge label
    let label = ''
    if (fromNode.type === 'condition' && fromNode.branches) {
      for (const b of fromNode.branches) {
        if (b.target === edge.to) {
          label = b.isElse ? 'ELSE' : (b.rules && b.rules.length > 0 ? `条件 ${fromNode.branches.indexOf(b) + 1}` : '')
          break
        }
      }
    }
    const midX = (x1 + x2) / 2
    const midY = (y1 + y2) / 2 - 8
    return { id: edge.id, path, label, labelX: midX, labelY: midY, from: edge.from, to: edge.to }
  }).filter(Boolean)
})

const dragPath = computed(() => {
  if (!connectingDrag.value) return ''
  const { fromX, fromY, toX, toY } = connectingDrag.value
  const dx = Math.max(50, Math.abs(toX - fromX) * 0.4)
  return `M ${fromX},${fromY} C ${fromX + dx},${fromY} ${toX - dx},${toY} ${toX},${toY}`
})

// ---- Detail view: DOM edges + SVG viewBox + transform ----
const detailBounds = computed(() => {
  if (!workflowDetail.value?.nodes?.length) return { minX: 0, minY: 0, maxX: 800, maxY: 400, w: 800, h: 400 }
  const nodes = workflowDetail.value.nodes
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity
  for (const n of nodes) {
    const nx = n.x || 0
    const ny = n.y || 0
    minX = Math.min(minX, nx)
    minY = Math.min(minY, ny)
    maxX = Math.max(maxX, nx + NODE_WIDTH)
    maxY = Math.max(maxY, ny + getNodeHeight(n))
  }
  const pad = 60
  minX -= pad; minY -= pad; maxX += pad; maxY += pad
  return { minX, minY, maxX, maxY, w: maxX - minX, h: maxY - minY }
})

const detailEdgePaths = computed(() => {
  if (!workflowDetail.value?.nodes || !workflowDetail.value?.edges) return []
  const b = detailBounds.value
  const ox = -b.minX, oy = -b.minY
  return workflowDetail.value.edges.map(edge => {
    const fromNode = workflowDetail.value.nodes.find(n => n.id === edge.from)
    const toNode = workflowDetail.value.nodes.find(n => n.id === edge.to)
    if (!fromNode || !toNode) return null
    const x1 = fromNode.x + NODE_WIDTH + ox
    const y1 = fromNode.y + getNodeHeight(fromNode) / 2 + oy
    const x2 = toNode.x + ox
    const y2 = toNode.y + getNodeHeight(toNode) / 2 + oy
    const dx = Math.max(50, Math.abs(x2 - x1) * 0.4)
    const path = `M ${x1},${y1} C ${x1 + dx},${y1} ${x2 - dx},${y2} ${x2},${y2}`
    return { id: edge.id, path }
  }).filter(Boolean)
})

const detailSvgViewBox = computed(() => {
  const b = detailBounds.value
  return `0 0 ${b.w} ${b.h}`
})

const detailScale = computed(() => {
  const b = detailBounds.value
  const sz = detailCanvasSize.value
  if (!b.w || !b.h) return 1
  const scaleX = (sz.w - 20) / b.w
  const scaleY = (sz.h - 20) / b.h
  return Math.min(1, Math.min(scaleX, scaleY))
})

// Observe canvas container size
let ro = null
onMounted(() => {
  if (typeof ResizeObserver !== 'undefined') {
    ro = new ResizeObserver(entries => {
      for (const e of entries) {
        detailCanvasSize.value = { w: e.contentRect.width, h: e.contentRect.height }
      }
    })
    if (detailCanvasGrid.value) ro.observe(detailCanvasGrid.value)
  }
})

watch(detailCanvasGrid, (el) => {
  if (ro && el) ro.observe(el)
  else if (ro && !el) ro.disconnect()
})

function isEdgeActive(edge) {
  return activeEdges.value.has(edge.id)
}

function onEdgeClick(edge) {
  const edgeData = formData.value.edges.find(e => e.id === edge.id)
  if (edgeData) {
    selectedNode.value = null
    selectedEdge.value = { ...edgeData }
  }
}

// ---- Parallel helpers ----
const branchList2 = computed(() => selectedNode.value?.branches || [])
const branchCount = computed({
  get: () => (selectedNode.value?.branches || []).length,
  set: (val) => { /* handled by onBranchCountChange */ }
})

function onBranchCountChange(newCount) {
  if (!selectedNode.value) return
  if (selectedNode.value.type !== 'parallel') return
  const current = selectedNode.value.branches || []
  if (newCount > current.length) {
    for (let i = current.length; i < newCount; i++) {
      current.push({ id: `branch_${i}`, label: `分支${current.length + 1}` })
    }
  } else if (newCount < current.length) {
    current.splice(newCount)
  }
  selectedNode.value = { ...selectedNode.value, branches: [...current] }
}

// ---- Editor ----
function openNewEditor() {
  isEdit.value = false
  formData.value = { id: null, name: '', description: '', agent_id: null, nodes: [], edges: [] }
  selectedNode.value = null
  selectedEdge.value = null
  messages.value = []
  nodeStates.value = {}
  activeEdges.value = new Set()
  executedNodeIds.value = new Set()
  logEntries.value = []
  nodeOutputs.value = []
  interventionData.value = null
  pausedNodeId.value = null
  countdown.value = 0
  agentTools.value = []
  dragNode.value = null
  connectingDrag.value = null
  panning.value = null
  showEditor.value = true
}

function closeEditor() {
  showEditor.value = false
  isEdit.value = false
  selectedNode.value = null
  selectedEdge.value = null
  messages.value = []
  nodeStates.value = {}
  activeEdges.value = new Set()
  executedNodeIds.value = new Set()
  logEntries.value = []
  nodeOutputs.value = []
  interventionData.value = null
  pausedNodeId.value = null
  countdown.value = 0
  agentTools.value = []
  dragNode.value = null
  connectingDrag.value = null
  panning.value = null
  // Remove global mouse listeners
  document.removeEventListener('mousemove', onGlobalMouseMove)
  document.removeEventListener('mouseup', onGlobalMouseUp)
  if (countdownTimer) { clearInterval(countdownTimer); countdownTimer = null }
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
  selectedEdge.value = null
  messages.value = []
  nodeStates.value = {}
  activeEdges.value = new Set()
  executedNodeIds.value = new Set()
  logEntries.value = []
  nodeOutputs.value = []
  dragNode.value = null
  connectingDrag.value = null
  panning.value = null
  interventionData.value = null
  pausedNodeId.value = null
  countdown.value = 0
  agentTools.value = []
  loadModels()
  showEditor.value = true
}

// ---- Custom canvas: pan, zoom, node drag, port connect ----

function onCanvasWheel(e) {
  if (!canvasWrap.value) return
  const rect = canvasWrap.value.getBoundingClientRect()
  const mouseX = e.clientX - rect.left
  const mouseY = e.clientY - rect.top
  const delta = e.deltaY > 0 ? 0.9 : 1.1
  const newZoom = Math.min(2, Math.max(0.2, canvasZoom.value * delta))
  // Zoom around mouse position
  const scaleRatio = newZoom / canvasZoom.value
  canvasPan.value = {
    x: mouseX - (mouseX - canvasPan.value.x) * scaleRatio,
    y: mouseY - (mouseY - canvasPan.value.y) * scaleRatio
  }
  canvasZoom.value = newZoom
}

function onCanvasMouseDown(e) {
  // Start panning (click on blank canvas)
  panning.value = {
    startMouseX: e.clientX,
    startMouseY: e.clientY,
    startPanX: canvasPan.value.x,
    startPanY: canvasPan.value.y
  }
  // Cancel connect mode
  pendingEdgeSource.value = null
  selectedNode.value = null
  selectedEdge.value = null
  hintError.value = ''
}

// Node dragging
function onNodeMouseDown(e, node) {
  // Left button only, and not clicking on a port
  if (e.button !== 0) return
  dragNode.value = {
    id: node.id,
    startMouseX: e.clientX,
    startMouseY: e.clientY,
    startNodeX: node.x,
    startNodeY: node.y
  }
  // Select node immediately
  selectedEdge.value = null
  const nd = formData.value.nodes.find(n => n.id === node.id)
  if (nd) {
    selectedNode.value = JSON.parse(JSON.stringify(nd))
    if (selectedNode.value.type === 'condition') {
      // Ensure branches exist (safeguard for older saved data)
      if (!selectedNode.value.branches || !Array.isArray(selectedNode.value.branches)) {
        selectedNode.value.branches = [
          { id: 'branch_' + Date.now(), rules: [{ id: 'rule_' + Date.now(), value: '', _var: '', _op: '', _val: '', logic: 'and' }], target: '', isElse: false },
          { id: 'branch_else_' + Date.now(), rules: [], target: '', isElse: true }
        ]
      }
      // Ensure each rule has logic field and parse value → structured fields
      selectedNode.value.branches.forEach(b => {
        if (b.rules) b.rules.forEach(r => {
          if (!r.logic) r.logic = 'and'
          parseRuleValue(r)
        })
      })
    }
    if (nd.type === 'agent' && nd.agent_id) loadAgentToolsById(nd.agent_id)
    if (nd.type === 'llm') detectPromptPreset(nd.system_prompt)
  }
}

// Output port: start drag-to-connect
function onOutputPortMouseDown(e, node) {
  if (e.button !== 0) return
  e.stopPropagation()
  const x = node.x + NODE_WIDTH
  const y = node.y + getNodeHeight(node) / 2
  connectingDrag.value = { from: node.id, fromX: x, fromY: y, toX: x, toY: y }
  selectedNode.value = null
  selectedEdge.value = null
}

// Input port: if in connect mode, create edge
function onInputPortMouseDown(e, node) {
  if (e.button !== 0) return
  e.stopPropagation()
  // If a drag is in progress, this will be handled by mouseup on document
}

// Global mousemove handler (attached in onMounted)
function onGlobalMouseMove(e) {
  if (!canvasWrap.value) return
  const rect = canvasWrap.value.getBoundingClientRect()
  const mouseX = e.clientX - rect.left
  const mouseY = e.clientY - rect.top

  // Node dragging
  if (dragNode.value) {
    const dx = (e.clientX - dragNode.value.startMouseX) / canvasZoom.value
    const dy = (e.clientY - dragNode.value.startMouseY) / canvasZoom.value
    const node = formData.value.nodes.find(n => n.id === dragNode.value.id)
    if (node) {
      node.x = dragNode.value.startNodeX + dx
      node.y = dragNode.value.startNodeY + dy
    }
    return
  }

  // Connecting drag
  if (connectingDrag.value) {
    // Convert screen coords to canvas coords
    const canvasX = (mouseX - canvasPan.value.x) / canvasZoom.value
    const canvasY = (mouseY - canvasPan.value.y) / canvasZoom.value
    connectingDrag.value = { ...connectingDrag.value, toX: canvasX, toY: canvasY }
    return
  }

  // Panning
  if (panning.value) {
    canvasPan.value = {
      x: panning.value.startPanX + (e.clientX - panning.value.startMouseX),
      y: panning.value.startPanY + (e.clientY - panning.value.startMouseY)
    }
    return
  }
}

// Global mouseup handler
function onGlobalMouseUp(e) {
  // Finish node drag
  if (dragNode.value) {
    // Sync position back to selectedNode so inspector doesn't overwrite it
    const node = formData.value.nodes.find(n => n.id === dragNode.value.id)
    if (node && selectedNode.value?.id === node.id) {
      selectedNode.value = { ...selectedNode.value, x: node.x, y: node.y }
    }
    dragNode.value = null
    return
  }

  // Finish connecting drag
  if (connectingDrag.value) {
    const ds = connectingDrag.value
    connectingDrag.value = null

    // Check if released over a node's input port
    if (!canvasWrap.value) return
    const rect = canvasWrap.value.getBoundingClientRect()
    const mouseX = e.clientX - rect.left
    const mouseY = e.clientY - rect.top
    const canvasX = (mouseX - canvasPan.value.x) / canvasZoom.value
    const canvasY = (mouseY - canvasPan.value.y) / canvasZoom.value

    // Find target node
    let targetNode = null
    for (const node of formData.value.nodes) {
      if (node.id === ds.from) continue
      const nx = node.x
      const ny = node.y
      const nw = NODE_WIDTH
      const nh = getNodeHeight(node)
      const portX = nx  // input port at left edge
      const portY = ny + nh / 2
      const dist = Math.hypot(canvasX - portX, canvasY - portY)
      if (dist < 15 / canvasZoom.value) {
        targetNode = node
        break
      }
    }

    if (targetNode) {
      const err = validateEdge(ds.from, targetNode.id)
      if (err) {
        showHintError(err + '，已取消')
      } else {
        const edgeId = `edge_${Date.now()}`
        formData.value.edges.push({ id: edgeId, from: ds.from, to: targetNode.id })
      }
    }
    return
  }

  // Finish panning
  if (panning.value) {
    panning.value = null
  }
}

// Click on node (select it - after drag, mousedown already selects)
function onNodeClick(node) {
  // Selection is handled in onNodeMouseDown, this is for when no drag happened
  pendingEdgeSource.value = null
  hintError.value = ''
}

function showHintError(msg) {
  hintError.value = '❌ ' + msg
  pendingEdgeSource.value = null
  setTimeout(() => { hintError.value = '' }, 2500)
}function initGraph() {
  // No-op: custom canvas init is handled in showEditor watcher
  canvasPan.value = { x: 250, y: 120 }
  canvasZoom.value = 1
  // Attach global mouse listeners
  document.addEventListener('mousemove', onGlobalMouseMove)
  document.addEventListener('mouseup', onGlobalMouseUp)
}

// ---- DAG cycle detection ----
function validateEdge(fromId, toId) {
  // 自连
  if (fromId === toId) return '不能连接到自身'
  // 重复边
  if (formData.value.edges.some(e => e.from === fromId && e.to === toId)) return '该连线已存在'
  // 环路检测: BFS from toId to see if we can reach fromId
  const adj = {}
  for (const n of formData.value.nodes) adj[n.id] = []
  for (const e of formData.value.edges) {
    if (adj[e.from]) adj[e.from].push(e.to)
  }
  // Add the prospective edge
  if (!adj[fromId]) return null
  adj[fromId].push(toId)

  const visited = new Set()
  const queue = [toId]
  while (queue.length > 0) {
    const cur = queue.shift()
    if (cur === fromId) return '创建该连线将产生环路' // cycle found
    if (visited.has(cur)) continue
    visited.add(cur)
    for (const next of (adj[cur] || [])) {
      if (!visited.has(next)) queue.push(next)
    }
  }
  return null // valid
}

function onCanvasKeydown(e) {
  const tag = e.target.tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return
  if (!showEditor.value) return
  if (e.key === 'Delete' || e.key === 'Backspace') {
    if (selectedNode.value) {
      deleteNode(selectedNode.value.id)
    } else if (selectedEdge.value) {
      deleteEdge(selectedEdge.value.id)
    }
  }
}

function deleteNode(nodeId) {
  formData.value.nodes = formData.value.nodes.filter(n => n.id !== nodeId)
  formData.value.edges = formData.value.edges.filter(ed => ed.from !== nodeId && ed.to !== nodeId)
  if (selectedNode.value?.id === nodeId) selectedNode.value = null
}

function deleteEdge(edgeId) {
  formData.value.edges = formData.value.edges.filter(ed => ed.id !== edgeId)
  if (selectedEdge.value?.id === edgeId) selectedEdge.value = null
}

function onNodeContextMenu(e, node) {
  e.preventDefault()
  selectedNode.value = node
  selectedEdge.value = null
  contextMenu.value = { show: true, x: e.clientX, y: e.clientY, type: 'node' }
}

function onEdgeContextMenu(e, edge) {
  e.preventDefault()
  selectedEdge.value = edge
  selectedNode.value = null
  contextMenu.value = { show: true, x: e.clientX, y: e.clientY, type: 'edge' }
}

function closeContextMenu() {
  contextMenu.value.show = false
}

function handleContextDelete() {
  if (contextMenu.value.type === 'node' && selectedNode.value) {
    deleteNode(selectedNode.value.id)
  } else if (contextMenu.value.type === 'edge' && selectedEdge.value) {
    deleteEdge(selectedEdge.value.id)
  }
  closeContextMenu()
}

function handleContextDuplicate() {
  if (contextMenu.value.type === 'node' && selectedNode.value) {
    const n = selectedNode.value
    const copy = { ...n, id: 'node_' + Date.now(), x: n.x + 30, y: n.y + 30 }
    formData.value.nodes.push(copy)
  }
  closeContextMenu()
}

function addNode(type) {
  const base = {
    id: `node_${Date.now()}`, type,
    name: nodeTypes[type]?.label || '新节点',
    x: (-canvasPan.value.x + 400) / canvasZoom.value + Math.random() * 100,
    y: (-canvasPan.value.y + 250) / canvasZoom.value + Math.random() * 100,
    description: ''
  }
  switch (type) {
    case 'start':
      base.variables = [{ name: 'input', type: 'text', default: '' }]
      break
    case 'agent':
      base.agent_id = null
      base.tools = []
      break
    case 'llm':
      base.model = ''
      base.system_prompt = ''
      base.user_prompt = ''
      base.temperature = 0.7
      base.max_tokens = 2048
      break
    case 'condition':
      base.branches = [
        { id: 'branch_' + Date.now(), rules: [{ id: 'rule_' + Date.now(), value: '', _var: '', _op: '', _val: '', logic: 'and' }], target: '', isElse: false },
        { id: 'branch_else_' + Date.now(), rules: [], target: '', isElse: true }
      ]
      break
    case 'human_intervention':
      base.config = {
        title: '请选择处理方式',
        timeout: 300,
        default_branch: `branch_${Date.now()}_1`,
        branches: [
          { id: `branch_${Date.now()}_1`, label: '同意', desc: '继续执行', target: '' },
          { id: `branch_${Date.now()}_2`, label: '拒绝', desc: '终止执行', target: '' }
        ]
      }
      break
    case 'parallel':
      base.branches = [{ id: 'branch_0', label: '分支1' }, { id: 'branch_1', label: '分支2' }]
      break
    case 'join':
      break
    case 'reply':
      base.inputs = { message: '' }
      base.reply_mode = 'template'
      break
  }
  formData.value.nodes.push(base)
  // Select the newly added node
  selectedNode.value = JSON.parse(JSON.stringify(base))
  if (base.type === 'llm') detectPromptPreset(base.system_prompt)
}

function zoomIn()  { canvasZoom.value = Math.min(2, canvasZoom.value * 1.2) }
function zoomOut() { canvasZoom.value = Math.max(0.2, canvasZoom.value * 0.8) }
function resetZoom() {
  canvasZoom.value = 1
  canvasPan.value = { x: 250, y: 120 }
}

function getNodeName(nodeId) {
  const n = formData.value.nodes.find(n => n.id === nodeId)
  return n ? n.name : nodeId
}

// ---- Agent tools ----
async function loadAgentTools() {
  if (!selectedNode.value?.agent_id) {
    agentTools.value = []
    return
  }
  await loadAgentToolsById(selectedNode.value.agent_id)
}

async function loadAgentToolsById(agentId) {
  if (!agentId) {
    agentTools.value = []
    return
  }
  try {
    const r = await api.agents.getSkills(agentId)
    agentTools.value = r.data || []
  } catch (e) {
    console.error('加载工具失败:', e)
    agentTools.value = []
  }
}

async function loadModels() {
  try { const r = await api.models.list(); modelsList.value = r.data?.items || [] }
  catch (e) { console.error('加载模型列表失败:', e) }
}

const promptPresets = {
  translate: '你是一个专业翻译。请将用户的输入准确翻译为目标语言，保持原意和语气。',
  code: '你是一个资深程序员。请根据用户的需求生成高质量代码，包含注释，遵循最佳实践。',
  summary: '你是一个文本分析专家。请对用户提供的内容进行准确、简洁的总结，提取关键信息。',
  roleplay: '你是一个角色扮演助手。请根据用户的设定扮演指定角色，保持角色一致性和沉浸感。',
  custom: '',
}

function getPresetPrompt(type) { return promptPresets[type] || '' }

function onPromptPresetChange(val) {
  if (val && val !== 'custom') {
    selectedNode.value.system_prompt = promptPresets[val]
    llmPromptPreset.value = val
  } else if (val === 'custom') {
    selectedNode.value.system_prompt = ''
    llmPromptPreset.value = 'custom'
  } else {
    selectedNode.value.system_prompt = ''
    llmPromptPreset.value = ''
  }
}

function detectPromptPreset(text) {
  if (!text) { llmPromptPreset.value = ''; return }
  for (const [key, val] of Object.entries(promptPresets)) {
    if (val && text === val) { llmPromptPreset.value = key; return }
  }
  llmPromptPreset.value = 'custom'
}

function insertVarToPrompt(varRef) {
  if (!selectedNode.value) return
  const varName = varRef.startsWith('/') ? varRef.slice(1) : varRef
  const insertion = `{{${varName}}}`
  if (!selectedNode.value.user_prompt) {
    selectedNode.value.user_prompt = insertion
  } else {
    selectedNode.value.user_prompt += insertion
  }
}

function insertVarToReply(varRef) {
  if (!selectedNode.value) return
  const varName = varRef.startsWith('/') ? varRef.slice(1) : varRef
  const insertion = `{{${varName}}}`
  if (!selectedNode.value.inputs) selectedNode.value.inputs = { message: '' }
  if (!selectedNode.value.inputs.message) {
    selectedNode.value.inputs.message = insertion
  } else {
    selectedNode.value.inputs.message += insertion
  }
}

// ---- Start node variables (Dify-style typed list) ----
const startVariables = computed({
  get() {
    if (!selectedNode.value || selectedNode.value.type !== 'start') return []
    const vars = selectedNode.value.variables
    if (Array.isArray(vars)) {
      return vars
    }
    // Migrate from comma-separated string
    if (typeof vars === 'string' && vars) {
      const migrated = vars.split(',').map(v => v.trim()).filter(Boolean).map(name => ({ name, type: 'text', default: '' }))
      selectedNode.value.variables = migrated
      return migrated
    }
    const defaultVars = [{ name: 'input', type: 'text', default: '' }]
    selectedNode.value.variables = defaultVars
    return defaultVars
  },
  set(val) {
    if (selectedNode.value) selectedNode.value.variables = val
  }
})

function addStartVar() {
  if (!selectedNode.value) return
  const vars = Array.isArray(selectedNode.value.variables) ? selectedNode.value.variables : []
  selectedNode.value.variables = [...vars, { name: '', type: 'text', default: '' }]
}

function removeStartVar(idx) {
  if (!selectedNode.value) return
  const vars = Array.isArray(selectedNode.value.variables) ? [...selectedNode.value.variables] : []
  vars.splice(idx, 1)
  selectedNode.value.variables = vars
}

// ---- Condition helpers (old data migration) ----
function isElseCondition(cond) {
  return cond.isElse === true
}

function isElseBranch(b) {
  return b.isElse === true
}

function syncConditionValue(cond) {
  if (!cond._var || !cond._op || cond._op === 'empty' || cond._op === 'not_empty') {
    if (cond._op === 'empty') cond.value = `${cond._var} == ''`
    else if (cond._op === 'not_empty') cond.value = `${cond._var} != ''`
    else cond.value = ''
    return
  }
  const varRef = cond._var
  switch (cond._op) {
    case 'eq': cond.value = `${varRef} == "${cond._val}"`; break
    case 'ne': cond.value = `${varRef} != "${cond._val}"`; break
    case 'in': cond.value = `"${cond._val}" in ${varRef}`; break
    case 'not_in': cond.value = `"${cond._val}" not in ${varRef}`; break
    case 'gt': cond.value = `${varRef} > ${cond._val}`; break
    case 'lt': cond.value = `${varRef} < ${cond._val}`; break
    case 'gte': cond.value = `${varRef} >= ${cond._val}`; break
    case 'lte': cond.value = `${varRef} <= ${cond._val}`; break
    case 'startswith': cond.value = `${varRef}.startswith("${cond._val}")`; break
    case 'endswith': cond.value = `${varRef}.endswith("${cond._val}")`; break
    default: cond.value = ''
  }
  if (selectedNode.value) selectedNode.value = { ...selectedNode.value }
}

function parseConditionFromValue(cond) {
  const val = cond.value || ''
  cond._var = cond._var || ''
  cond._op = cond._op || ''
  cond._val = cond._val || ''
  if (!val) return
  const inMatch = val.match(/"(.+)" in (.+)/)
  if (inMatch) { cond._var = inMatch[2]; cond._op = 'in'; cond._val = inMatch[1]; return }
  const notInMatch = val.match(/"(.+)" not in (.+)/)
  if (notInMatch) { cond._var = notInMatch[2]; cond._op = 'not_in'; cond._val = notInMatch[1]; return }
  const eqMatch = val.match(/(.+) == "(.+)"/)
  if (eqMatch) { cond._var = eqMatch[1]; cond._op = 'eq'; cond._val = eqMatch[2]; return }
  const neMatch = val.match(/(.+) != "(.+)"/)
  if (neMatch) { cond._var = neMatch[1]; cond._op = 'ne'; cond._val = neMatch[2]; return }
  const gtMatch = val.match(/(.+) > (.+)/)
  if (gtMatch) { cond._var = gtMatch[1]; cond._op = 'gt'; cond._val = gtMatch[2]; return }
  const ltMatch = val.match(/(.+) < (.+)/)
  if (ltMatch) { cond._var = ltMatch[1]; cond._op = 'lt'; cond._val = ltMatch[2]; return }
  const gteMatch = val.match(/(.+) >= (.+)/)
  if (gteMatch) { cond._var = gteMatch[1]; cond._op = 'gte'; cond._val = gteMatch[2]; return }
  const lteMatch = val.match(/(.+) <= (.+)/)
  if (lteMatch) { cond._var = lteMatch[1]; cond._op = 'lte'; cond._val = lteMatch[2]; return }
  const swMatch = val.match(/(.+)\.startswith\("(.+)"\)/)
  if (swMatch) { cond._var = swMatch[1]; cond._op = 'startswith'; cond._val = swMatch[2]; return }
  const ewMatch = val.match(/(.+)\.endswith\("(.+)"\)/)
  if (ewMatch) { cond._var = ewMatch[1]; cond._op = 'endswith'; cond._val = ewMatch[2]; return }
  const emptyMatch = val.match(/(.+) == ''/)
  if (emptyMatch) { cond._var = emptyMatch[1]; cond._op = 'empty'; cond._val = ''; return }
  const notEmptyMatch = val.match(/(.+) != ''/)
  if (notEmptyMatch) { cond._var = notEmptyMatch[1]; cond._op = 'not_empty'; cond._val = ''; return }
  if (selectedNode.value) selectedNode.value = { ...selectedNode.value }
}

// ---- Rule helpers (branches + rules) ----
function parseRuleValue(rule) {
  const val = rule.value || ''
  rule._var = rule._var || ''
  rule._op = rule._op || ''
  rule._val = rule._val || ''
  if (!val) return
  const inMatch = val.match(/"(.+)" in (.+)/)
  if (inMatch) { rule._var = inMatch[2]; rule._op = 'in'; rule._val = inMatch[1]; return }
  const notInMatch = val.match(/"(.+)" not in (.+)/)
  if (notInMatch) { rule._var = notInMatch[2]; rule._op = 'not_in'; rule._val = notInMatch[1]; return }
  const eqMatch = val.match(/(.+) == "(.+)"/)
  if (eqMatch) { rule._var = eqMatch[1]; rule._op = 'eq'; rule._val = eqMatch[2]; return }
  const neMatch = val.match(/(.+) != "(.+)"/)
  if (neMatch) { rule._var = neMatch[1]; rule._op = 'ne'; rule._val = neMatch[2]; return }
  const gtMatch = val.match(/(.+) > (.+)/)
  if (gtMatch) { rule._var = gtMatch[1]; rule._op = 'gt'; rule._val = gtMatch[2]; return }
  const ltMatch = val.match(/(.+) < (.+)/)
  if (ltMatch) { rule._var = ltMatch[1]; rule._op = 'lt'; rule._val = ltMatch[2]; return }
  const gteMatch = val.match(/(.+) >= (.+)/)
  if (gteMatch) { rule._var = gteMatch[1]; rule._op = 'gte'; rule._val = gteMatch[2]; return }
  const lteMatch = val.match(/(.+) <= (.+)/)
  if (lteMatch) { rule._var = lteMatch[1]; rule._op = 'lte'; rule._val = lteMatch[2]; return }
  const swMatch = val.match(/(.+)\.startswith\("(.+)"\)/)
  if (swMatch) { rule._var = swMatch[1]; rule._op = 'startswith'; rule._val = swMatch[2]; return }
  const ewMatch = val.match(/(.+)\.endswith\("(.+)"\)/)
  if (ewMatch) { rule._var = ewMatch[1]; rule._op = 'endswith'; rule._val = ewMatch[2]; return }
  const emptyMatch = val.match(/(.+) == ''/)
  if (emptyMatch) { rule._var = emptyMatch[1]; rule._op = 'empty'; rule._val = ''; return }
  const notEmptyMatch = val.match(/(.+) != ''/)
  if (notEmptyMatch) { rule._var = notEmptyMatch[1]; rule._op = 'not_empty'; rule._val = ''; return }
}

function syncRuleValue(rule) {
  if (!rule._var || !rule._op || rule._op === 'empty' || rule._op === 'not_empty') {
    if (rule._op === 'empty') rule.value = `${rule._var} == ''`
    else if (rule._op === 'not_empty') rule.value = `${rule._var} != ''`
    else rule.value = ''
    return
  }
  const varRef = rule._var
  switch (rule._op) {
    case 'eq': rule.value = `${varRef} == "${rule._val}"`; break
    case 'ne': rule.value = `${varRef} != "${rule._val}"`; break
    case 'in': rule.value = `"${rule._val}" in ${varRef}`; break
    case 'not_in': rule.value = `"${rule._val}" not in ${varRef}`; break
    case 'gt': rule.value = `${varRef} > ${rule._val}`; break
    case 'lt': rule.value = `${varRef} < ${rule._val}`; break
    case 'gte': rule.value = `${varRef} >= ${rule._val}`; break
    case 'lte': rule.value = `${varRef} <= ${rule._val}`; break
    case 'startswith': rule.value = `${varRef}.startswith("${rule._val}")`; break
    case 'endswith': rule.value = `${varRef}.endswith("${rule._val}")`; break
    default: rule.value = ''
  }
}

function onBranchTargetChange(branch) {
  if (!selectedNode.value || !branch.target) return
  const edgeId = `cond_branch_${branch.id}`
  const fromId = selectedNode.value.id
  const toId = branch.target
  const existing = formData.value.edges.find(e => e.id === edgeId)
  if (existing) {
    existing.from = fromId; existing.to = toId
  } else {
    formData.value.edges.push({ id: edgeId, from: fromId, to: toId })
  }
}

function addIfBranch() {
  if (!selectedNode.value) return
  const oldBranches = selectedNode.value.branches || []
  const elseIdx = oldBranches.findIndex(b => b.isElse)
  const prep = elseIdx !== -1 ? oldBranches.slice(0, elseIdx) : [...oldBranches]
  const elseBr = elseIdx !== -1 ? oldBranches[elseIdx] : null
  const newBranch = {
    id: 'branch_' + Date.now(),
    rules: [{ id: 'rule_' + Date.now(), value: '', _var: '', _op: '', _val: '', logic: 'and' }],
    target: '',
    isElse: false
  }
  selectedNode.value = {
    ...selectedNode.value,
    branches: [...prep, newBranch, ...(elseBr ? [elseBr] : [])]
  }
}

function addRule(branch) {
  if (!branch) return
  const rules = branch.rules || []
  rules.push({ id: 'rule_' + Date.now(), value: '', _var: '', _op: '', _val: '', logic: 'and' })
  selectedNode.value = { ...selectedNode.value }
}

function removeRule(branch, idx) {
  if (!branch) return
  const rules = branch.rules || []
  if (rules.length <= 1) return
  rules.splice(idx, 1)
  selectedNode.value = { ...selectedNode.value }
}

function toggleRuleLogic(rule) {
  rule.logic = rule.logic === 'or' ? 'and' : 'or'
  selectedNode.value = { ...selectedNode.value }
}

// ---- Branch helpers (human_intervention) ----
function addBranch() {
  if (!selectedNode.value) return
  if (!selectedNode.value.config) selectedNode.value.config = { branches: [] }
  if (!selectedNode.value.config.branches) selectedNode.value.config.branches = []
  selectedNode.value.config.branches.push({ id: `branch_${Date.now()}`, label: '', desc: '', target: '' })
}

function onHumanBranchTargetChange(branch) {
  if (!selectedNode.value || !branch.target) return
  const edgeId = `human_branch_${branch.id}`
  const fromId = selectedNode.value.id
  const toId = branch.target
  const existing = formData.value.edges.find(e => e.id === edgeId)
  if (existing) {
    existing.from = fromId; existing.to = toId
  } else {
    formData.value.edges.push({ id: edgeId, from: fromId, to: toId })
  }
}

// ---- Merged removeBranch (handles both condition & human_intervention) ----
function removeBranch(idx) {
  if (!selectedNode.value) return
  // Human intervention branch
  if (selectedNode.value.config?.branches) {
    if (selectedNode.value.config.branches.length <= 1) return
    selectedNode.value.config.branches.splice(idx, 1)
    return
  }
  // Condition branch
  const oldBranches = selectedNode.value.branches || []
  if (oldBranches[idx]?.isElse) return
  const removed = oldBranches[idx]
  if (removed.id) {
    const edgeId = `cond_branch_${removed.id}`
    formData.value.edges = formData.value.edges.filter(e => e.id !== edgeId)
  }
  const newBranches = [...oldBranches]
  newBranches.splice(idx, 1)
  selectedNode.value = { ...selectedNode.value, branches: newBranches }
}

// ---- SSE ----
async function readSSE(response, callbacks) {
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let currentEvent = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''
    for (const line of lines) {
      if (line.startsWith('event: ')) {
        currentEvent = line.slice(7).trim()
      } else if (line.startsWith('data: ')) {
        try {
          const parsed = JSON.parse(line.slice(6))
          const eventName = parsed.event || currentEvent
          if (callbacks[eventName]) {
            callbacks[eventName](parsed.data)
          }
          currentEvent = ''
        } catch (e) {
          console.warn('SSE parse error:', e)
        }
      } else if (line.trim() === '') {
        currentEvent = ''
      }
    }
  }
}

// ---- Test chat ----
async function runTest() {
  if (!testInput.value.trim() || isRunning.value) return
  // Check start node exists
  const hasStart = formData.value.nodes.some(n => n.type === 'start')
  if (!hasStart) {
    messages.value.push({ role: 'error', content: '工作流需要至少一个开始(Start)节点' })
    return
  }
  // 未保存时自动保存
  if (!formData.value.id) {
    if (!formData.value.name.trim()) {
      formData.value.name = '未命名工作流'
    }
    try {
      await saveWorkflow(true)
    } catch (e) {
      messages.value.push({ role: 'error', content: '保存失败: ' + e.message })
      return
    }
  } else {
    // Auto-save changes before test
    try {
      await saveWorkflow(true)
    } catch (e) {
      // Non-fatal: test with existing saved data
      console.warn('Auto-save before test failed:', e)
    }
  }
  isTesting.value = true
  const msg = testInput.value
  messages.value.push({ role: 'user', content: msg })
  testInput.value = ''
  isRunning.value = true
  variableContext.value = {}
  nodeOutputs.value = []
  // Reset edge highlighting for new run
  activeEdges.value = new Set()
  executedNodeIds.value = new Set()
  try {
    const response = await api.workflows.test(formData.value.id, { message: msg, history: [] })
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}))
      throw new Error(errData.message || errData.detail || '测试请求失败')
    }
    await runTestSSE(response)
  } catch (e) {
    messages.value.push({ role: 'error', content: '测试失败: ' + e.message })
    isRunning.value = false
    isTesting.value = false
  }
}

async function runTestSSE(response) {
  let hasFinal = false
  const nodeStartTime = {}
  const sseHandlers = {
    node_start: (data) => {
      nodeStartTime[data.node_id] = Date.now()
      nodeStates.value = { ...nodeStates.value, [data.node_id]: 'running' }
      // Light up incoming edges from already-executed nodes
      const incomingEdges = formData.value.edges.filter(
        e => e.to === data.node_id && executedNodeIds.value.has(e.from)
      )
      if (incomingEdges.length > 0) {
        const next = new Set(activeEdges.value)
        incomingEdges.forEach(e => next.add(e.id))
        activeEdges.value = next
      }
      messages.value.push({ role: 'node', content: '', nodeId: data.node_id, nodeType: data.node_type })
      // Add log entry
      const node = formData.value.nodes.find(n => n.id === data.node_id)
      logEntries.value.push({
        nodeId: data.node_id,
        nodeName: node?.name || data.node_id,
        nodeType: data.node_type,
        status: 'running',
        input: null,
        output: null,
        duration: null,
        tokens: null,
        expanded: false
      })
    },
    node_output: (data) => {
      const lastNodeMsg = [...messages.value].reverse().find(m => m.nodeId === data.node_id && m.role === 'node')
      if (lastNodeMsg) lastNodeMsg.content += data.output
      // Update log entry output
      const logEntry = logEntries.value.find(e => e.nodeId === data.node_id && e.status === 'running')
      if (logEntry) {
        logEntry.output = data.output
        if (data.usage) {
          logEntry.tokens = data.usage
        }
      }
      // Capture variable context
      if (data.variable) {
        variableContext.value = { ...variableContext.value, [data.variable]: data.output }
      }
      // Capture node output
      const node = formData.value.nodes.find(n => n.id === data.node_id)
      const nodeName = node?.name || data.node_id
      nodeOutputs.value.push({
        time: new Date().toLocaleTimeString(),
        nodeName,
        varKey: data.variable || `${nodeName}_output`,
        output: typeof data.output === 'string' ? data.output.slice(0, 100) : JSON.stringify(data.output).slice(0, 100)
      })
      // Condition node: light up outgoing edge to the chosen branch's target
      if (node && node.type === 'condition' && typeof data.output === 'string') {
        const chosenBranch = (node.branches || []).find(b => b.id === data.output)
        if (chosenBranch && chosenBranch.target) {
          const outEdge = formData.value.edges.find(
            e => e.from === data.node_id && e.to === chosenBranch.target
          )
          if (outEdge) {
            const next = new Set(activeEdges.value)
            next.add(outEdge.id)
            activeEdges.value = next
          }
        }
      }
    },
    node_end: (data) => {
      nodeStates.value = { ...nodeStates.value, [data.node_id]: 'done' }
      // Track executed node for edge highlighting
      const next = new Set(executedNodeIds.value)
      next.add(data.node_id)
      executedNodeIds.value = next
      const logEntry = logEntries.value.find(e => e.nodeId === data.node_id && e.status === 'running')
      if (logEntry) {
        logEntry.status = 'done'
        logEntry.duration = Date.now() - (nodeStartTime[data.node_id] || Date.now())
      }
    },
    log_update: (data) => {
      // Update existing log entry or add a log message
      const logEntry = logEntries.value.find(e => e.nodeId === data.node_id)
      if (logEntry && data.log) {
        logEntry.status = data.status || logEntry.status
      }
    },
    final: (data) => {
      hasFinal = true
      messages.value.push({ role: 'assistant', content: data.output })
      nodeStates.value = {}
      isRunning.value = false
      isTesting.value = false
    },
    error: (data) => {
      if (data.node_id) {
        nodeStates.value = { ...nodeStates.value, [data.node_id]: 'error' }
      }
      messages.value.push({ role: 'error', content: data.error || data.message || '执行错误', nodeId: data.node_id })
      isRunning.value = false
      isTesting.value = false
    },
    human_intervention: (data) => {
      pausedNodeId.value = data.node_id
      interventionData.value = data
      // Mark human_intervention node as executed so downstream edges can light up after resume
      const next = new Set(executedNodeIds.value)
      next.add(data.node_id)
      executedNodeIds.value = next
      messages.value.push({ role: 'system', content: `⏸️ ${data.title || '需要人工介入'}` })
      startCountdown(data.timeout || 300)
    }
  }
  await readSSE(response, sseHandlers)
  if (!hasFinal && !interventionData.value && isRunning.value) {
    isRunning.value = false
    isTesting.value = false
  }
}

function startCountdown(seconds) {
  countdown.value = seconds
  if (countdownTimer) clearInterval(countdownTimer)
  countdownTimer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      clearInterval(countdownTimer)
      countdownTimer = null
      if (interventionData.value?.default_branch) {
        selectBranch(interventionData.value.default_branch)
      }
    }
  }, 1000)
}

async function selectBranch(choice) {
  if (countdownTimer) { clearInterval(countdownTimer); countdownTimer = null }
  interventionData.value = null
  messages.value.push({ role: 'system', content: `用户选择: ${choice}` })
  try {
    const response = await api.workflows.resume(formData.value.id, { node_id: pausedNodeId.value, choice })
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}))
      throw new Error(errData.message || errData.detail || '恢复执行失败')
    }
    await runTestSSE(response)
  } catch (e) {
    messages.value.push({ role: 'error', content: '恢复执行失败: ' + e.message })
    isRunning.value = false
    isTesting.value = false
  }
  pausedNodeId.value = null
}

// ---- Preview (deprecated: now uses DOM + SVG) ----
function initPreviewGraph() {
  // No-op: detail view uses DOM nodes + SVG edges directly
  // Kept for backward compatibility, can be called safely
}

// ---- Delete ----
function confirmDelete(wf) { deleteWorkflow.value = wf; showDeleteConfirm.value = true }

async function deleteWorkflowConfirm() {
  try {
    await api.workflows.delete([deleteWorkflow.value.id])
    showDeleteConfirm.value = false
    if (showEditor.value) { showEditor.value = false }
    else if (isDetail.value) goBack()
    else loadWorkflows()
  } catch (e) { console.error('删除失败:', e) }
}

// ---- Validate ----
function validateVariables() {
  const allVars = []
  for (const node of formData.value.nodes) {
    const nodeName = node.name || getNodeTypeName(node.type)
    if (node.type === 'start') {
      const varArr = typeof node.variables === 'string' ? node.variables.split(',').map(v => v.trim()).filter(Boolean) : (Array.isArray(node.variables) ? node.variables : [])
      for (const v of varArr) {
        const key = `${nodeName}_${v}`
        if (allVars.includes(key)) {
          return { valid: false, msg: `变量 "${v}" 在节点 "${nodeName}" 中与已有变量重名` }
        }
        allVars.push(key)
      }
    } else {
      const key = `${nodeName}_output`
      if (allVars.includes(key)) {
        return { valid: false, msg: `节点 "${nodeName}" 的输出变量与已有变量重名` }
      }
      allVars.push(key)
    }
  }
  return { valid: true }
}

function validateParallelNesting() {
  const parallelNodes = formData.value.nodes.filter(n => n.type === 'parallel')
  if (parallelNodes.length === 0) return null
  // Build adjacency: nodeId → [child node ids reachable via edges]
  const children = {}
  for (const n of formData.value.nodes) children[n.id] = []
  for (const e of formData.value.edges) {
    if (children[e.from]) children[e.from].push(e.to)
  }
  // DFS to find max nesting depth of parallel nodes
  let maxDepth = 0
  const visited = new Set()
  function dfs(nodeId, depth) {
    if (visited.has(nodeId)) return
    visited.add(nodeId)
    const node = formData.value.nodes.find(n => n.id === nodeId)
    if (node?.type === 'parallel') {
      maxDepth = Math.max(maxDepth, depth)
    }
    for (const child of (children[nodeId] || [])) {
      dfs(child, depth + (node?.type === 'parallel' ? 1 : 0))
    }
  }
  for (const pn of parallelNodes) {
    visited.clear()
    dfs(pn.id, 1)
  }
  if (maxDepth >= 4) return `并行嵌套层级不能超过3层（当前最大${maxDepth}层）`
  return null
}

// ---- Save ----
async function saveWorkflow(silent = false) {
  if (!silent) {
    if (!formData.value.name.trim()) { alert('请输入工作流名称'); return }
    const varResult = validateVariables()
    if (!varResult.valid) { alert(varResult.msg); return }
    const nestErr = validateParallelNesting()
    if (nestErr) { alert(nestErr); return }
  }
  // Node positions are already stored in formData directly (custom canvas)
  // Sync selectedNode to formData before saving (ensure latest edits are captured)
  if (selectedNode.value) {
    const sidx = formData.value.nodes.findIndex(n => n.id === selectedNode.value.id)
    if (sidx !== -1) {
      formData.value.nodes[sidx] = JSON.parse(JSON.stringify(selectedNode.value))
    }
  }
  // Preprocess: convert start node variables from string to array
  for (const node of formData.value.nodes) {
    if (node.type === 'start' && typeof node.variables === 'string') {
      node.variables = node.variables.split(',').map(v => v.trim()).filter(Boolean)
    }
  }
  // Serialize condition nodes: sync structured fields → value string
  formData.value.nodes.forEach(n => {
    if (n.type === 'condition' && n.branches) {
      n.branches.forEach(b => {
        if (b.rules) b.rules.forEach(r => syncRuleValue(r))
      })
    }
  })
  isSaving.value = true
  try {
    // Clean payload — only include fields the API expects
    const payload = {
      name: formData.value.name || '未命名工作流',
      description: formData.value.description || '',
      nodes: formData.value.nodes,
      edges: formData.value.edges,
      agent_id: formData.value.agent_id || undefined
    }
    console.log('SAVE payload:', JSON.stringify(payload))
    const saved = isEdit.value
      ? await api.workflows.update(formData.value.id, payload)
      : await api.workflows.create(payload)

    console.log('SAVE response:', saved)
    const savedData = saved?.data || saved
    if (savedData?.id) formData.value.id = savedData.id

    // Sync in-memory data (both silent and manual save)
    const idx = workflows.value.findIndex(w => w.id === formData.value.id)
    if (idx !== -1) {
      workflows.value[idx].name = formData.value.name
      workflows.value[idx].description = formData.value.description
      workflows.value[idx].nodes = JSON.parse(JSON.stringify(formData.value.nodes))
      workflows.value[idx].edges = JSON.parse(JSON.stringify(formData.value.edges))
    }
    if (workflowDetail.value?.id === formData.value.id) {
      workflowDetail.value.name = formData.value.name
      workflowDetail.value.description = formData.value.description
      workflowDetail.value.nodes = JSON.parse(JSON.stringify(formData.value.nodes))
      workflowDetail.value.edges = JSON.parse(JSON.stringify(formData.value.edges))
    }

    if (silent) return

    // Show success toast AFTER closing editor
    const isEditNow = isEdit.value
    const isDetailNow = isDetail.value
    if (!isEditNow && savedData?.id) {
      closeEditor()
      await loadWorkflows()
      ElMessage.success('保存成功')
    } else {
      closeEditor()
      ElMessage.success('保存成功')
    }
  } catch (e) {
    console.error('保存失败:', e)
    if (!silent) ElMessage.error('保存失败: ' + (e.message || e))
  }
  finally { isSaving.value = false }
}

// ---- Watchers ----
watch(selectedNode, (val) => {
  if (!val) return
  const idx = formData.value.nodes.findIndex(n => n.id === val.id)
  if (idx !== -1) {
    formData.value.nodes[idx] = JSON.parse(JSON.stringify(val))
  }
}, { deep: true })

watch(selectedEdge, (val) => {
  if (!val) return
  const edge = formData.value.edges.find(e => e.id === val.id)
  if (edge) {
    Object.assign(edge, val)
  }
}, { deep: true })

// nodeStates changes are handled reactively by Vue (node-status class on .wf-node)

watch(showEditor, (val) => {
  if (val) {
    nextTick(() => initGraph())
    document.addEventListener('keydown', onCanvasKeydown)
  } else {
    document.removeEventListener('keydown', onCanvasKeydown)
  }
})

onMounted(async () => {
  await loadAgents()
  if (route.params.id) await loadWorkflowDetail(route.params.id)
  else await loadWorkflows()
})

onUnmounted(() => {
  document.removeEventListener('keydown', onCanvasKeydown)
  document.removeEventListener('mousemove', onGlobalMouseMove)
  document.removeEventListener('mouseup', onGlobalMouseUp)
  if (countdownTimer) { clearInterval(countdownTimer); countdownTimer = null }
})
</script>

<style scoped>
/* ============================ DESIGN TOKENS ============================ */
.workflow-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  --bg-base: #0a0e1a;
  --bg-surface: #111726;
  --bg-elevated: #161d2e;
  --bg-hover: #1c2438;
  --border-subtle: rgba(255,255,255,0.06);
  --border-default: rgba(255,255,255,0.10);
  --border-strong: rgba(255,255,255,0.16);
  --text-primary: #e8edf5;
  --text-secondary: #9aa5b8;
  --text-muted: #5d6778;
  --accent: #3b82f6;
  --accent-glow: rgba(59,130,246,0.15);
  --n-start: #8b5cf6;
  --n-agent: #3b82f6;
  --n-llm: #06b6d4;
  --n-condition: #f59e0b;
  --n-parallel: #14b8a6;
  --n-join: #6366f1;
  --n-human: #ec4899;
  --n-reply: #10b981;
  --status-idle: #475569;
  --status-running: #3b82f6;
  --status-done: #10b981;
  --status-error: #ef4444;
  --status-paused: #f59e0b;
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;
  --shadow-card: 0 4px 24px rgba(0,0,0,0.35);
  --shadow-glass: inset 0 1px 0 rgba(255,255,255,0.06), 0 8px 32px rgba(0,0,0,0.4);
  --font-sans: 'Geist', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  --font-mono: 'Geist Mono', 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
}

.wf-editor {
  position: fixed;
  inset: 0;
  z-index: 2000;
  display: flex;
  flex-direction: column;
  background: var(--bg-base);
  font-family: var(--font-sans);
}

/* ============================ TOPBAR ============================ */
.topbar {
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
  z-index: 100;
}
.topbar-left, .topbar-center, .topbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
.topbar-divider {
  width: 1px;
  height: 22px;
  background: var(--border-default);
}
.btn-back {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  transition: all .15s;
  background: none;
  border: none;
  font-family: inherit;
}
.btn-back:hover { color: var(--text-primary); background: var(--bg-hover); }
.wf-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  padding: 4px 12px;
  border-radius: var(--radius-sm);
  border: 1px solid transparent;
  transition: all .15s;
  min-width: 200px;
  background: transparent;
  font-family: inherit;
  outline: none;
}
.wf-name:hover { border-color: var(--border-default); background: var(--bg-hover); }
.wf-name:focus { border-color: var(--accent); background: var(--bg-hover); }
.zoom-group {
  display: flex;
  align-items: center;
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  overflow: hidden;
}
.zoom-btn {
  width: 30px; height: 28px;
  display: flex; align-items: center; justify-content: center;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 16px;
  transition: all .12s;
  background: none; border: none;
  font-family: inherit;
}
.zoom-btn:hover { color: var(--text-primary); background: var(--bg-hover); }
.zoom-label {
  font-size: 11px;
  color: var(--text-muted);
  min-width: 42px;
  text-align: center;
  font-family: var(--font-mono);
}
.node-badge {
  font-size: 11px;
  color: var(--text-muted);
  padding: 3px 8px;
  background: var(--bg-elevated);
  border-radius: 4px;
  font-family: var(--font-mono);
}
.btn-test {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 16px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all .15s;
  border: none;
  background: var(--accent);
  color: #fff;
  box-shadow: 0 0 0 1px rgba(59,130,246,0.3), 0 2px 8px rgba(59,130,246,0.25);
  font-family: inherit;
}
.btn-test:hover { background: #2563eb; transform: translateY(-1px); }
.btn-test:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
.run-dot-small {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #fff;
  animation: pulse-dot 1s infinite;
}
.btn-save {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all .15s;
  border: 1px solid var(--border-default);
  background: var(--bg-elevated);
  color: var(--text-primary);
  font-family: inherit;
}
.btn-save:hover { border-color: var(--border-strong); background: var(--bg-hover); }
.btn-save:disabled { opacity: 0.5; cursor: not-allowed; }

/* ============================ BODY AREA ============================ */
.body-area {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* ============================ LEFT PALETTE ============================ */
.palette {
  width: 220px;
  background: var(--bg-surface);
  border-right: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}
.palette-header {
  padding: 14px 16px 10px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: var(--text-muted);
}
.palette-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px 12px;
}
.palette-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 10px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all .12s;
  margin-bottom: 2px;
}
.palette-item:hover { background: var(--bg-hover); }
.palette-dot {
  width: 10px; height: 10px;
  border-radius: 50%;
  margin-top: 4px;
  flex-shrink: 0;
  box-shadow: 0 0 8px currentColor;
}
.palette-info { display: flex; flex-direction: column; gap: 2px; }
.palette-label { font-size: 13px; font-weight: 500; color: var(--text-primary); }
.palette-desc { font-size: 11px; color: var(--text-muted); }
.palette-footer {
  padding: 12px 16px;
  border-top: 1px solid var(--border-subtle);
}
.palette-tip {
  font-size: 11px;
  color: var(--text-muted);
  line-height: 1.5;
}
.palette-tip strong { color: var(--text-secondary); }

/* ============================ CENTER CANVAS ============================ */
.canvas-wrap {
  flex: 1;
  position: relative;
  overflow: hidden;
  background:
    radial-gradient(circle at 20% 30%, rgba(59,130,246,0.04), transparent 50%),
    radial-gradient(circle at 80% 70%, rgba(139,92,246,0.03), transparent 50%),
    var(--bg-base);
}
.canvas-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
  background-size: 32px 32px;
  pointer-events: none;
}
.canvas-content {
  position: absolute;
  inset: 0;
}
.canvas-hint {
  position: absolute;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  background: rgba(17,23,38,0.8);
  backdrop-filter: blur(8px);
  border: 1px solid var(--border-subtle);
  border-radius: 20px;
  font-size: 11px;
  color: var(--text-muted);
  z-index: 10;
  white-space: nowrap;
}
.canvas-hint.hint-error {
  background: rgba(239,68,68,0.15);
  border-color: rgba(239,68,68,0.3);
  color: #f87171;
}

/* ============================ NODE CARDS (Dify-style) ============================ */
.wf-node {
  position: absolute;
  width: 200px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: 0;
  cursor: grab;
  transition: border-color .2s, box-shadow .2s, transform .15s;
  z-index: 2;
  overflow: visible;
  user-select: none;
}
.wf-node:active { cursor: grabbing; }
.wf-node:hover {
  border-color: var(--border-strong);
  box-shadow: var(--shadow-card);
}
.wf-node.selected {
  border-color: var(--node-color, var(--accent));
  box-shadow: 0 0 0 1px var(--node-color, var(--accent)), 0 0 24px -4px var(--node-color, var(--accent));
}
.wf-node.connect-source {
  border-color: #22c55e;
  box-shadow: 0 0 0 1px #22c55e, 0 0 16px -4px #22c55e;
}
.node-top-bar {
  height: 3px;
  background: var(--node-color, var(--accent));
  border-radius: var(--radius-md) var(--radius-md) 0 0;
}
.node-body {
  padding: 10px 12px 11px;
}
.node-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.node-icon {
  width: 26px; height: 26px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  flex-shrink: 0;
  background: color-mix(in srgb, var(--node-color) 15%, transparent);
  color: var(--node-color);
}
.node-title-row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 0;
}
.node-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.node-type-tag {
  font-size: 10px;
  color: var(--text-muted);
  font-family: var(--font-mono);
}
.node-status {
  width: 8px; height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--status-done);
  box-shadow: 0 0 6px currentColor;
}
.node-status.running {
  background: var(--status-running);
  animation: pulse-dot 1.2s infinite;
}
.node-status.error {
  background: var(--status-error);
}
.node-status.paused {
  background: var(--status-paused);
}
.node-meta {
  font-size: 11px;
  color: var(--text-muted);
  line-height: 1.4;
  display: flex;
  align-items: center;
  gap: 6px;
}
.node-meta-item {
  display: flex;
  align-items: center;
  gap: 3px;
}

/* Node ports */
.node-port {
  position: absolute;
  width: 12px; height: 12px;
  border-radius: 50%;
  background: var(--bg-base);
  border: 2px solid var(--node-color, var(--text-muted));
  top: 36px;
  z-index: 3;
  cursor: crosshair;
  transition: transform .15s, box-shadow .15s;
}
.node-port:hover {
  transform: scale(1.4);
  box-shadow: 0 0 8px var(--node-color, var(--accent));
}
.node-port.in { left: -7px; }
.node-port.out { right: -7px; }
.node-port.port-target {
  border-color: #22c55e;
  box-shadow: 0 0 8px rgba(34,197,94,0.5);
}
.node-port.port-highlight {
  animation: pulse-dot 1s infinite;
}
.node-port.port-source-active {
  border-color: #22c55e;
  background: #22c55e;
}

/* Branch badges */
.branch-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 6px;
}
.branch-badge {
  font-size: 9px;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: var(--font-mono);
  background: color-mix(in srgb, var(--n-condition) 12%, transparent);
  color: var(--n-condition);
  border: 1px solid color-mix(in srgb, var(--n-condition) 20%, transparent);
}
.branch-badge.else {
  background: color-mix(in srgb, #94a3b8 12%, transparent);
  color: #94a3b8;
  border-color: rgba(148,163,184,0.2);
}

/* ============================ SVG EDGES ============================ */
.edges-svg {
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
  pointer-events: none;
  z-index: 1;
  overflow: visible;
}
.edges-svg .edge-path {
  fill: none;
  stroke: rgba(255,255,255,0.12);
  stroke-width: 2;
  transition: stroke .2s, stroke-width .2s;
  pointer-events: stroke;
  cursor: pointer;
}
.edges-svg .edge-path:hover {
  stroke: rgba(59,130,246,0.5);
  stroke-width: 2.5;
}
.edges-svg .edge-path.active {
  stroke: rgba(59,130,246,0.9);
  stroke-width: 3;
  filter: drop-shadow(0 0 5px rgba(59,130,246,0.7));
}
.edge-label {
  font-size: 10px;
  fill: var(--text-muted);
  font-family: var(--font-sans);
  text-anchor: middle;
}
.edge-flow {
  fill: var(--accent);
  opacity: 0.85;
  filter: drop-shadow(0 0 4px rgba(59,130,246,0.9));
}
.drag-line-svg {
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
  pointer-events: none;
  z-index: 5;
  overflow: visible;
}

/* Run banner */
.run-banner {
  position: absolute;
  top: 12px;
  right: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  background: rgba(59,130,246,0.10);
  border: 1px solid rgba(59,130,246,0.25);
  border-radius: 20px;
  font-size: 12px;
  color: #60a5fa;
  z-index: 10;
  backdrop-filter: blur(8px);
}
.run-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--accent);
  animation: pulse-dot 1s infinite;
}

/* ============================ RIGHT INSPECTOR ============================ */
.inspector {
  width: 340px;
  background: var(--bg-surface);
  border-left: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}
.inspector-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px 10px;
  border-bottom: 1px solid var(--border-subtle);
}
.inspector-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
}
.inspector-close {
  color: var(--text-muted);
  cursor: pointer;
  font-size: 16px;
  background: none;
  border: none;
  padding: 2px;
  line-height: 1;
}
.inspector-close:hover { color: var(--text-primary); }
.inspector-header-actions { display: flex; align-items: center; gap: 4px; }
.inspector-delete {
  color: #f87171;
  cursor: pointer;
  font-size: 12px;
  background: rgba(248, 113, 113, 0.1);
  border: 1px solid rgba(248, 113, 113, 0.3);
  border-radius: 4px;
  padding: 2px 8px;
  line-height: 1;
  transition: all 0.15s;
}
.inspector-delete:hover {
  background: rgba(248, 113, 113, 0.2);
  color: #fca5a5;
}
.context-menu {
  position: fixed;
  z-index: 9999;
  background: var(--bg-elevated, #1a2234);
  border: 1px solid var(--border-default, #2a3548);
  border-radius: 8px;
  padding: 4px 0;
  min-width: 180px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.4);
}
.context-menu-item {
  padding: 8px 14px;
  font-size: 13px;
  color: var(--text-primary, #e8edf5);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background 0.1s;
}
.context-menu-item:hover {
  background: var(--bg-hover, #252e44);
  color: #f87171;
}
.context-menu-item .ctx-icon { font-size: 14px; }
.context-menu-item .ctx-kbd {
  margin-left: auto;
  font-size: 11px;
  color: var(--text-muted, #5d6778);
  background: var(--bg-surface, #111726);
  padding: 1px 5px;
  border-radius: 3px;
  border: 1px solid var(--border-subtle, #1e2638);
}
.context-menu-backdrop {
  position: fixed;
  inset: 0;
  z-index: 9998;
  background: transparent;
}
.inspector-body {
  flex: 1;
  overflow-y: auto;
  padding: 14px 16px;
}

/* Type badge */
.type-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  margin-bottom: 14px;
}
.type-badge .badge-icon { font-size: 13px; }

/* Inspector tabs */
.insp-tabs {
  display: flex;
  gap: 2px;
  margin-bottom: 14px;
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
  padding: 2px;
}
.insp-tab {
  flex: 1;
  padding: 5px 8px;
  text-align: center;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  cursor: pointer;
  border-radius: 4px;
  transition: all .12s;
}
.insp-tab.active {
  background: var(--bg-hover);
  color: var(--text-primary);
}

/* Form overrides for El-Plus inside inspector */
.config-form .el-form-item { margin-bottom: 12px; }
.config-form .el-form-item__label { color: var(--text-secondary); font-size: 12px; font-weight: 500; }
.config-form .el-input__inner,
.config-form .el-textarea__inner,
.config-form .el-select .el-input__inner {
  background: var(--bg-elevated);
  border-color: var(--border-subtle);
  color: var(--text-primary);
}
.config-form .el-input__inner:focus,
.config-form .el-textarea__inner:focus {
  border-color: var(--accent);
}
.config-form .el-select__tags { background: transparent; }
.config-empty {
  text-align: center;
  padding: 40px 16px;
  color: var(--text-muted);
  font-size: 13px;
}
.config-empty-inner { text-align: center; }
.config-hint { font-size: 11px; margin-top: 6px; color: var(--text-muted); }
.preset-prompt-display {
  padding: 8px 10px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
}
.var-hint-row {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
  margin-top: 4px;
}
.var-hint-label {
  font-size: 11px;
  color: var(--text-muted);
  flex-shrink: 0;
}
.var-chip {
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--accent);
  background: var(--accent-glow);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 3px;
  padding: 1px 6px;
  cursor: pointer;
  transition: all 0.1s;
}
.var-chip:hover {
  background: rgba(59, 130, 246, 0.2);
}
.start-var-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.start-var-row {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* Variable ref chip */
.var-ref {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 7px;
  border-radius: 4px;
  font-size: 11px;
  font-family: var(--font-mono);
  background: rgba(59,130,246,0.10);
  color: #60a5fa;
  border: 1px solid rgba(59,130,246,0.15);
}
.var-ref .var-slash { opacity: 0.5; }

/* Output preview */
.output-preview {
  padding: 8px 10px;
  background: rgba(16,185,129,0.06);
  border: 1px solid rgba(16,185,129,0.12);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  gap: 6px;
}
.output-preview .output-var {
  font-size: 11px;
  font-family: var(--font-mono);
  color: #34d399;
}

/* Collapsible section */
.collapse {
  margin-top: 4px;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  overflow: hidden;
}
.collapse-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  cursor: pointer;
  background: var(--bg-elevated);
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
}
.collapse-arrow {
  font-size: 10px;
  transition: transform .2s;
}
.collapse.open .collapse-arrow { transform: rotate(90deg); }
.collapse-body {
  padding: 10px;
  display: none;
}
.collapse.open .collapse-body { display: block; }

/* Condition branch card */
.branch-card {
  border-left: 3px solid var(--n-condition);
  background: rgba(245,158,11,0.04);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  padding: 8px 10px;
  margin-bottom: 6px;
}
.branch-card.branch-else {
  border-left-color: #94a3b8;
  background: rgba(148,163,184,0.04);
}
.branch-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 5px;
}
.branch-tag {
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 3px;
  font-family: var(--font-mono);
}
.rule-row {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 4px;
  font-size: 11px;
}
.branch-target {
  display: flex;
  align-items: center;
}

/* Branch row (human_intervention) */
.branch-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

/* Test area */
.test-area {
  margin-top: 16px;
  border-top: 1px solid var(--border-subtle);
  padding-top: 12px;
}
.test-header {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 8px;
}
.test-messages {
  max-height: 200px;
  overflow-y: auto;
  margin-bottom: 8px;
}
.test-msg {
  padding: 6px 8px;
  border-radius: var(--radius-sm);
  margin-bottom: 4px;
  font-size: 12px;
}
.test-msg.msg-user {
  background: rgba(59,130,246,0.08);
  border-left: 2px solid var(--accent);
}
.test-msg.msg-assistant {
  background: rgba(16,185,129,0.06);
  border-left: 2px solid #10b981;
}
.test-msg.msg-node {
  background: rgba(148,163,184,0.04);
  border-left: 2px solid var(--text-muted);
}
.test-msg.msg-system {
  background: rgba(6,182,212,0.06);
  border-left: 2px solid var(--n-llm);
}
.test-msg.msg-error {
  background: rgba(239,68,68,0.06);
  border-left: 2px solid var(--status-error);
}
.msg-label {
  font-size: 10px;
  font-weight: 600;
  color: var(--text-muted);
  margin-bottom: 2px;
}
.msg-content {
  color: var(--text-primary);
  font-size: 12px;
  line-height: 1.5;
  word-break: break-word;
}
.test-input-row {
  display: flex;
  gap: 6px;
}
.intervention-card {
  padding: 10px;
  background: rgba(236,72,153,0.06);
  border: 1px solid rgba(236,72,153,0.15);
  border-radius: var(--radius-sm);
  margin-bottom: 6px;
}
.intervention-card h4 {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}
.branch-buttons {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.countdown {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 6px;
}

/* ============================ BOTTOM CONSOLE ============================ */
.console {
  height: 200px;
  background: var(--bg-surface);
  border-top: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}
.console-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  height: 34px;
  border-bottom: 1px solid var(--border-subtle);
}
.console-tabs {
  display: flex;
  gap: 2px;
}
.console-tab {
  padding: 4px 12px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all .12s;
}
.console-tab.active {
  color: var(--text-primary);
  border-bottom-color: var(--accent);
}
.console-tab .tab-count {
  font-size: 10px;
  padding: 0 5px;
  border-radius: 8px;
  background: var(--bg-elevated);
  color: var(--text-muted);
  margin-left: 4px;
}
.console-tab.active .tab-count {
  background: var(--accent-glow);
  color: var(--accent);
}
.console-actions {
  display: flex;
  gap: 6px;
}
.console-action {
  font-size: 11px;
  color: var(--text-muted);
  cursor: pointer;
  padding: 3px 8px;
  border-radius: 4px;
  transition: all .12s;
  background: none;
  border: none;
  font-family: inherit;
}
.console-action:hover { color: var(--text-primary); background: var(--bg-hover); }
.console-body {
  flex: 1;
  overflow-y: auto;
  padding: 8px 16px;
  font-family: var(--font-mono);
  font-size: 12px;
  line-height: 1.7;
}

/* Log entries */
.log-line {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 1px 0;
}
.log-time {
  color: var(--text-muted);
  flex-shrink: 0;
  font-size: 11px;
}
.log-tag {
  font-size: 10px;
  font-weight: 700;
  padding: 0 5px;
  border-radius: 3px;
  flex-shrink: 0;
  min-width: 80px;
  text-align: center;
}
.log-tag.node_start { background: rgba(59,130,246,0.15); color: #60a5fa; }
.log-tag.node_end { background: rgba(16,185,129,0.12); color: #34d399; }
.log-tag.node_output { background: rgba(6,182,212,0.12); color: #22d3ee; }
.log-tag.log_update { background: rgba(148,163,184,0.10); color: #94a3b8; }
.log-tag.human { background: rgba(236,72,153,0.12); color: #f472b6; }
.log-tag.final { background: rgba(16,185,129,0.15); color: #10b981; }
.log-tag.error { background: rgba(239,68,68,0.12); color: #f87171; }
.log-text {
  color: var(--text-secondary);
  font-size: 12px;
}
.log-text .log-var { color: #60a5fa; }
.log-text .log-val { color: #2dd4bf; }
.log-text .log-node { color: var(--text-primary); font-weight: 600; }
.log-empty {
  color: var(--text-muted);
  font-size: 12px;
  padding: 20px 0;
  text-align: center;
  font-family: var(--font-sans);
}

/* ============================ ANIMATIONS ============================ */
@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: .5; transform: scale(1.3); }
}

/* ============================ SCROLLBAR ============================ */
.wf-editor ::-webkit-scrollbar,
.workflow-page ::-webkit-scrollbar { width: 6px; height: 6px; }
.wf-editor ::-webkit-scrollbar-track,
.workflow-page ::-webkit-scrollbar-track { background: transparent; }
.wf-editor ::-webkit-scrollbar-thumb,
.workflow-page ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08); border-radius: 3px; }
.wf-editor ::-webkit-scrollbar-thumb:hover,
.workflow-page ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.14); }

/* ============================ DETAIL VIEW ============================ */
.detail-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px 32px;
  border-bottom: 1px solid var(--border-subtle);
}
.detail-title { flex: 1; }
.detail-title h2 { font-size: 20px; font-weight: 700; color: var(--text-primary); margin: 0; }
.page-desc { font-size: 13px; color: var(--text-muted); margin-top: 4px; }
.header-actions { display: flex; gap: 8px; }
.loading-tip { text-align: center; padding: 40px; color: var(--text-muted); font-size: 14px; }

/* ===== Detail View (editor-matching layout) ===== */
.detail-view {
  flex: 1;
  display: flex;
  gap: 0;
  overflow: hidden;
  min-height: 0;
}
.detail-canvas-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}
.detail-canvas-toolbar {
  padding: 8px 16px;
  border-bottom: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}
.detail-canvas-grid {
  flex: 1;
  position: relative;
  background: var(--bg-base);
  background-image:
    linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
  background-size: 32px 32px;
  overflow: hidden;
  min-height: 0;
}
.detail-canvas-inner {
  position: relative;
  transform-origin: 0 0;
}
.detail-graph-preview { display: none; }
.detail-edges-svg {
  position: absolute;
  left: 0;
  top: 0;
  pointer-events: none;
}
.detail-edge-path {
  fill: none;
  stroke: rgba(255,255,255,0.24);
  stroke-width: 1.5;
  marker-end: url(#detail-arrow);
}
.detail-node {
  cursor: default;
  pointer-events: auto;
}
.detail-nodes-layer {
  position: absolute;
  left: 0;
  top: 0;
  pointer-events: none;
}
.detail-nodes-layer .wf-node {
  pointer-events: auto;
}
.detail-empty-canvas {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  font-size: 14px;
  pointer-events: none;
}
.detail-side-panel {
  width: 320px;
  flex-shrink: 0;
  border-left: 1px solid var(--border-subtle);
  background: var(--bg-surface);
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.detail-side-section h3 {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 12px;
}
.info-row {
  display: flex;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-subtle);
  font-size: 13px;
}
.info-row:last-child { border-bottom: none; }
.info-row .label { color: var(--text-muted); width: 100px; flex-shrink: 0; }
.info-row .value { color: var(--text-primary); }
.node-list { display: flex; flex-direction: column; gap: 6px; }
.node-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-left: 3px solid var(--node-color, var(--accent));
  border-radius: var(--radius-sm);
  transition: background 0.15s;
}
.node-item:hover { background: var(--bg-hover); }
.node-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.node-info {
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.node-info .node-name { font-size: 13px; font-weight: 500; color: var(--text-primary); }
.node-info .node-type { font-size: 11px; color: var(--text-muted); }
.empty-text { font-size: 13px; color: var(--text-muted); text-align: center; padding: 20px; }

/* ============================ LIST VIEW ============================ */
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 24px 32px;
  border-bottom: 1px solid var(--border-subtle);
}
.page-header h2 { font-size: 20px; font-weight: 700; color: var(--text-primary); margin: 0; }
.search-input { width: 240px; }
.search-input .el-input__inner {
  background: var(--bg-elevated);
  border-color: var(--border-subtle);
  color: var(--text-primary);
}
.kb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  padding: 24px 32px;
}
.kb-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  overflow: hidden;
  cursor: pointer;
  transition: all .2s;
}
.kb-card:hover {
  border-color: var(--border-strong);
  transform: translateY(-2px);
  box-shadow: var(--shadow-card);
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px 0;
}
.kb-icon {
  width: 40px; height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 20px;
}
.card-actions { position: relative; }
.more-btn { color: var(--text-muted); }
.more-btn:hover { color: var(--text-primary); }
.card-body { padding: 12px 16px 14px; }
.kb-name { font-size: 15px; font-weight: 600; color: var(--text-primary); margin: 0 0 4px; }
.kb-meta { font-size: 11px; color: var(--text-muted); margin: 0 0 6px; }
.kb-desc { font-size: 12px; color: var(--text-secondary); margin: 0; line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.card-footer {
  display: flex;
  gap: 16px;
  padding: 10px 16px;
  border-top: 1px solid var(--border-subtle);
}
.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-muted);
}
.add-card {
  border: 2px dashed var(--border-default);
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}
.add-card:hover { border-color: var(--accent); }
</style>
