# Plan: 导入文档向量化 → Milvus 存储 + 检索修复

## Summary
文档确认导入后，后台线程 `process_document` 已实现分块→向量化→存储到 Milvus。但当前 `vector_store.py` 的 MilvusClient 使用方式有 3 个问题：①未调用 `load_collection()` 导致 search 500；②索引用 IVF_FLAT+L2 而非更优的 HNSW+COSINE；③未持久化 chunk 内容到 Milvus。

本计划：重写 `vector_store.py` 对齐用户提供的 MilvusClient 参考代码（Schema→Index→Create→Insert→Flush→Load→Search→Release），修复 search 500。

## Current State
| 文件 | 现状 |
|------|------|
| `vector_store.py` | MilvusClient 简化创建，IVF_FLAT+L2，无 `load_collection()`/`flush()`/`release_collection()` |
| `embedding_service.py` | 正确调用 embed + store + search，search 依赖 SQL JOIN 拿 content |
| `knowledge_tasks.py` | process_document 已完整（parse→split→chunk→embed→store） |
| `schemas/knowledge.py` | KnowledgeSearchResult 已有 content/score/filename 等 |
| `.env` | 已配 MILVUS_HOST/PORT/USER/PASSWORD/COLLECTION，dimension=1024 |

## Changes

### 1. `app/utils/vector_store.py` — 重写 MilvusVectorStore

**Why**: 对齐 MilvusClient 标准用法（Schema→Index→Create→Insert→Flush→Load→Search→Release），解决 search 500。

**What**:
- 使用 `MilvusClient.create_schema(enable_dynamic_field=True)` + `schema.add_field()` 显式定义字段
  - `id` (INT64, primary, auto_id=False)
  - `kb_id` (INT64)
  - `doc_id` (INT64)
  - `text` (VARCHAR, max_length=65535) — chunk 内容，减少 SQL 依赖
  - `embedding` (FLOAT_VECTOR, dim=dimension)
- 使用 `MilvusClient.prepare_index_params()` + `add_index()` 建 HNSW 索引 (M=16, efConstruction=128, metric_type=COSINE)
- `create_collection()` 同时传入 schema + index_params
- `add()` 插入含 `text` 字段的完整记录，后调 `client.flush()`
- `search()` 前调 `client.load_collection()`，后调 `client.release_collection()`
- `search()` 的 `output_fields` 含 `["text", "kb_id", "doc_id", "id"]`
- `delete_by_ids()` 不变
- `clear()` 不变

### 2. `app/services/embedding_service.py` — 传 text 到 vector store

**Why**: Milvus 新增 `text` 字段，存 chunk 内容方便 search 直接返回。

**What**: `store_embeddings()` 接受 `texts: list[str]` 参数，传给 `store.add()`。

### 3. `app/utils/vector_store.py` `add()` — 接收 texts

**Why**: 配合 embedding_service 存储文本到 Milvus。

**What**: `add()` 参数加 `texts: list[str] | None = None`，写入 records 时包含 `"text"`。

### 4. `app/tasks/knowledge_tasks.py` — 传 texts

**Why**: process_document 调用 store_embeddings 时需传 chunk 原文。

**What**: `store_embeddings(batch_chunk_ids, embeddings, kb_id, doc_id, texts=batch_chunks)`。

### 5. 补：Milvus collection 重建

**Why**: 现有 `agentflow_chunks` collection schema 不兼容新字段（无 text 字段），需要 drop 重建。

**How**: 在 `MilvusVectorStore.__init__` 中自动检测旧 schema（无 text 字段），自动 drop + recreate。

## Verification
1. 启动后端: `uvicorn main:app --reload --port 8000`
2. 上传一个 .txt 文件 → 下一步配置切割器 → 下一步预览 → 下一步确认导入
3. 等待后台处理完成（文档状态从 PARSING → CHUNKING → EMBEDDING → COMPLETED）
4. 在 RAG 问答界面输入问题 → 验证返回 AI 答案 + 参考来源
5. 检查 Milvus：通过 Attu 查看 `agentflow_chunks` collection 是否有向量数据

## Rollback
若出错，直接删 `agentflow_chunks` collection（Attu 中操作），后端会自动重建。
