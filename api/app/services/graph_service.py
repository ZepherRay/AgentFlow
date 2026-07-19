"""Graph RAG service — extract entities/relations from chunks into Neo4j + Milvus."""

import json
import uuid
import numpy as np
import asyncio
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.document import Document, DocumentStatus
from app.models.chunk import Chunk
from app.utils.neo4j_client import get_neo4j_driver
from app.services.llm_service import LLMService
from app.services.embedding_service import EmbeddingService
from config import settings

# ── Prompts ──────────────────────────────────────────────────────

SIMPLE_EXTRACT_PROMPT = """你是一个知识图谱抽取专家。从以下文本中抽取所有实体和关系。

返回格式（严格JSON数组，不要其他文字）：
[
  {{
    "source": "实体1",
    "source_type": "实体类型",
    "relation": "关系",
    "target": "实体2",
    "target_type": "实体类型"
  }}
]

文本：
{text}"""

SCHEMA_EXTRACT_PROMPT = """你是一个知识图谱抽取专家。先分析以下文本的主题领域，然后抽取实体和关系。

第一步：分析领域，输出schema（实体类型列表和关系类型列表）。
第二步：按schema抽取实体和关系。

返回格式（严格JSON，不要其他文字）：
{{
  "schema": {{
    "entity_types": ["类型1", "类型2"],
    "relation_types": ["关系1", "关系2"]
  }},
  "triples": [
    {{
      "source": "实体1",
      "source_type": "类型1",
      "relation": "关系1",
      "target": "实体2",
      "target_type": "类型2"
    }}
  ]
}}

文本：
{text}"""

BATCH_EXTRACT_PROMPT = """你是一个知识图谱抽取专家。从以下多个文本片段中抽取所有实体和关系。

每个文本片段用---分隔。

返回格式（严格JSON数组，不要其他文字）：
[
  {{
    "source": "实体1",
    "source_type": "实体类型",
    "relation": "关系",
    "target": "实体2",
    "target_type": "实体类型"
  }}
]

文本片段：
{texts}"""


