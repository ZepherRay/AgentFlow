from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.agent import Agent
from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document
from app.models.chunk import Chunk
from app.services.controller.intent_router import IntentRouter
from app.services.controller.agent_builder import AgentBuilder
from app.services.tools import get_tool_by_name, ALL_TOOLS
from app.services.llm_service import LLMService
from app.core.exceptions import NotFoundException
from config import settings
from typing import Dict, List, Optional, AsyncGenerator
from functools import lru_cache
import hashlib

_RUNTIME_CACHE = {}
_LLM_CACHE = {}


class AgentService:
    @staticmethod
    async def get_agent(db: AsyncSession, agent_id: int) -> Agent:
        agent = await db.get(Agent, agent_id)
        if not agent:
            raise NotFoundException("智能体不存在")
        return agent

    @staticmethod
    async def generate_agent(db: AsyncSession, user_input: str) -> Agent:
        intent_analysis = await IntentRouter.analyze_intent(user_input)
        config = await AgentBuilder.build_agent_config(intent_analysis)

        kb_content = await AgentService._get_kb_content(db, config.get("kb_ids", []))
        system_prompt = await AgentBuilder.generate_system_prompt(config, kb_content)

        agent = Agent(
            name=config["name"],
            type=config["type"],
            description=config["description"],
            architecture=config["architecture"],
            system_prompt=system_prompt,
            llm_params=config["llm_params"],
            skills=config["skills"],
            kb_ids=config["kb_ids"],
        )
        db.add(agent)
        await db.flush()
        await db.refresh(agent)
        return agent

    @staticmethod
    def _get_cache_key(agent: Agent) -> str:
        key_parts = [
            str(agent.id),
            agent.architecture or "",
            str(agent.llm_params or {}),
            str(agent.skills or []),
            agent.system_prompt[:200] if agent.system_prompt else ""
        ]
        return hashlib.md5("|".join(key_parts).encode()).hexdigest()

    @staticmethod
    def _get_llm(agent: Agent):
        temp = agent.llm_params.get("temperature", 0.7) if agent.llm_params else 0.7
        max_tokens = agent.llm_params.get("max_tokens", 2048) if agent.llm_params else 2048
        
        cache_key = f"{settings.LLM_MODEL}_{temp}_{max_tokens}"
        if cache_key not in _LLM_CACHE:
            from langchain_openai import ChatOpenAI
            _LLM_CACHE[cache_key] = ChatOpenAI(
                model=settings.LLM_MODEL,
                temperature=temp,
                max_tokens=max_tokens,
                api_key=settings.DASHSCOPE_API_KEY,
                base_url=settings.DASHSCOPE_BASE_URL,
            )
        return _LLM_CACHE[cache_key]

    @staticmethod
    async def build_runtime(agent: Agent):
        cache_key = AgentService._get_cache_key(agent)
        
        if cache_key in _RUNTIME_CACHE:
            return _RUNTIME_CACHE[cache_key]

        tools = []
        skill_names = agent.skills or []
        for skill_name in skill_names:
            tool = get_tool_by_name(skill_name)
            if tool:
                tools.append(tool.to_langchain_tool())

        if agent.architecture in ["react", "plan_execute", "router_skill", "single"]:
            runtime = await AgentService._build_single_agent(agent, tools)
        elif agent.architecture in ["multi", "graph_workflow", "blackboard"]:
            runtime = await AgentService._build_multi_agent(agent, tools)
        else:
            runtime = await AgentService._build_single_agent(agent, tools)

        _RUNTIME_CACHE[cache_key] = runtime
        return runtime

    @staticmethod
    def clear_cache(agent_id: int = None):
        if agent_id:
            keys_to_remove = [k for k in _RUNTIME_CACHE if k.startswith(str(agent_id))]
            for k in keys_to_remove:
                del _RUNTIME_CACHE[k]
        else:
            _RUNTIME_CACHE.clear()

    @staticmethod
    async def _build_single_agent(agent: Agent, tools: List):
        try:
            from langchain.agents import create_react_agent, AgentExecutor
        except ImportError:
            from langchain.agents import AgentExecutor
            from langchain.agents.react import create_react_agent
        from langchain_core.prompts import PromptTemplate

        llm = AgentService._get_llm(agent)

        system = agent.system_prompt or ""
        template_text = f"""你是一个有帮助的智能助手。

{system}

你可以使用以下工具：
{{tools}}

请严格使用以下格式回复：

Question: 用户的问题
Thought: 你应该始终思考要做什么
Action: 要执行的动作，必须是 [{{tool_names}}] 之一。如果不需要调用工具，不要写 Action。
Action Input: 动作的输入
Observation: 动作的结果
...（Thought/Action/Action Input/Observation 可以重复多轮）
Thought: 我现在知道最终答案了
Final Answer: 最终答案

注意：
- 如果需要调用工具，必须严格按照 Thought/Action/Action Input/Observation 格式
- 如果不需要调用工具，直接给出 Final Answer

开始！

Question: {{input}}
Thought: {{agent_scratchpad}}"""
        prompt = PromptTemplate.from_template(template_text)

        agent_instance = create_react_agent(llm, tools, prompt)
        return AgentExecutor(
            agent=agent_instance,
            tools=tools,
            verbose=False,
            max_iterations=15,
            handle_parsing_errors=True,
        )

    @staticmethod
    async def _build_multi_agent(agent: Agent, tools: List):
        """多智能体——简化版：顺序调用协调器→工具→最终回复。"""
        async def multi_chat(message: str):
            max_rounds = 6
            conversation = []
            current_input = message
            for _round in range(max_rounds):
                # 协调器决定下一步
                coord_prompt = f"""用户消息: {current_input}
历史: {conversation[-2:]}
可用工具: {[t.name for t in tools]}

请决定下一步。如果不需要调用工具，直接回复用户。如果需要调用工具，只返回工具名称。"""
                decision = await LLMService.chat([
                    {"role": "system", "content": agent.system_prompt or "你是智能助手。"},
                    {"role": "user", "content": coord_prompt},
                ])
                decision = decision.strip()

                # 检查是否要调用工具
                matched_tool = next((t for t in tools if t.name == decision), None)
                if matched_tool:
                    yield f"\n[调用工具: {matched_tool.name}]\n"
                    result = await matched_tool.execute(query=current_input)
                    conversation.append(f"工具 {matched_tool.name} 结果: {result}")
                    current_input = f"工具执行结果: {result}"
                else:
                    # 协调器直接回复
                    yield decision
                    return

            # 超过轮次，生成最终回复
            yield decision

        return multi_chat

    @staticmethod
    def _format_history(history: list) -> str:
        """格式化对话历史为文本上下文。"""
        if not history:
            return ""
        lines = []
        for h in history[-10:]:
            role = "用户" if h.get("role") == "user" else "助手"
            content = h.get("content", "")
            if content:
                lines.append(f"{role}: {content}")
        return "\n".join(lines) + "\n"

    @staticmethod
    async def chat(agent: Agent, message: str, history: list = None) -> AsyncGenerator[str, None]:
        skill_names = agent.skills or []
        tools = []
        for skill_name in skill_names:
            tool = get_tool_by_name(skill_name)
            if tool:
                tools.append(tool.to_langchain_tool())

        history_text = AgentService._format_history(history or [])
        context_message = f"{history_text}用户: {message}" if history_text else message

        if not tools:
            async for chunk in AgentService._stream_llm_direct(agent, context_message):
                yield chunk
        elif agent.architecture in ["multi", "graph_workflow", "blackboard"]:
            multi_chat = await AgentService._build_multi_agent(agent, tools)
            async for chunk in multi_chat(context_message):
                yield chunk
        else:
            runtime = await AgentService.build_runtime(agent)
            async for chunk in AgentService._stream_with_executor(runtime, context_message):
                yield chunk

    @staticmethod
    async def _stream_llm_direct(agent: Agent, message: str) -> AsyncGenerator[str, None]:
        llm = AgentService._get_llm(agent)
        
        try:
            system_prompt = agent.system_prompt or ""
            messages = [
                ("system", system_prompt),
                ("human", message)
            ]
            
            async for chunk in llm.astream(messages):
                if hasattr(chunk, 'content') and chunk.content:
                    yield chunk.content
        except Exception as e:
            yield f"错误: {str(e)}"

    @staticmethod
    async def _stream_with_executor(runtime, message: str) -> AsyncGenerator[str, None]:
        try:
            result = await runtime.ainvoke({"input": message})
            if isinstance(result, dict):
                output = result.get("output", "")
                if output:
                    yield output
        except Exception as e:
            yield f"错误: {str(e)}"

    @staticmethod
    async def generate_system_prompt(db: AsyncSession, agent: Agent) -> str:
        kb_content = await AgentService._get_kb_content(db, agent.kb_ids or [])
        config = {
            "name": agent.name,
            "type": agent.type,
            "description": agent.description,
            "architecture": agent.architecture,
            "skills": agent.skills or [],
            "kb_ids": agent.kb_ids or [],
            "llm_params": agent.llm_params or {},
        }
        return await AgentBuilder.generate_system_prompt(config, kb_content)

    @staticmethod
    async def _get_kb_content(db: AsyncSession, kb_ids: List[int]) -> str:
        if not kb_ids:
            return ""

        contents = []
        for kb_id in kb_ids:
            kb = await db.get(KnowledgeBase, kb_id)
            if not kb:
                continue
            
            doc_result = await db.execute(select(Document).where(Document.kb_id == kb_id))
            docs = list(doc_result.scalars().all())
            
            for doc in docs:
                chunk_result = await db.execute(select(Chunk).where(Chunk.doc_id == doc.id).limit(3))
                chunks = list(chunk_result.scalars().all())
                if chunks:
                    chunk_content = "\n".join([c.content[:500] for c in chunks])
                    contents.append(f"知识库: {kb.name}\n文档: {doc.filename}\n内容摘要: {chunk_content}")
        
        return "\n\n".join(contents)[:3000]