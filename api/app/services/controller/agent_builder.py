from app.models.agent import Agent
from app.services.controller.intent_router import IntentAnalysis
from app.services.llm_service import LLMService
from typing import Dict, Optional


class AgentBuilder:
    @staticmethod
    async def build_agent_config(intent_analysis: IntentAnalysis, name: str = None) -> Dict:
        config = {
            "name": name or intent_analysis.intent or "未命名智能体",
            "type": intent_analysis.agent_type,
            "description": f"基于需求: {intent_analysis.intent}",
            "architecture": intent_analysis.architecture,
            "skills": intent_analysis.skills,
            "kb_ids": intent_analysis.kb_ids,
            "llm_params": {
                "temperature": 0.7,
                "max_tokens": 2048,
            },
        }
        return config

    @staticmethod
    async def generate_system_prompt(agent_config: Dict, kb_content: str = "") -> str:
        skills_desc = "\n".join([
            f"- {skill}: {AgentBuilder._get_skill_description(skill)}"
            for skill in agent_config.get("skills", [])
        ])

        prompt = f"""你是一个智能助手，具备以下能力:
        
角色定位:
{agent_config.get('description', '通用智能助手')}

可用技能:
{skills_desc}

知识库信息:
{kb_content if kb_content else '无'}

工作流程:
1. 分析用户问题
2. 如需调用工具，输出工具调用指令
3. 根据工具返回结果生成最终回答

请用中文友好地回答用户问题。"""

        return prompt

    @staticmethod
    def _get_skill_description(skill_name: str) -> str:
        descriptions = {
            "search_knowledge_base": "搜索知识库文档",
            "vector_search": "向量检索相关文档",
            "graph_search": "图数据库检索实体关系",
            "calculator": "数学计算",
            "code_executor": "执行Python代码",
            "read_file": "读取文件内容",
            "write_file": "写入文件内容",
            "get_current_time": "获取当前时间",
        }
        return descriptions.get(skill_name, skill_name)