import numpy as np
from pathlib import Path
from config import settings


class FAISSVectorStore:
    """FAISS 向量存储封装"""

    def __init__(self, dimension: int = 1536):
        self.dimension = dimension
        self.index = None
        self.id_map: dict[int, int] = {}
        self._init_index()

    def _init_index(self):
        try:
            import faiss
            self.index = faiss.IndexFlatL2(self.dimension)
        except ImportError:
            raise ImportError("faiss-cpu not installed")

    def add(self, embeddings: np.ndarray, ids: list[int]):
        if self.index is None:
            self._init_index()
        start_idx = self.index.ntotal
        self.index.add(embeddings)
        for i, chunk_id in enumerate(ids):
            self.id_map[start_idx + i] = chunk_id

    def search(self, query: np.ndarray, k: int = 5) -> tuple[np.ndarray, np.ndarray]:
        if self.index is None:
            self._init_index()
        if self.index.ntotal == 0:
            return np.array([[-1] * k]), np.array([[0.0] * k])
        k = min(k, self.index.ntotal)
        return self.index.search(query, k)

    def save(self, path: str):
        try:
            import faiss
            faiss.write_index(self.index, path)
        except ImportError:
            pass

    def load(self, path: str):
        try:
            import faiss
            self.index = faiss.read_index(path)
        except ImportError:
            pass


_vector_store: FAISSVectorStore | None = None


def get_vector_store() -> FAISSVectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = FAISSVectorStore(dimension=settings.VECTOR_DIMENSION)
        index_path = Path(settings.VECTOR_FAISS_INDEX_PATH)
        if index_path.exists():
            _vector_store.load(str(index_path))
    return _vector_store