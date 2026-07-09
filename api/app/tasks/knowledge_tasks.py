import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.models.document import Document, DocumentStatus
from app.models.chunk import Chunk
from app.models.knowledge_base import KnowledgeBase
from app.services.document_service import DocumentService
from app.services.chunk_service import ChunkService
from app.services.embedding_service import EmbeddingService


async def process_document(doc_id: int):
    """异步处理文档：解析 -> 切分 -> 向量化"""
    async with AsyncSessionLocal() as db:
        doc = await db.get(Document, doc_id)
        if not doc:
            return

        doc.status = DocumentStatus.PARSING
        await db.commit()

        try:
            text = await DocumentService.parse_document(doc.file_path)
            chunks = await ChunkService.split(text)
            doc.status = DocumentStatus.CHUNKING
            await db.commit()

            chunk_ids = []
            embeddings = []
            for i, chunk_text in enumerate(chunks):
                chunk = Chunk(
                    content=chunk_text,
                    chunk_index=i,
                    doc_id=doc.id,
                    token_count=len(chunk_text),
                )
                db.add(chunk)
                await db.flush()
                await db.refresh(chunk)
                chunk_ids.append(chunk.id)

                embedding = await EmbeddingService.embed_text(chunk_text)
                embeddings.append(embedding)

            doc.status = DocumentStatus.EMBEDDING
            await db.commit()

            await EmbeddingService.store_embeddings(chunk_ids, embeddings)

            doc.chunk_count = len(chunks)
            doc.status = DocumentStatus.COMPLETED

            kb = await db.get(KnowledgeBase, doc.kb_id)
            if kb:
                kb.chunk_count += len(chunks)

            await db.commit()

        except Exception as e:
            doc.status = DocumentStatus.FAILED
            await db.commit()
            raise e


def run_process_document(doc_id: int):
    asyncio.run(process_document(doc_id))