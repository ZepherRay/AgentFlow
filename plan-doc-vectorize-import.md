# Plan: 导入文档向量化 → Milvus 存储完整流程修复

## Summary
文档上传后字符数和知识条数都是 0，说明后台 `process_document` 线程没有正确执行。需要：①确保文档解析成功；②确保向量化流程完整；③确保 Milvus 存储成功；④前端显示正确状态。

## Current State
| 文件 | 现状 |
|------|------|
| `knowledge_tasks.py` | `process_document` 流程完整（parse→split→chunk→embed→store），但可能因依赖缺失失败 |
| `document_loaders.py` | 支持 .docx，但需要 `python-docx` 包 |
| `vector_store.py` | 已重写为 MilvusClient 标准用法（Schema→Index→Load→Search→Release） |
| `embedding_service.py` | `store_embeddings` 支持 texts 参数 |
| `knowledge_service.py` | `confirm_import` 启动后台线程 |
| `.env` | 已配 Milvus 连接和 DashScope API Key |

## Root Cause Analysis
1. **`process_document` 失败无日志**：异常只 print，不写入日志文件
2. **依赖缺失**：`.docx` 文件需要 `python-docx`，可能未安装
3. **状态更新失败**：异常时状态设为 FAILED，但前端可能没刷新

## Changes

### 1. `app/tasks/knowledge_tasks.py` — 增强日志和错误处理

**Why**: 让失败原因可追踪。

**What**:
- 用 `logger.exception()` 替代 `print()`
- 记录完整执行日志（开始、每个阶段、结束）
- 确保事务正确提交

### 2. `app/services/knowledge_service.py` — `delete_document_post` 加 Milvus 清理

**Why**: 删除文档时同时清理 Milvus 向量，保持一致性。

**What**: `delete_document_post` 中收集 chunk_ids，调用 `store.delete_by_ids()`

### 3. 安装缺失依赖

**Why**: `.docx` 文件需要 `python-docx`。

**What**: `pip install python-docx`

### 4. `app/api/v1/knowledge.py` — 修复 reprocess_document 缺少 import

**Why**: `delete` 未导入，导致重新处理失败。

**What**: 添加 `from sqlalchemy import select, delete`

### 5. 前端 — KnowledgeEdit.vue — 添加文档状态轮询

**Why**: 后台处理完成后前端能自动刷新。

**What**: `confirm_import` 后启动轮询，检查文档状态，完成后刷新列表。

## Verification
1. 安装依赖: `pip install python-docx`
2. 重启后端: `uvicorn main:app --reload --port 8000`
3. 上传 .docx 文件 → 下一步 → 确认导入
4. 查看日志: `agentflow/logs/app.log` 确认 process_document 执行
5. 等待文档状态变为 COMPLETED
6. 确认字符数和知识条数 > 0
7. RAG 问答验证检索正常
