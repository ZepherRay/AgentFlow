import numpy as np
from pathlib import Path
from typing import Any
from config import settings
from loguru import logger


class BaseVectorStore:
    def add(self, embeddings: np.ndarray, ids: list[int], kb_id: int | None = None, doc_id: int | None = None, texts: list[str] | None = None): ...
    def search(self, query: np.ndarray, top_k: int = 5, kb_id: int | None = None) -> tuple[np.ndarray, np.ndarray]: ...
    def delete_by_ids(self, ids: list[int]): ...
    def clear(self): ...


class MilvusVectorStore(BaseVectorStore):

    def __init__(self, host: str, port: int, user: str, password: str, db: str,
                 collection_name: str, dimension: int):
        from pymilvus import MilvusClient, DataType
        self.dimension = dimension
        self.collection_name = collection_name
        self.db = db

        self.client = MilvusClient(
            uri=f"http://{host}:{port}",
            db_name=db,
            user=user,
            password=password,
        )
        logger.info(f"Milvus connected: {host}:{port}/{db}")

        if not self.client.has_collection(collection_name=collection_name):
            self._create_collection()
        else:
            self._check_and_migrate_schema()

    def _create_collection(self):
        from pymilvus import MilvusClient, DataType
        schema = MilvusClient.create_schema(
            auto_id=False,
            enable_dynamic_field=True,
        )
        schema.add_field(
            field_name="id",
            datatype=DataType.INT64,
            is_primary=True,
        )
        schema.add_field(
            field_name="kb_id",
            datatype=DataType.INT64,
        )
        schema.add_field(
            field_name="doc_id",
            datatype=DataType.INT64,
        )
        schema.add_field(
            field_name="text",
            datatype=DataType.VARCHAR,
            max_length=65535,
        )
        schema.add_field(
            field_name="embedding",
            datatype=DataType.FLOAT_VECTOR,
            dim=self.dimension,
        )

        index_params = MilvusClient.prepare_index_params()
        index_params.add_index(
            field_name="embedding",
            index_type="HNSW",
            metric_type="COSINE",
            params={
                "M": 16,
                "efConstruction": 128,
            },
        )

        self.client.create_collection(
            collection_name=self.collection_name,
            schema=schema,
            index_params=index_params,
        )
        logger.info(f"Milvus collection created: {self.collection_name}")

    def _check_and_migrate_schema(self):
        try:
            desc = self.client.describe_collection(collection_name=self.collection_name)
            fields = {f["name"] for f in desc.get("fields", [])}
            if "text" not in fields:
                logger.info(f"Migrating collection {self.collection_name}: dropping old schema")
                self.client.drop_collection(collection_name=self.collection_name)
                self._create_collection()
        except Exception as e:
            logger.warning(f"Schema check failed, recreate: {e}")
            self.client.drop_collection(collection_name=self.collection_name)
            self._create_collection()

    def add(self, embeddings: np.ndarray, ids: list[int], kb_id: int | None = None, doc_id: int | None = None, texts: list[str] | None = None):
        if len(ids) == 0:
            return
        kb_id = kb_id or 0
        doc_id = doc_id or 0
        records = []
        for i, chunk_id in enumerate(ids):
            record = {
                "id": int(chunk_id),
                "kb_id": int(kb_id),
                "doc_id": int(doc_id),
                "embedding": embeddings[i].astype(np.float32).tolist(),
            }
            if texts and i < len(texts):
                record["text"] = texts[i][:65535]
            records.append(record)
        self.client.insert(collection_name=self.collection_name, data=records)
        self.client.flush(collection_name=self.collection_name)
        logger.info(f"Milvus inserted {len(ids)} vectors into {self.collection_name}")

    def search(self, query: np.ndarray, top_k: int = 5, kb_id: int | None = None) -> tuple[np.ndarray, np.ndarray]:
        try:
            collection_stats = self.client.get_collection_stats(collection_name=self.collection_name)
            if collection_stats["row_count"] == 0:
                return np.array([[-1.0] * top_k]), np.array([[0] * top_k])
        except Exception as e:
            logger.warning(f"Collection stats failed: {e}")
            return np.array([[-1.0] * top_k]), np.array([[0] * top_k])

        self.client.load_collection(collection_name=self.collection_name)

        try:
            search_params = {"ef": 64}
            filter_expr = f"kb_id == {int(kb_id)}" if kb_id is not None else None

            results = self.client.search(
                collection_name=self.collection_name,
                data=query.astype(np.float32).tolist(),
                limit=top_k,
                filter=filter_expr,
                metric_type="COSINE",
                search_params=search_params,
                output_fields=["id", "kb_id", "doc_id", "text"],
            )

            distances = []
            ids = []
            for hits in results:
                distances.append([h["distance"] for h in hits] if hits else [-1.0] * top_k)
                ids.append([h["id"] for h in hits] if hits else [0] * top_k)

            for i in range(len(distances)):
                while len(distances[i]) < top_k:
                    distances[i].append(-1.0)
                    ids[i].append(0)
            return np.array(distances), np.array(ids)
        finally:
            try:
                self.client.release_collection(collection_name=self.collection_name)
            except Exception as e:
                logger.warning(f"Release collection failed: {e}")

    def delete_by_ids(self, ids: list[int]):
        if not ids:
            return
        self.client.delete(
            collection_name=self.collection_name,
            filter=f"id in [{','.join(str(int(i)) for i in ids)}]",
        )
        logger.info(f"Milvus deleted {len(ids)} vectors")

    def clear(self):
        if self.client.has_collection(collection_name=self.collection_name):
            self.client.drop_collection(collection_name=self.collection_name)
            logger.info(f"Milvus collection dropped: {self.collection_name}")
        self.__init__(
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
            user=settings.MILVUS_USER,
            password=settings.MILVUS_PASSWORD,
            db=settings.MILVUS_DB,
            collection_name=self.collection_name,
            dimension=self.dimension,
        )


