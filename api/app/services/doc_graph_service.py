"""DocGraphService — per-document graph extraction with MySQL JSON storage (no vectorization)."""

import json
import uuid
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.doc_graph import DocGraph
from app.services.llm_service import LLMService


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


class DocGraphService:

    @staticmethod
    def _build_graph_from_triples(triples: list) -> dict:
        """Convert LLM-extracted triples to vis-network compatible format."""
        nodes_map: dict[str, dict] = {}
        edges: list[dict] = []

        for t in triples:
            src_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"docgraph:{t['source']}"))
            tgt_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"docgraph:{t['target']}"))

            if src_id not in nodes_map:
                nodes_map[src_id] = {
                    "id": src_id,
                    "label": t["source"],
                    "type": t.get("source_type", "Entity"),
                }
            if tgt_id not in nodes_map:
                nodes_map[tgt_id] = {
                    "id": tgt_id,
                    "label": t["target"],
                    "type": t.get("target_type", "Entity"),
                }

            edges.append({
                "from_id": src_id,
                "to_id": tgt_id,
                "label": t.get("relation", "RELATED_TO"),
                "type": t.get("relation", "RELATED_TO"),
            })

        return {
            "nodes": list(nodes_map.values()),
            "edges": edges,
        }

    @staticmethod
    async def extract(text: str) -> dict:
        """Extract triples from text using LLM, return vis-network graph data."""
        text_trimmed = text[:8000]
        try:
            resp = await LLMService.chat([
                {"role": "system", "content": "你是一个知识图谱抽取专家，只输出JSON。"},
                {"role": "user", "content": SCHEMA_EXTRACT_PROMPT.format(text=text_trimmed)},
            ], max_tokens=4096)
            content = resp.strip()
            logger.info(f"DocGraph LLM response length: {len(content)}")
            if content.startswith("```"):
                content = content.split("\n", 1)[-1]
                content = content.rsplit("```", 1)[0]
            data = json.loads(content)
            triples = data.get("triples", [])
            logger.info(f"DocGraph extracted: {len(triples)} triples")
        except json.JSONDecodeError as e:
            logger.error(f"DocGraph JSON decode failed: {e}, response: {content[:500]}")
            triples = []
        except Exception as e:
            logger.error(f"DocGraph extract failed: {e}")
            triples = []
        return DocGraphService._build_graph_from_triples(triples)

    @staticmethod
    def store(session: Session, kb_id: int, doc_id: int, graph_data: dict):
        """Store graph data to MySQL."""
        graph_json = json.dumps(graph_data, ensure_ascii=False)
        existing = session.query(DocGraph).filter(DocGraph.doc_id == doc_id).first()
        if existing:
            existing.graph_data = graph_json
            existing.kb_id = kb_id
        else:
            session.add(DocGraph(kb_id=kb_id, doc_id=doc_id, graph_data=graph_json))
        session.commit()

    @staticmethod
    async def extract_and_store(session: Session, doc_id: int, text: str, kb_id: int = 0) -> dict:
        """Extract + store, return graph data immediately."""
        graph_data = await DocGraphService.extract(text)
        DocGraphService.store(session, kb_id, doc_id, graph_data)
        logger.info(f"DocGraph stored for doc {doc_id}: {len(graph_data['nodes'])} nodes, {len(graph_data['edges'])} edges")
        return graph_data

    @staticmethod
    async def extract_and_store_async(doc_id: int, doc_text: str, kb_id: int) -> dict:
        """Async version for knowledge_tasks, returns graph data."""
        from app.db.session import SyncSessionLocal, get_sync_engine
        engine = get_sync_engine()
        session = SyncSessionLocal(bind=engine)
        try:
            graph_data = await DocGraphService.extract(doc_text)
            if graph_data['nodes']:
                DocGraphService.store(session, kb_id, doc_id, graph_data)
                logger.info(f"DocGraph stored for doc {doc_id}: {len(graph_data['nodes'])} nodes, {len(graph_data['edges'])} edges")
            else:
                DocGraphService._delete_empty_graph(session, doc_id)
                logger.warning(f"DocGraph empty for doc {doc_id}, not stored")
            return graph_data
        except Exception as e:
            session.rollback()
            logger.error(f"DocGraph store failed for doc {doc_id}: {e}")
            return {"nodes": [], "edges": []}
        finally:
            session.close()

    @staticmethod
    def _delete_empty_graph(session: Session, doc_id: int):
        """Delete empty graph cache to force re-extraction."""
        existing = session.query(DocGraph).filter(DocGraph.doc_id == doc_id).first()
        if existing:
            session.delete(existing)
            session.commit()
            logger.info(f"Deleted empty graph for doc {doc_id}")

    @staticmethod
    def get_doc_graph(session: Session, kb_id: int, doc_id: int) -> dict | None:
        """Retrieve stored graph from MySQL."""
        dg = session.query(DocGraph).filter(
            DocGraph.doc_id == doc_id,
            DocGraph.kb_id == kb_id,
        ).first()
        if not dg:
            return None
        data = json.loads(dg.graph_data)
        if not data.get('nodes'):
            return None
        return {
            "kb_id": kb_id,
            **data,
        }

    @staticmethod
    def delete_doc_graph(session: Session, doc_id: int):
        session.query(DocGraph).filter(DocGraph.doc_id == doc_id).delete()
        session.commit()
