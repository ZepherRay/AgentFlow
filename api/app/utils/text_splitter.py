import re
from typing import List


def chinese_sentence_boundary(text: str) -> List[str]:
    """Split Chinese text by sentence boundaries (。！？；newline)."""
    pattern = r"(?<=[。！？；\n])"
    sentences = re.split(pattern, text)
    sentences = [s.strip() for s in sentences if s.strip()]
    return sentences


class TokenTextSplitter:
    """Fixed-size token chunking (by character count for CJK)."""

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


class SentenceSplitter:
    """Split by sentence boundaries, merge up to chunk_size."""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50,
                 sentence_splitter=None):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.sentence_splitter = sentence_splitter or chinese_sentence_boundary

    def split_text(self, text: str) -> List[str]:
        sentences = self.sentence_splitter(text)
        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_len = len(sentence)
            if current_length + sentence_len > self.chunk_size and current_chunk:
                chunk_text = "".join(current_chunk)
                chunks.append(chunk_text)
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
            current_chunk.append(sentence)
            current_length += sentence_len

        if current_chunk:
            chunks.append("".join(current_chunk))
        return chunks


class SemanticSplitter:
    """Semantic chunking via DashScope embedding + llama_index."""

    def __init__(self, buffer_size: int = 1, chunk_size: int = 512,
                 chunk_overlap: int = 50):
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

    def split_text(self, text: str) -> List[str]:
        if self.embed_model is None:
            splitter = SentenceSplitter(chunk_size=self.chunk_size)
            return splitter.split_text(text)
        try:
            from llama_index.core.node_parser import SemanticSplitterNodeParser
            from llama_index.core import Document
            node_parser = SemanticSplitterNodeParser(
                embed_model=self.embed_model,
                buffer_size=self.buffer_size,
            )
            doc = Document(text=text)
            nodes = node_parser.get_nodes_from_documents([doc])
            return [node.text for node in nodes]
        except ImportError:
            splitter = SentenceSplitter(chunk_size=self.chunk_size)
            return splitter.split_text(text)


SPLITTER_TYPES = {
    "token": TokenTextSplitter,
    "sentence": SentenceSplitter,
    "semantic": SemanticSplitter,
}


def get_splitter(splitter_type: str = "sentence", **kwargs):
    if splitter_type not in SPLITTER_TYPES:
        raise ValueError(f"Unknown splitter type: {splitter_type}")
    return SPLITTER_TYPES[splitter_type](**kwargs)


# ── High-level convenience wrappers ──

def split_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    splitter = TokenTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
    return splitter.split_text(text)


def split_by_paragraph(text: str) -> list[str]:
    return [p.strip() for p in text.split("\n\n") if p.strip()]


def split_by_sentence(text: str) -> list[str]:
    return chinese_sentence_boundary(text)