class GraphService:

    @staticmethod
    async def extract_graph_from_kb(
        db: AsyncSession, kb_id: int, method: str = "simple"
    ) -> dict:
        """Extract entities & relations from all completed docs in a kb into Neo4j + Milvus."""
        result = await db.execute(
            select(Document).where(
                Document.kb_id == kb_id,
                Document.status == DocumentStatus.COMPLETED,
            )
        )
        docs = list(result.scalars().all())
        if not docs:
            return {"nodes_count": 0, "relationships_count": 0, "message": "没有已完成的文档"}

        # 1. Clean old graph vectors in Milvus for this kb
        try:
            await GraphService._clean_graph_vectors(kb_id)
        except Exception as e:
            logger.warning(f"Skip graph vector cleanup: {e}")

        driver = await get_neo4j_driver()
        all_triples: list[dict] = []
        total_triples = 0

        # Collect all texts first
        all_texts_with_doc = []
        for doc in docs:
            chunk_result = await db.execute(
                select(Chunk).where(Chunk.doc_id == doc.id).order_by(Chunk.chunk_index)
            )
            chunks = list(chunk_result.scalars().all())
            for chunk in chunks:
                if chunk.content.strip():
                    all_texts_with_doc.append((chunk.content, doc.id))

        # Batch extract with LLM (5 texts per batch)
        batch_size = 5
        for i in range(0, len(all_texts_with_doc), batch_size):
            batch = all_texts_with_doc[i:i + batch_size]
            texts = [t[0][:3000] for t in batch]
            doc_ids = [t[1] for t in batch]
            
            triples = await GraphService._extract_triples_batch(texts, method)
            if triples:
                await GraphService._write_to_neo4j_batch(driver, triples, kb_id, doc_ids)
                all_triples.extend(triples)
                total_triples += len(triples)
                logger.info(f"Processed batch {i//batch_size + 1}/{(len(all_texts_with_doc)+batch_size-1)//batch_size}: {len(triples)} triples")

        logger.info(f"Graph extraction done for kb={kb_id}: {total_triples} triples")

        # 2. Vectorize triples -> Milvus (parallel)
        if all_triples:
            await GraphService._vectorize_triples(db, all_triples, kb_id)

        counts = await GraphService._count_graph(driver, kb_id)
        return {
            **counts,
            "message": f"抽取完成，共 {total_triples} 条三元组",
        }

    @staticmethod
    async def _clean_graph_vectors(kb_id: int):
        """Remove old graph vectors for this kb before re-extraction.
        Graph vectors stored with doc_id=-1 + kb_id field in global collection.
        """
        from app.utils.vector_store import get_vector_store
        try:
            store = get_vector_store(kb_id=kb_id)
            store.delete_by_filter(f"doc_id == -1 and kb_id == {int(kb_id)}")
            logger.info(f"Cleaned old graph vectors for kb={kb_id}")
        except Exception as e:
            logger.warning(f"Clean graph vectors failed: {e}")

    @staticmethod
    async def _vectorize_triples(db: AsyncSession, triples: list[dict], kb_id: int):
        """Generate embeddings for triples and store in global Milvus collection."""
        from app.utils.vector_store import get_vector_store
        store = get_vector_store(kb_id=kb_id)
        batch_size = 20
        for i in range(0, len(triples), batch_size):
            batch = triples[i:i + batch_size]
            texts = [
                f"{t['source']} --[{t.get('relation', 'related')}]--> {t['target']}"
                for t in batch
            ]
            ids = [-(abs(hash(t)) % (2**62 - 1)) for t in texts]
            embeddings = await EmbeddingService.embed_texts(texts)
            embeddings_np = np.array(embeddings, dtype=np.float32)
            store.add(embeddings_np, ids, doc_id=-1, texts=texts, kb_id=kb_id)
            logger.info(f"Stored {len(batch)} graph vectors in Milvus for kb={kb_id}")

    @staticmethod
    async def _extract_triples(text: str, method: str) -> list[dict]:
        """Call LLM to extract triples from text."""
        try:
            if method == "schema":
                prompt = SCHEMA_EXTRACT_PROMPT.format(text=text[:3000])
            else:
                prompt = SIMPLE_EXTRACT_PROMPT.format(text=text[:3000])

            resp = await LLMService.chat([
                {"role": "system", "content": "你是一个知识图谱抽取专家，只输出JSON。"},
                {"role": "user", "content": prompt},
            ])
            content = resp.strip()

            if content.startswith("```"):
                content = content.split("\n", 1)[-1]
                content = content.rsplit("```", 1)[0]

            if method == "schema":
                data = json.loads(content)
                return data.get("triples", [])
            else:
                return json.loads(content)

        except Exception as e:
            logger.warning(f"LLM extract failed for chunk (method={method}): {e}")
            return []

    @staticmethod
    async def _extract_triples_batch(texts: list[str], method: str) -> list[dict]:
        """Batch extract triples from multiple texts using single LLM call."""
        try:
            texts_str = "\n---\n".join(texts)
            prompt = BATCH_EXTRACT_PROMPT.format(texts=texts_str)

            resp = await LLMService.chat([
                {"role": "system", "content": "你是一个知识图谱抽取专家，只输出JSON。"},
                {"role": "user", "content": prompt},
            ])
            content = resp.strip()

            if content.startswith("```"):
                content = content.split("\n", 1)[-1]
                content = content.rsplit("```", 1)[0]

            return json.loads(content)

        except Exception as e:
            logger.warning(f"LLM batch extract failed (method={method}): {e}")
            return []

    @staticmethod
    async def _write_to_neo4j(
        driver, triples: list[dict], kb_id: int, doc_id: int
    ):
        """Write triples to Neo4j using MERGE to deduplicate."""
        async with driver.session(database=settings.NEO4J_DATABASE) as session:
            for t in triples:
                source_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{kb_id}:{t['source']}"))
                target_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{kb_id}:{t['target']}"))

                await session.run(
                    """
                    MERGE (n:Entity {id: $source_id, kb_id: $kb_id})
                    SET n.label = $source_label, n.type = $source_type
                    """,
                    source_id=source_id,
                    kb_id=kb_id,
                    source_label=t["source"],
                    source_type=t.get("source_type", "Entity"),
                )

                await session.run(
                    """
                    MERGE (n:Entity {id: $target_id, kb_id: $kb_id})
                    SET n.label = $target_label, n.type = $target_type
                    """,
                    target_id=target_id,
                    kb_id=kb_id,
                    target_label=t["target"],
                    target_type=t.get("target_type", "Entity"),
                )

                rel_type = t.get("relation", "RELATED_TO")
                await session.run(
                    """
                    MATCH (a:Entity {id: $source_id})
                    MATCH (b:Entity {id: $target_id})
                    MERGE (a)-[r:RELATED {type: $rel_type, doc_id: $doc_id}]->(b)
                    SET r.label = $rel_type
                    """,
                    source_id=source_id,
                    target_id=target_id,
                    rel_type=rel_type,
                    doc_id=doc_id,
                )

    @staticmethod
    async def _write_to_neo4j_batch(
        driver, triples: list[dict], kb_id: int, doc_ids: list[int]
    ):
        """Batch write triples to Neo4j using single transaction."""
        async with driver.session(database=settings.NEO4J_DATABASE) as session:
            async with session.begin_transaction() as tx:
                entities_map: dict[str, str] = {}
                
                for t in triples:
                    source_key = f"{kb_id}:{t['source']}"
                    if source_key not in entities_map:
                        entities_map[source_key] = str(uuid.uuid5(uuid.NAMESPACE_DNS, source_key))
                        await tx.run(
                            """
                            MERGE (n:Entity {id: $id, kb_id: $kb_id})
                            SET n.label = $label, n.type = $type
                            """,
                            id=entities_map[source_key],
                            kb_id=kb_id,
                            label=t["source"],
                            type=t.get("source_type", "Entity"),
                        )
                    
                    target_key = f"{kb_id}:{t['target']}"
                    if target_key not in entities_map:
                        entities_map[target_key] = str(uuid.uuid5(uuid.NAMESPACE_DNS, target_key))
                        await tx.run(
                            """
                            MERGE (n:Entity {id: $id, kb_id: $kb_id})
                            SET n.label = $label, n.type = $type
                            """,
                            id=entities_map[target_key],
                            kb_id=kb_id,
                            label=t["target"],
                            type=t.get("target_type", "Entity"),
                        )

                for t, doc_id in zip(triples, doc_ids * ((len(triples) + len(doc_ids) - 1) // len(doc_ids))):
                    source_key = f"{kb_id}:{t['source']}"
                    target_key = f"{kb_id}:{t['target']}"
                    rel_type = t.get("relation", "RELATED_TO")
                    
                    await tx.run(
                        """
                        MATCH (a:Entity {id: $source_id})
                        MATCH (b:Entity {id: $target_id})
                        MERGE (a)-[r:RELATED {type: $rel_type, doc_id: $doc_id}]->(b)
                        SET r.label = $rel_type
                        """,
                        source_id=entities_map[source_key],
                        target_id=entities_map[target_key],
                        rel_type=rel_type,
                        doc_id=doc_id,
                    )

    @staticmethod
    async def get_graph_data(kb_id: int, doc_id: int | None = None) -> dict:
        """Fetch all nodes and edges for a kb (or a single doc) from Neo4j."""
        driver = await get_neo4j_driver()
        nodes_map: dict[str, dict] = {}
        edges: list[dict] = []

        async with driver.session(database=settings.NEO4J_DATABASE) as session:
            if doc_id is not None:
                result = await session.run(
                    """
                    MATCH (n:Entity {kb_id: $kb_id})-[r {doc_id: $doc_id}]->(m:Entity {kb_id: $kb_id})
                    RETURN n, r, m
                    """,
                    kb_id=kb_id,
                    doc_id=int(doc_id),
                )
            else:
                result = await session.run(
                    """
                    MATCH (n:Entity {kb_id: $kb_id})-[r]->(m:Entity {kb_id: $kb_id})
                    RETURN n, r, m
                    """,
                    kb_id=kb_id,
                )

            async for record in result:
                n = record["n"]
                m = record["m"]
                r = record["r"]

                n_id = n.get("id", "")
                m_id = m.get("id", "")

                if n_id and n_id not in nodes_map:
                    nodes_map[n_id] = {
                        "id": n_id,
                        "label": n.get("label", n_id),
                        "type": n.get("type", "Entity"),
                    }
                if m_id and m_id not in nodes_map:
                    nodes_map[m_id] = {
                        "id": m_id,
                        "label": m.get("label", m_id),
                        "type": m.get("type", "Entity"),
                    }

                edges.append({
                    "from_id": n_id,
                    "to_id": m_id,
                    "label": r.get("label", r.get("type", "related")),
                    "type": r.get("type", "related"),
                })

        return {
            "nodes": list(nodes_map.values()),
            "edges": edges,
            "kb_id": kb_id,
        }

    @staticmethod
    async def extract_answer_graph(answer_text: str) -> dict:
        """Extract entities & relations from AI answer text (no persistence)."""
        triples = await GraphService._extract_triples(answer_text[:3000], "schema")
        nodes_map: dict[str, dict] = {}
        edges: list[dict] = []

        for t in triples:
            source_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"answer:{t['source']}"))
            target_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"answer:{t['target']}"))

            if source_id not in nodes_map:
                nodes_map[source_id] = {
                    "id": source_id,
                    "label": t["source"],
                    "type": t.get("source_type", "Entity"),
                }
            if target_id not in nodes_map:
                nodes_map[target_id] = {
                    "id": target_id,
                    "label": t["target"],
                    "type": t.get("target_type", "Entity"),
                }

            edges.append({
                "from_id": source_id,
                "to_id": target_id,
                "label": t.get("relation", "RELATED_TO"),
                "type": t.get("relation", "RELATED_TO"),
            })

        return {"nodes": list(nodes_map.values()), "edges": edges, "kb_id": 0}

    @staticmethod
    async def _count_graph(driver, kb_id: int) -> dict:
        """Count nodes and relations in Neo4j for a kb."""
        async with driver.session(database=settings.NEO4J_DATABASE) as session:
            node_result = await session.run(
                "MATCH (n:Entity {kb_id: $kb_id}) RETURN count(n) AS cnt",
                kb_id=kb_id,
            )
            rel_result = await session.run(
                "MATCH (n:Entity {kb_id: $kb_id})-[r]->() RETURN count(r) AS cnt",
                kb_id=kb_id,
            )
            nodes_count = await node_result.single()
            rels_count = await rel_result.single()
            return {
                "nodes_count": nodes_count["cnt"] if nodes_count else 0,
                "relationships_count": rels_count["cnt"] if rels_count else 0,
            }
