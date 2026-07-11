# RAG 流程完善计划

## 一、总结

基于用户确认的技术选型，完善 AgentFlow RAG 管道：文档加载（多 Loader 按后缀选择）、中文友好切分器（3种）、批量嵌入、检索前优化（3种可选）、Rerank、LLM 切换、完整 RAG 问答端点。

## 二、当前状态分析

| 环节 | 当前状态 | 问题 |
|------|----------|------|
| 文档加载 | `file_parser.py` 简单实现 | 仅 PyPDF2/Python-docx/openpyxl，无 PyMuPDF/Unstructured/Pandas |
| 切分器 | 固定字符切分 | 无语义边界，无中文友好支持，无 SemanticSplitter |
| 嵌入 | 逐条嵌入 | 性能慢，未使用批量 API |
| 检索 | 直接向量检索 | 无 HyDE/Query Rewrite/Multi-Query |
| Rerank | 无 | 无精排，直接返回 ANN 结果 |
| LLM | 固定 qwen-plus | 不可切换 |
| RAG 问答 | 无端点 | 只检索不生成回答 |

## 三、技术选型确认

| 环节 | 选择 | 原因 |
|------|------|------|
| PDF Loader | PyMuPDFReader (fitz) 为主，PyPDF2 备用 | PyMuPDF 提取精度更高，支持表格 |
| Word Loader | python-docx | 成熟稳定 |
| CSV Loader | pandas | 支持复杂表格解析 |
| Markdown/HTML/ipynb | 原生解析 + markdown-it-py | 轻量高效 |
| 切分器 | TokenTextSplitter + SentenceSplitter + SemanticSplitterNodeParser | 覆盖不同场景 |
| 中文边界 | 自定义 `chinese_sentence_boundary` | 适配中文标点 |
| 嵌入 | 批量 batch_size=20 | 平衡速度与稳定性 |
| 检索优化 | HyDE / Query Rewrite / Multi-Query（用户选择） | 多策略可选 |
| Rerank | DashScope gte-rerank-v2 | 统一账号，中文效果好 |
| LLM | qwen-plus / qwen-max / qwen-turbo（用户选择） | 动态切换 |
| 向量存储 | Milvus（主）+ FAISS（回退） | 保持不变 |

## 四、变更文件清单

### 新增文件

1. **`app/utils/document_loaders.py`** — 文档加载器工厂，按后缀选择不同 Loader
2. **`app/utils/chinese_splitter.py`** — 中文友好切分器，含 `chinese_sentence_boundary`
3. **`app/services/rag_service.py`** — RAG 问答服务，检索前优化 + Rerank + LLM 生成
4. **`app/schemas/rag.py`** — RAG 相关 schema（RAGRequest, RAGResponse）
5. **`app/api/v1/rag.py`** — RAG 问答 API 路由

### 修改文件

1. **`app/utils/file_parser.py`** — 重构，调用新的 Loader 工厂
2. **`app/utils/text_splitter.py`** — 替换为中文友好切分器
3. **`app/services/chunk_service.py`** — 支持多种切分器选择
4. **`app/services/embedding_service.py`** — 支持批量嵌入
5. **`app/services/llm_service.py`** — 支持动态模型选择、Rerank API、HyDE
6. **`app/tasks/knowledge_tasks.py`** — 使用批量嵌入，支持切分器选择
7. **`app/api/v1/knowledge.py`** — 更新 import/confirm 支持切分器参数
8. **`requirements.txt`** — 添加新依赖（fitz, pandas, markdown-it-py, llama-index-core）
9. **`.env`** — 添加 Rerank 模型配置

## 五、详细实现步骤

### 5.1 文档加载器重构 (`app/utils/document_loaders.py`)

```python
# 工厂模式，按后缀分发
LOADER_MAP = {
    ".pdf": ["pymupdf", "pypdf2"],
    ".docx": ["docx"],
    ".csv": ["pandas"],
    ".md": ["markdown"],
    ".html": ["html"],
    ".ipynb": ["ipynb"],
    ...
}

class DocumentLoaderFactory:
    @staticmethod
    def get_loader(file_path: str, loader_type: str = None) -> BaseLoader:
        ...

class PyMuPDFLoader:
    def load(self, file_path: str) -> str:
        # fitz 提取，保留表格结构
        ...

class PandasCSVLoader:
    def load(self, file_path: str) -> str:
        # pandas 读取，转为文本
        ...
```

### 5.2 中文友好切分器 (`app/utils/chinese_splitter.py`)

```python
def chinese_sentence_boundary(text: str) -> list[str]:
    """中文句子边界识别，按句号/问号/感叹号/换行分割"""
    ...

class ChineseSentenceSplitter:
    """按句子边界切分，chunk_size/chunk_overlap 控制"""
    ...

class ChineseTokenSplitter:
    """按 Token 切分（粗略按字符）"""
    ...
```

