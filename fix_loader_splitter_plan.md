# 修复 Document Loaders 和 Splitters

## 一、总结

修复 2 个问题：添加 UnstructuredReader 支持 PDF 加载，修复 3 个 Splitter Bug。

## 二、变更清单

### 新增

1. **`app/utils/document_loaders.py`** — +`UnstructuredPDFLoader` class, 注册到 LOADER_MAP

### 修改

2. **`app/utils/chinese_splitter.py`** — 3 个 Bug 修复
3. **`requirements.txt`** — +`unstructured[pdf]`

## 三、详细修改

### 3.1 新增 `UnstructuredPDFLoader`（document_loaders.py）

在 `PyPDF2Loader` 后插入：

```python
class UnstructuredPDFLoader(BaseLoader):
    def load(self, file_path: str) -> str:
        try:
            from unstructured.partition.pdf import partition_pdf
            elements = partition_pdf(filename=file_path)
            return "\n\n".join(str(e) for e in elements)
        except ImportError:
            raise ImportError("unstructured[pdf] not installed")
```

LOADER_MAP PDF 条目更新：

```python
".pdf": [("pymupdf", PyMuPDFLoader), ("pypdf2", PyPDF2Loader), ("unstructured", UnstructuredPDFLoader)],
```

工厂 `get_loader()` 已支持 fallback 链：尝试 pymupdf → pypdf2 → unstructured → raise。

### 3.2 `SemanticSplitter` 自动构建 embed_model（chinese_splitter.py）

构造函数中从 `config.settings` 读取配置自动创建 DashScopeEmbedding：

```python
class SemanticSplitter:
    def __init__(self, buffer_size: int = 1, chunk_size: int = 512, chunk_overlap: int = 50):
        self.buffer_size = buffer_size
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embed_model = None
        try:
            from config import settings
            from llama_index.embeddings.dashscope import DashScopeEmbedding
            self.embed_model = DashScopeEmbedding(
                model_name=settings.LLM_EMBEDDING_MODEL,
                api_key=settings.DASHSCOPE_API_KEY,
            )
        except ImportError:
            pass
```

`split_text()` 中已有 `if self.embed_model is None` 回退逻辑，不修改。

### 3.3 `TokenTextSplitter` 无限循环修复（chinese_splitter.py）

```python
class TokenTextSplitter:
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        if chunk_overlap >= chunk_size:
            chunk_overlap = chunk_size // 2
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> List[str]:
        chunks = []
        start = 0
        text_len = len(text)
        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            chunk = text[start:end]
            chunks.append(chunk)
            if end == text_len:
                break
            start = end - self.chunk_overlap
        return chunks
```

### 3.4 `SentenceSplitter` 基于字符数重叠修复（chinese_splitter.py）

```python
# 重叠逻辑改为按 chunk_overlap 字符数累积倒数句子
if self.chunk_overlap > 0 and current_chunk:
    overlap_chars = []
    overlap_len = 0
    for s in reversed(current_chunk):
        if overlap_len + len(s) > self.chunk_overlap and overlap_chars:
            break
        overlap_chars.insert(0, s)
        overlap_len += len(s)
    current_chunk = overlap_chars
    current_length = overlap_len
else:
    current_chunk = []
    current_length = 0
```

### 3.5 requirements.txt

```txt
unstructured[pdf]>=0.15.0
```

## 四、验证

1. `pip install unstructured[pdf]` → 安装成功
2. `python -c "from app.utils.chinese_splitter import TokenTextSplitter, SentenceSplitter, SemanticSplitter"`
3. 上传 PDF 文件 → 自动触发 UnstructuredReader（如果 pymupdf 不可用）
4. 测试 `chunk_overlap >= chunk_size` → 自动降为 `chunk_size // 2`，不死循环
