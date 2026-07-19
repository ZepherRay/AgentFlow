from app.services.tools.base import BaseTool
from app.services.knowledge_service import KnowledgeService
from app.utils.vector_store import get_vector_store
from app.utils.neo4j_client import get_neo4j_driver
from app.db.session import AsyncSessionLocal
from app.schemas.knowledge import KnowledgeSearchRequest


class SearchKnowledgeBaseTool(BaseTool):
    name = "search_knowledge_base"
    description = "搜索指定知识库中的文档内容"
    parameters = [
        {"name": "kb_id", "type": "int", "required": True, "description": "知识库ID"},
        {"name": "query", "type": "str", "required": True, "description": "搜索查询词"},
        {"name": "top_k", "type": "int", "required": False, "description": "返回结果数量，默认5"},
    ]

    async def execute(self, **kwargs) -> str:
        kb_id = kwargs.get("kb_id")
        query = kwargs.get("query")
        top_k = kwargs.get("top_k", 5)
        
        if not kb_id or not query:
            return "错误：缺少必要参数 kb_id 或 query"
        
        try:
            async with AsyncSessionLocal() as db:
                req = KnowledgeSearchRequest(kb_id=kb_id, query=query, top_k=top_k)
                results = await KnowledgeService.search(db, req)
                return "\n\n".join([f"文档: {r.filename}\n内容: {r.content}" for r in results])
        except Exception as e:
            return f"搜索失败: {str(e)}"


class VectorSearchTool(BaseTool):
    name = "vector_search"
    description = "使用向量检索搜索相关文档片段"
    parameters = [
        {"name": "kb_id", "type": "int", "required": True, "description": "知识库ID"},
        {"name": "query", "type": "str", "required": True, "description": "搜索查询词"},
        {"name": "top_k", "type": "int", "required": False, "description": "返回结果数量，默认5"},
    ]

    async def execute(self, **kwargs) -> str:
        kb_id = kwargs.get("kb_id")
        query = kwargs.get("query")
        top_k = kwargs.get("top_k", 5)
        
        if not kb_id or not query:
            return "错误：缺少必要参数 kb_id 或 query"
        
        try:
            store = get_vector_store(kb_id=int(kb_id))
            results = store.search(query, top_k=top_k)
            if results:
                return "\n\n".join([f"相似度: {r.score:.4f}\n内容: {r.text}" for r in results])
            return "未找到相关文档"
        except Exception as e:
            return f"向量检索失败: {str(e)}"


class GraphSearchTool(BaseTool):
    name = "graph_search"
    description = "在Neo4j图数据库中搜索实体和关系"
    parameters = [
        {"name": "query", "type": "str", "required": True, "description": "搜索查询词"},
    ]

    async def execute(self, **kwargs) -> str:
        query = kwargs.get("query")
        if not query:
            return "错误：缺少必要参数 query"
        
        try:
            from config import settings
            if not settings.NEO4J_URI:
                return "Neo4j客户端未配置"
            
            driver = await get_neo4j_driver()
            async with driver.session(database=settings.NEO4J_DATABASE) as session:
                cypher = f"MATCH (n) WHERE n.name CONTAINS '{query}' OR n.content CONTAINS '{query}' RETURN n LIMIT 10"
                result = await session.run(cypher)
                records = await result.data()
            
            if records:
                return "\n\n".join([str(record) for record in records])
            return "未找到相关实体"
        except Exception as e:
            return f"图检索失败: {str(e)}"


search_knowledge_base = SearchKnowledgeBaseTool()
vector_search = VectorSearchTool()
graph_search = GraphSearchTool()