class FAISSVectorStore(BaseVectorStore):

    def __init__(self, dimension: int = 1024):
        import faiss
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.id_map: dict[int, int] = {}

    def add(self, embeddings: np.ndarray, ids: list[int], kb_id: int | None = None, doc_id: int | None = None, texts: list[str] | None = None):
        if len(ids) == 0:
            return
        start_idx = self.index.ntotal
        self.index.add(embeddings.astype(np.float32))
        for i, chunk_id in enumerate(ids):
            self.id_map[start_idx + i] = chunk_id

    def search(self, query: np.ndarray, top_k: int = 5, kb_id: int | None = None) -> tuple[np.ndarray, np.ndarray]:
        if self.index.ntotal == 0:
            return np.array([[-1.0] * top_k]), np.array([[0] * top_k])
        k = min(top_k, self.index.ntotal)
        distances, indices = self.index.search(query.astype(np.float32), k)
        ids = np.array([[self.id_map.get(int(i), 0) for i in row] for row in indices])
        if ids.shape[1] < top_k:
            pad = top_k - ids.shape[1]
            ids = np.hstack([ids, np.zeros((ids.shape[0], pad), dtype=np.int64)])
            distances = np.hstack([distances, np.full((distances.shape[0], pad), -1.0)])
        return distances, ids

    def delete_by_ids(self, ids: list[int]):
        logger.warning("FAISS fallback does not support delete; ignored")

    def clear(self):
        import faiss
        self.index = faiss.IndexFlatL2(self.dimension)
        self.id_map = {}


_vector_store: BaseVectorStore | None = None


def get_vector_store() -> BaseVectorStore:
    global _vector_store
    if _vector_store is None:
        if settings.VECTOR_STORE_TYPE.lower() == "milvus":
            try:
                _vector_store = MilvusVectorStore(
                    host=settings.MILVUS_HOST,
                    port=settings.MILVUS_PORT,
                    user=settings.MILVUS_USER,
                    password=settings.MILVUS_PASSWORD,
                    db=settings.MILVUS_DB,
                    collection_name=settings.MILVUS_COLLECTION,
                    dimension=settings.VECTOR_DIMENSION,
                )
            except Exception as e:
                logger.error(f"Milvus init failed, fallback to FAISS: {e}")
                _vector_store = FAISSVectorStore(dimension=settings.VECTOR_DIMENSION)
        else:
            _vector_store = FAISSVectorStore(dimension=settings.VECTOR_DIMENSION)
    return _vector_store
