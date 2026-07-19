from app.services.llm_service import LLMService
from typing import Dict, List, Optional


class IntentAnalysis:
    def __init__(self, intent: str, agent_type: str, architecture: str, skills: List[str], kb_ids: List[int]):
        self.intent = intent
        self.agent_type = agent_type
        self.architecture = architecture
        self.skills = skills
        self.kb_ids = kb_ids


class IntentRouter:
    ARCHITECTURES = {
        "single": "单智能体",
        "react": "ReAct 架构",
        "plan_execute": "Plan & Execute 架构",
        "router_skill": "Router+Skill 架构",
        "multi": "多智能体",
        "graph_workflow": "Graph/Workflow 架构",
        "blackboard": "Blackboard 架构",
    }

    SKILLS_MAP = {
        "search": ["search_knowledge_base", "vector_search"],
        "calculation": ["calculator", "code_executor"],
        "file": ["read_file", "write_file"],
        "graph": ["graph_search"],
        "time": ["get_current_time"],
    }

    @staticmethod
    async def analyze_intent(user_input: str) -> IntentAnalysis:
        prompt = f"""请分析用户需求并生成智能体配置建议。
        
用户需求: {user_input}

请输出JSON格式的分析结果，包含以下字段:
1. intent: 意图描述(简短)
2. agent_type: 智能体类型，取值为 "single" 或 "multi"
3. architecture: 架构类型，从以下选项中选择: single, react, plan_execute, router_skill, multi, graph_workflow, blackboard
4. skills: 推荐的技能列表(从以下选项选择): search_knowledge_base, vector_search, graph_search, calculator, code_executor, read_file, write_file, get_current_time
5. required_knowledge: 是否需要知识库支持(true/false)

输出格式示例:
{{
    "intent": "数据分析助手",
    "agent_type": "single",
    "architecture": "react",
    "skills": ["search_knowledge_base", "calculator"],
    "required_knowledge": true
}}

只输出JSON，不要输出其他内容。"""

        messages = [
            {"role": "system", "content": "你是一个智能体配置分析助手，擅长分析用户需求并推荐合适的智能体架构和技能。"},
            {"role": "user", "content": prompt},
        ]

        result = await LLMService.chat(messages, temperature=0.3, max_tokens=500)
        
        try:
            import json
            data = json.loads(result)
            return IntentAnalysis(
                intent=data.get("intent", ""),
                agent_type=data.get("agent_type", "single"),
                architecture=data.get("architecture", "single"),
                skills=data.get("skills", []),
                kb_ids=[],
            )
        except Exception:
            return IntentAnalysis(
                intent=user_input[:50],
                agent_type="single",
                architecture="react",
                skills=["search_knowledge_base"],
                kb_ids=[],
            )

    @staticmethod
    def get_architecture_name(architecture: str) -> str:
        return IntentRouter.ARCHITECTURES.get(architecture, architecture)