### 5.3 RAG 服务 (`app/services/rag_service.py`)

```python
class RAGService:
    @staticmethod
    async def query(
        query: str,
        kb_id: int,
        query_optimizer: str = "hyde",  # hyde / rewrite / multi_query / none
        llm_model: str = "qwen-plus",
        top_k: int = 10,
        rerank_top_n: int = 5,
        temperature: float = 0.7
    ) -> RAGResponse:
        # 1. Query 优化（HyDE/Rewrite/Multi-Query）
        # 2. 向量检索
        # 3. Rerank（gte-rerank-v2）
        # 4. Prompt 拼接
        # 5. LLM 生成
        ...
```

### 5.4 LLM 服务增强 (`app/services/llm_service.py`)

```python
class LLMService:
    # 新增方法
    async def hyde(self, query: str) -> str:
        """生成假设答案文档"""
        ...
    
    async def query_rewrite(self, query: str) -> list[str]:
        """改写为多个查询"""
        ...
    
    async def multi_query(self, query: str) -> list[str]:
        """生成多个子问题"""
        ...
    
    async def rerank(self, query: str, documents: list[str]) -> list[tuple[int, float]]:
        """调用 DashScope gte-rerank-v2"""
        ...
    
    async def chat_with_model(self, model: str, messages: list[dict], ...) -> str:
        """动态模型调用"""
        ...
```

### 5.5 后台任务优化 (`app/tasks/knowledge_tasks.py`)

```python
# 批量嵌入逻辑
async def process_document(doc_id, config):
    ...
    # 切分（支持选择切分器）
    chunks = await ChunkService.split(text, splitter_type=config.splitter_type, ...)
    
    # 批量嵌入（batch_size=20）
    for i in range(0, len(chunks), 20):
        batch_chunks = chunks[i:i+20]
        embeddings = await EmbeddingService.embed_texts(batch_chunks)
        await EmbeddingService.store_embeddings(batch_ids, embeddings, kb_id, doc_id)
        await db.commit()  # 批次提交
```

### 5.6 API 路由 (`app/api/v1/rag.py`)

```python
@router.post("/query", response_model=RAGResponse)
async def rag_query(
    req: RAGRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return await RAGService.query(req.query, req.kb_id, ...)
```

### 5.7 Schema (`app/schemas/rag.py`)

```python
class RAGRequest(BaseModel):
    query: str
    kb_id: int
    query_optimizer: str = Field("hyde", description="hyde / rewrite / multi_query / none")
    llm_model: str = Field("qwen-plus", description="qwen-plus / qwen-max / qwen-turbo")
    top_k: int = 10
    rerank_top_n: int = 5
    temperature: float = 0.7

class RAGResponse(BaseModel):
    answer: str
    sources: list[KnowledgeSearchResult]
    latency: float
```

### 5.8 新增依赖 (`requirements.txt`)

```
fitz>=0.20.0           # PyMuPDF
pandas>=2.2.0          # CSV 解析
markdown-it-py>=3.0.0  # Markdown 解析
llama-index-core>=0.11.0  # SemanticSplitterNodeParser
```

### 5.9 环境配置 (`.env`)

```env
# Rerank
RERANK_MODEL=gte-rerank-v2
RERANK_API_KEY=${DASHSCOPE_API_KEY}
RERANK_API_BASE=${DASHSCOPE_BASE_URL}

# 默认切分器
DEFAULT_SPLITTER=sentence
DEFAULT_CHUNK_SIZE=512
DEFAULT_CHUNK_OVERLAP=50
```

## 六、验证步骤

1. **安装依赖**: `pip install fitz pandas markdown-it-py llama-index-core`
2. **重启服务**: `uvicorn main:app --reload --port 8000`
3. **测试文档加载**: 上传不同格式文件（PDF/Word/CSV/Markdown），验证解析结果
4. **测试切分器**: 切换不同切分器类型，验证切分效果
5. **测试 RAG 问答**: 
   - `POST /api/v1/rag/query` 传入不同参数
   - 验证 HyDE/Query Rewrite/Multi-Query 效果
   - 验证不同 LLM 模型切换
6. **性能测试**: 上传大文档，验证批量嵌入速度提升

## 七、假设与决策

| 决策 | 假设 |
|------|------|
| 优先使用 PyMuPDF | 用户需要高质量 PDF 解析，PyMuPDF 比 PyPDF2 更好 |
| SemanticSplitter 需要 LlamaIndex | LlamaIndex 的实现最成熟，无需自己造轮子 |
| Rerank 使用 DashScope | 用户已有 DashScope 账号，统一管理 |
| 批量大小 20 | 平衡 API 限流与请求效率 |
| 前端下拉选择 | 用户需要灵活配置检索策略 |
