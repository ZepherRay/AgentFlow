import asyncio
import threading
from loguru import logger
from sqlalchemy.orm import Session
from app.db.session import get_sync_engine, SyncSessionLocal
from app.models.document import Document, DocumentStatus
from app.models.chunk import Chunk
from app.models.embedding import Embedding
from app.models.knowledge_base import KnowledgeBase
from app.utils.file_parser import parse_file
from app.utils.chinese_splitter import get_splitter
from app.services.embedding_service import EmbeddingService
from app.services.doc_graph_service import DocGraphService

from app.schemas.knowledge import ImportConfig


def process_document_sync(doc_id: int, config: ImportConfig, loop: asyncio.AbstractEventLoop):
    """Sync DB ops + keep embedding HTTP calls in event loop. aiomysql not thread-safe -> use sync session."""
    engine = get_sync_engine()
    session = SyncSessionLocal(bind=engine)
    try:
        logger.info(f"Starting process_document for doc_id={doc_id}")
        doc = session.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            logger.warning(f"Document {doc_id} not found in DB (may not be committed yet)")
            return

        doc.status = DocumentStatus.PARSING
        session.commit()
        logger.info(f"Document {doc_id} status changed to PARSING")

        # Parse (sync wrapper around sync fn)
        logger.info(f"Parsing document {doc_id}: {doc.file_path}")
        text = parse_file(doc.file_path, loader_type=config.reader_type)
        doc.char_count = len(text)
        logger.info(f"Document {doc_id} parsed, char_count={doc.char_count}")

        # Chunk (sync)
        splitter = get_splitter(
            config.splitter_type,
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
        )
        chunks = splitter.split_text(text)
        logger.info(f"Document {doc_id} split into {len(chunks)} chunks")

        doc.status = DocumentStatus.CHUNKING
        session.commit()

        # Create chunk records (sync)
        chunk_objects = []
        for i, chunk_text in enumerate(chunks):
            chunk = Chunk(
                content=chunk_text,
                chunk_index=i,
                doc_id=doc.id,
                token_count=len(chunk_text),
            )
            session.add(chunk)
            chunk_objects.append(chunk)

        session.flush()
        chunk_ids = [c.id for c in chunk_objects]
        doc.chunk_count = len(chunks)
        logger.info(f"Document {doc_id} created {len(chunk_ids)} chunks in DB")

        doc.status = DocumentStatus.EMBEDDING
        session.commit()
        logger.info(f"Document {doc_id} status changed to EMBEDDING")

        # Embeddings (async HTTP calls -> run in event loop)
        batch_size = 20
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i+batch_size]
            batch_chunk_ids = chunk_ids[i:i+batch_size]
            logger.info(f"Document {doc_id} embedding batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1}")

            # Run async embedding in the passed event loop
            future = asyncio.run_coroutine_threadsafe(
                EmbeddingService.embed_texts(batch_chunks, embed_model=config.embed_model), loop
            )
            embeddings = future.result()
            logger.info(f"Document {doc_id} got {len(embeddings)} embeddings for batch")

            future2 = asyncio.run_coroutine_threadsafe(
                EmbeddingService.store_embeddings(
                    batch_chunk_ids, embeddings,
                    kb_id=doc.kb_id, doc_id=doc.id, texts=batch_chunks,
                    embed_model=config.embed_model
                ), loop
            )
            future2.result()

            # Track in Embedding table
            for cid in batch_chunk_ids:
                session.add(Embedding(chunk_id=cid, vector_id=str(cid), model=config.embed_model, dimension=1024))
            session.commit()
            logger.info(f"Document {doc_id} batch {i//batch_size + 1} stored to Milvus")

        old_chunk_count = doc.chunk_count or 0
        doc.chunk_count = len(chunks)
        doc.status = DocumentStatus.COMPLETED
        logger.info(f"Document {doc_id} completed: char_count={doc.char_count}, chunk_count={doc.chunk_count}")

        kb = session.query(KnowledgeBase).filter(KnowledgeBase.id == doc.kb_id).first()
        if kb:
            kb.chunk_count = max(0, kb.chunk_count - old_chunk_count + len(chunks))
            logger.info(f"KnowledgeBase {kb.id} chunk_count updated to {kb.chunk_count}")

        session.commit()
        logger.info(f"Document {doc_id} process completed successfully")

        # Auto-extract doc graph after processing - store in MySQL for instant display
        try:
            full_text = "\n".join(chunks)
            graph_future = asyncio.run_coroutine_threadsafe(
                DocGraphService.extract_and_store_async(doc.id, full_text, doc.kb_id), loop
            )
            graph_future.result(timeout=180)
            logger.info(f"DocGraph auto-extracted for doc {doc_id}")
        except Exception as e:
            logger.warning(f"DocGraph auto-extract failed for doc {doc_id}: {e}")

    except Exception as e:
        session.rollback()
        doc = session.query(Document).filter(Document.id == doc_id).first()
        if doc:
            kb = session.query(KnowledgeBase).filter(KnowledgeBase.id == doc.kb_id).first()
            if kb:
                kb.chunk_count = max(0, kb.chunk_count - (doc.chunk_count or 0))
            # Delete Milvus vectors
            try:
                chunk_ids = [c.id for c in doc.chunks]
                if chunk_ids:
                    from app.utils.vector_store import get_vector_store
                    store = get_vector_store(kb_id=doc.kb_id)
                    store.delete_by_ids(chunk_ids)
            except Exception as del_e:
                logger.warning(f"Failed to delete Milvus vectors for doc {doc_id}: {del_e}")
            session.delete(doc)  # cascades to Chunks → Embeddings
            session.commit()
            logger.info(f"Deleted failed document {doc_id} and its data")
        logger.exception(f"Process document {doc_id} failed: {e}")
    finally:
        session.close()


def process_documents(file_ids: list[int], config: ImportConfig = None):
    """批量处理文档 - 每个文档用独立线程"""
    if config is None:
        config = ImportConfig()

    # Get or create the shared background event loop for HTTP calls
    background_loop = _get_background_loop()

    for doc_id in file_ids:
        t = threading.Thread(
            target=process_document_sync,
            args=(doc_id, config, background_loop),
            daemon=True,
        )
        t.start()


_background_loop: asyncio.AbstractEventLoop | None = None


def _get_background_loop() -> asyncio.AbstractEventLoop:
    """Shared background event loop for embedding HTTP calls."""
    global _background_loop
    if _background_loop is None or _background_loop.is_closed():
        _background_loop = asyncio.new_event_loop()
        t = threading.Thread(target=_background_loop.run_forever, daemon=True)
        t.start()
    return _background_loop


# Keep backward compat: old async entry points
async def process_document(doc_id: int, config: ImportConfig = None):
    if config is None:
        config = ImportConfig()
    loop = _get_background_loop()
    process_document_sync(doc_id, config, loop)


async def process_documents_async(file_ids: list[int], config: ImportConfig = None):
    if config is None:
        config = ImportConfig()
    loop = _get_background_loop()
    for doc_id in file_ids:
        process_document_sync(doc_id, config, loop)
