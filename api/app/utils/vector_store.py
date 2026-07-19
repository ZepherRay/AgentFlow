import numpy as np
from pathlib import Path
from typing import Any
from config import settings
from loguru import logger


class BaseVectorStore:
    def add(self, embeddings: np.ndarray, ids: list[int], doc_id: int | None = None,
            texts: list[str] | None = None, kb_id: int | None = None): ...
    def search(self, query: np.ndarray, top_k: int = 5, kb_id: int | None = None) -> tuple[np.ndarray, np.ndarray, list[dict]]: ...
    def delete_by_ids(self, ids: list[int]): ...
    def delete_by_filter(self, filter_expr: str): ...
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
        self.client.load_collection(collection_name=self.collection_name)

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
            logger.warning(f"Schema check failed (not dropping): {e}")

    def add(self, embeddings: np.ndarray, ids: list[int], doc_id: int | None = None,
            texts: list[str] | None = None, kb_id: int | None = None):
        if len(ids) == 0:
            return
        doc_id = doc_id or 0
        records = []
        for i, chunk_id in enumerate(ids):
            record = {
                "id": int(chunk_id),
                "doc_id": int(doc_id),
                "kb_id": int(kb_id) if kb_id is not None else 0,
                "embedding": embeddings[i].astype(np.float32).tolist(),
            }
            if texts and i < len(texts):
                record["text"] = texts[i][:65535]
            records.append(record)
        self.client.insert(collection_name=self.collection_name, data=records)
        self.client.flush(collection_name=self.collection_name)
        logger.info(f"Milvus inserted {len(ids)} vectors into {self.collection_name}")

    def search(self, query: np.ndarray, top_k: int = 5, kb_id: int | None = None) -> tuple[np.ndarray, np.ndarray, list[dict]]:
        try:
            collection_stats = self.client.get_collection_stats(collection_name=self.collection_name)
            if collection_stats["row_count"] == 0:
                return np.array([[-1.0] * top_k]), np.array([[0] * top_k]), []
        except Exception as e:
            logger.warning(f"Collection stats failed: {e}")
            return np.array([[-1.0] * top_k]), np.array([[0] * top_k]), []

        search_params = {"ef": 64}

        filter_expr = None
        if kb_id is not None:
            filter_expr = f"kb_id == {int(kb_id)}"

        results = self.client.search(
            collection_name=self.collection_name,
            data=query.astype(np.float32).tolist(),
            limit=top_k,
            metric_type="COSINE",
            search_params=search_params,
            output_fields=["id", "doc_id", "text"],
            filter=filter_expr,
        )

        distances = []
        ids = []
        texts_meta = []
        for hits in results:
            distances.append([h["distance"] for h in hits] if hits else [-1.0] * top_k)
            ids.append([h["id"] for h in hits] if hits else [0] * top_k)
            meta = []
            for h in hits:
                meta.append({
                    "id": h["id"],
                    "text": h.get("text", ""),
                    "doc_id": h.get("doc_id", 0),
                })
            texts_meta.append(meta)

        for i in range(len(distances)):
            while len(distances[i]) < top_k:
                distances[i].append(-1.0)
                ids[i].append(0)
                texts_meta[i].append({"id": 0, "text": "", "doc_id": 0})
        return np.array(distances), np.array(ids), texts_meta

    def delete_by_ids(self, ids: list[int]):
        if not ids:
            return
        self.client.delete(
            collection_name=self.collection_name,
            filter=f"id in [{','.join(str(int(i)) for i in ids)}]",
        )
        logger.info(f"Milvus deleted {len(ids)} vectors")

    def delete_by_filter(self, filter_expr: str):
        try:
            self.client.load_collection(collection_name=self.collection_name)
        except Exception:
            pass
        self.client.delete(
            collection_name=self.collection_name,
            filter=filter_expr,
        )
        logger.info(f"Milvus deleted by filter: {filter_expr}")

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

    def add(self, embeddings: np.ndarray, ids: list[int], doc_id: int | None = None, texts: list[str] | None = None):
        if len(ids) == 0:
            return
        start_idx = self.index.ntotal
        self.index.add(embeddings.astype(np.float32))
        for i, chunk_id in enumerate(ids):
            self.id_map[start_idx + i] = chunk_id

    def search(self, query: np.ndarray, top_k: int = 5, **kwargs) -> tuple[np.ndarray, np.ndarray, list[dict]]:
        if self.index.ntotal == 0:
            return np.array([[-1.0] * top_k]), np.array([[0] * top_k]), []
        k = min(top_k, self.index.ntotal)
        distances, indices = self.index.search(query.astype(np.float32), k)
        ids = np.array([[self.id_map.get(int(i), 0) for i in row] for row in indices])
        if ids.shape[1] < top_k:
            pad = top_k - ids.shape[1]
            ids = np.hstack([ids, np.zeros((ids.shape[0], pad), dtype=np.int64)])
            distances = np.hstack([distances, np.full((distances.shape[0], pad), -1.0)])
        texts_meta = [[{"id": int(ids[0][j]), "text": ""} for j in range(top_k)]]
        return distances, ids, texts_meta

    def delete_by_ids(self, ids: list[int]):
        logger.warning("FAISS fallback does not support delete; ignored")

    def delete_by_filter(self, filter_expr: str):
        logger.warning("FAISS fallback does not support delete; ignored")

    def clear(self):
        import faiss
        self.index = faiss.IndexFlatL2(self.dimension)
        self.id_map = {}


_store_registry: dict[str, BaseVectorStore] = {}


def get_vector_store(kb_id: int | None = None) -> BaseVectorStore:
    global _store_registry
    collection_name = settings.MILVUS_COLLECTION  # single global collection

    existing = _store_registry.get(collection_name)

    use_milvus = settings.VECTOR_STORE_TYPE.lower() == "milvus"
    if use_milvus:
        # Return cached Milvus, or retry if currently FAISS fallback
        if existing:
            if isinstance(existing, MilvusVectorStore):
                return existing
            logger.warning(f"Retrying Milvus for {collection_name} (was FAISS fallback)")

        try:
            store = MilvusVectorStore(
                host=settings.MILVUS_HOST,
                port=settings.MILVUS_PORT,
                user=settings.MILVUS_USER,
                password=settings.MILVUS_PASSWORD,
                db=settings.MILVUS_DB,
                collection_name=collection_name,
                dimension=settings.VECTOR_DIMENSION,
            )
            _store_registry[collection_name] = store
            return store
        except Exception as e:
            logger.error(f"Milvus init failed for {collection_name}, fallback to FAISS: {e}")
            if existing and isinstance(existing, FAISSVectorStore):
                return existing  # reuse cached FAISS to avoid data loss between batches
            store = FAISSVectorStore(dimension=settings.VECTOR_DIMENSION)
            _store_registry[collection_name] = store
            return store

    store = FAISSVectorStore(dimension=settings.VECTOR_DIMENSION)
    _store_registry[collection_name] = store
    return store
