"""DAG 工作流执行引擎 — tinyflow-inspired: node handlers + topological queue + chain state"""

import asyncio
import copy
import re
from typing import AsyncGenerator, Dict, List, Optional, Any, Set
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import Workflow
from app.models.agent import Agent
from app.services.agent_service import AgentService
from app.services.tools import get_tool_by_name
from app.services.llm_service import LLMService
from config import settings

# ──────────────────────────────────────────────────────────────
# Paused states (module-level, same as before)
# ──────────────────────────────────────────────────────────────
_paused_states: Dict[str, dict] = {}
# Strong refs to timeout tasks — prevents asyncio GC from cancelling them
# when the executor/state is collected after the /test stream closes.
_timeout_tasks: Set[asyncio.Task] = set()


# ──────────────────────────────────────────────────────────────
# Chain State — tinyflow's ChainState analog
# ──────────────────────────────────────────────────────────────
class ChainState:
    """Runtime memory & execution tracking."""

    def __init__(self):
        self.memory: Dict[str, Any] = {"variables": {}}
        self.executed: Set[str] = set()
        self.interrupted = False
        self.paused_node_id: Optional[str] = None
        self._timeout_task: Optional[asyncio.Task] = None


# ──────────────────────────────────────────────────────────────
# Node handlers — tinyflow's Node hierarchy
# ──────────────────────────────────────────────────────────────
class BaseNode:
    def output_key(self, node: dict) -> str:
        return f"{node.get('name', node['id'])}_output"

    async def exec(self, node: dict, state: ChainState, db: AsyncSession) -> AsyncGenerator[dict, None]:
        raise NotImplementedError


class StartNode(BaseNode):
    async def exec(self, node: dict, state: ChainState, db: AsyncSession) -> AsyncGenerator[dict, None]:
        variables = node.get("variables", [])
        node_name = node.get("name", "start")
        # Handle both array format [{name, type, default}] and string format "input, user_id"
        if isinstance(variables, list):
            var_list = [v.get("name", "") for v in variables if v.get("name")]
        elif isinstance(variables, str):
            var_list = [v.strip() for v in variables.split(",") if v.strip()]
        else:
            var_list = []

        for i, v in enumerate(var_list):
            var_key = f"{node_name}_{v}"
            # First variable gets the input message, rest get defaults
            if i == 0:
                state.memory["variables"][var_key] = state.memory.get("input", "")
            else:
                # Check for default value in array format
                if isinstance(variables, list):
                    var_def = next((vd for vd in variables if vd.get("name") == v), None)
                    state.memory["variables"][var_key] = var_def.get("default", "") if var_def else ""
                else:
                    state.memory["variables"][var_key] = ""
        yield {"event": "node_end", "data": {"node_id": node["id"]}}


class EndNode(BaseNode):
    async def exec(self, node: dict, state: ChainState, db: AsyncSession) -> AsyncGenerator[dict, None]:
        yield {"event": "node_end", "data": {"node_id": node["id"]}}


class AgentNode(BaseNode):
    async def exec(self, node: dict, state: ChainState, db: AsyncSession) -> AsyncGenerator[dict, None]:
        agent_id = node.get("agent_id")
        if not agent_id:
            raise ValueError(f"Agent 节点 {node['id']} 缺少 agent_id")

        agent = await db.get(Agent, agent_id)
        if not agent:
            raise ValueError(f"Agent (id={agent_id}) 不存在")

        node_tools = node.get("tools")
        original_skills = agent.skills
        if node_tools:
            agent.skills = node_tools

        try:
            resolved = _resolve_inputs(node.get("inputs", {}), state)
            query = resolved.get("query", state.memory.get("input", ""))
            history = resolved.get("history", [])

            parts = []
            async for chunk in AgentService.chat(agent, query, history):
                parts.append(chunk)
            output = "".join(parts)
        finally:
            if node_tools:
                agent.skills = original_skills

        var_key = self.output_key(node)
        state.memory["variables"][var_key] = output
        yield {"event": "node_output", "data": {"node_id": node["id"], "output": output, "variable": var_key}}


class LLMNode(BaseNode):
    async def exec(self, node: dict, state: ChainState, db: AsyncSession) -> AsyncGenerator[dict, None]:
        # Model: support __other__ custom override (Dify-style)
        model = node.get("model") or ""
        if model == "__other__":
            model = node.get("model_custom") or settings.LLM_MODEL
        if not model:
            model = settings.LLM_MODEL
        temperature = node.get("temperature")
        max_tokens = node.get("max_tokens")

        # System prompt (interpolate {{var}})
        system_prompt = _interpolate(node.get("system_prompt", ""), state)

        # User prompt: prefer user_prompt field, fallback to inputs.prompt, then state.input
        user_prompt = node.get("user_prompt", "")
        if not user_prompt:
            resolved = _resolve_inputs(node.get("inputs", {}), state)
            user_prompt = resolved.get("prompt", "")
        if not user_prompt:
            user_prompt = state.memory.get("input", "")
        user_prompt = _interpolate(user_prompt, state)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        parts = []
        usage = None
        async for chunk in LLMService.chat_stream(model=model, messages=messages, temperature=temperature, max_tokens=max_tokens):
            if isinstance(chunk, dict) and "__usage__" in chunk:
                usage = chunk["__usage__"]
            else:
                parts.append(chunk)

        output = "".join(parts)
        var_key = self.output_key(node)
        state.memory["variables"][var_key] = output
        yield {"event": "node_output", "data": {"node_id": node["id"], "output": output, "variable": var_key, "usage": usage}}


class ConditionNode(BaseNode):
    async def exec(self, node: dict, state: ChainState, db: AsyncSession) -> AsyncGenerator[dict, None]:
        """Evaluate branches -> store chosen branch id. Edge routing done by scheduler."""
        branches = node.get("branches", [])

        # upstream error -> auto else
        for _input_key, input_val in node.get("inputs", {}).items():
            if isinstance(input_val, str) and input_val.startswith("/"):
                ref = input_val[1:]
                upstream_val = state.memory.get("variables", {}).get(ref)
                if isinstance(upstream_val, dict) and "error" in upstream_val:
                    for branch in branches:
                        if branch.get("isElse"):
                            state.memory["variables"][self.output_key(node)] = branch["id"]
                            yield {"event": "node_output", "data": {"node_id": node["id"], "output": branch["id"], "note": "upstream error, else branch"}}
                            return
                    state.memory["variables"][self.output_key(node)] = ""
                    yield {"event": "node_output", "data": {"node_id": node["id"], "output": ""}}
                    return

        chosen = None
        else_id = None
        for branch in branches:
            if branch.get("isElse"):
                else_id = branch["id"]
                continue
            rules = branch.get("rules", [])
            if not rules:
                continue
            if await _eval_branch(rules, state):
                chosen = branch["id"]
                break
        if not chosen:
            chosen = else_id

        state.memory["variables"][self.output_key(node)] = chosen or ""
        yield {"event": "node_output", "data": {"node_id": node["id"], "output": chosen or ""}}


class HumanInterventionNode(BaseNode):
    async def exec(self, node: dict, state: ChainState, db: AsyncSession) -> AsyncGenerator[dict, None]:
        config = node.get("config", {}) or {}
        title = config.get("title", "请选择处理方式")
        timeout = config.get("timeout", 300)
        default_branch = config.get("default_branch", "")
        branches = config.get("branches", [])

        # IMPORTANT: save pause snapshot BEFORE yielding — execute() returns immediately
        # upon receiving human_intervention event, closing this generator and skipping
        # any code after the yield.
        state.interrupted = True
        state.paused_node_id = node["id"]

        pause_key = f"{node['id']}"
        _paused_states[pause_key] = {
            "context": copy.deepcopy(state.memory),
            "edges": [],
            "nodes": [],
            "default_branch": default_branch,
            "timeout": timeout,
            "timeout_task": None,
        }

        if timeout > 0:
            async def _timeout_handler():
                try:
                    await asyncio.sleep(timeout)
                    _paused_states.pop(pause_key, None)
                    state.interrupted = False
                    state.paused_node_id = None
                finally:
                    _timeout_tasks.discard(asyncio.current_task())

            task = asyncio.create_task(_timeout_handler())
            _timeout_tasks.add(task)
            state._timeout_task = task
            _paused_states[pause_key]["timeout_task"] = task

        yield {
            "event": "human_intervention",
            "data": {
                "node_id": node["id"],
                "title": title,
                "timeout": timeout,
                "default_branch": default_branch,
                "branches": [{"id": b["id"], "label": b.get("label"), "desc": b.get("desc")} for b in branches],
            },
        }


class ReplyNode(BaseNode):
    async def exec(self, node: dict, state: ChainState, db: AsyncSession) -> AsyncGenerator[dict, None]:
        # Dify-style two modes: template (interpolate {{var}}) | variable (lookup single var ref)
        reply_mode = node.get("reply_mode", "template")
        inputs = node.get("inputs", {}) or {}
        raw_msg = inputs.get("message", "") or ""
        variables = state.memory.get("variables", {})

        def _lookup(ref: str):
            if ref == "input":
                return state.memory.get("input", "")
            return variables.get(ref)

        if reply_mode == "variable":
            raw = raw_msg.strip()
            message = raw
            # Case 1: single {{var}} form
            m = re.match(r"^\{\{\s*([a-zA-Z0-9_\u4e00-\u9fa5]+)\s*\}\}$", raw)
            if m:
                val = _lookup(m.group(1))
                if val is not None:
                    message = val if isinstance(val, str) else str(val)
            # Case 2: /var form (no other {{}})
            elif raw.startswith("/") and "{{" not in raw:
                ref = raw[1:]
                val = _lookup(ref)
                if val is not None:
                    message = val if isinstance(val, str) else str(val)
            # Case 3: bare var name
            elif re.fullmatch(r"[a-zA-Z0-9_\u4e00-\u9fa5]+", raw):
                val = _lookup(raw)
                if val is not None:
                    message = val if isinstance(val, str) else str(val)
            # Case 4: contains {{...}} — fallback to template interpolation
            elif "{{" in raw:
                resolved = _resolve_inputs(inputs, state)
                message = _interpolate(resolved.get("message", raw), state)
        else:
            # template mode: resolve /var refs first, then interpolate {{var}}
            resolved = _resolve_inputs(inputs, state)
            message = _interpolate(resolved.get("message", raw_msg), state)
            if not message:
                message = state.memory.get("input", "")

        var_key = self.output_key(node)
        state.memory["variables"][var_key] = message
        yield {"event": "node_output", "data": {"node_id": node["id"], "output": message}}


class ParallelNode(BaseNode):
    async def exec(self, node: dict, state: ChainState, db: AsyncSession) -> AsyncGenerator[dict, None]:
        # Parallel is a marker — actual parallel execution handled by scheduler
        yield {"event": "node_end", "data": {"node_id": node["id"]}}


class JoinNode(BaseNode):
    async def exec(self, node: dict, state: ChainState, db: AsyncSession) -> AsyncGenerator[dict, None]:
        # Merge all upstream nodes' `_output` variables into a single dict.
        # (Scheduler ensures all upstream nodes have executed before join runs.)
        merged = {}
        for var_name, var_value in state.memory.get("variables", {}).items():
            if var_name.endswith("_output"):
                merged[var_name] = var_value
        state.memory["variables"][self.output_key(node)] = merged
        yield {"event": "node_output", "data": {"node_id": node["id"], "output": merged, "variable": self.output_key(node)}}


_NODE_HANDLERS: Dict[str, BaseNode] = {
    "start": StartNode(),
    "end": EndNode(),
    "agent": AgentNode(),
    "llm": LLMNode(),
    "condition": ConditionNode(),
    "human_intervention": HumanInterventionNode(),
    "reply": ReplyNode(),
    "parallel": ParallelNode(),
    "join": JoinNode(),
}


# ──────────────────────────────────────────────────────────────
# Condition helpers (same logic, extracted)
# ──────────────────────────────────────────────────────────────
def _eval_expr(expr: str, ctx: dict) -> Optional[bool]:
    try:
        allowed = {"str": str, "len": len, "int": int, "float": float, "bool": bool}
        result = eval(expr, {"__builtins__": {}} | allowed, ctx)
        return bool(result)
    except Exception:
        return None


async def _llm_judge(expr: str, ctx: dict) -> bool:
    prompt = f"判断以下条件是否成立\n\n上下文: {ctx}\n条件: {expr}\n\n只返回 True 或 False"
    result = await LLMService.chat([{"role": "user", "content": prompt}], temperature=0.1, max_tokens=10)
    return "true" in result.strip().lower()


async def _eval_branch(rules: list, state: ChainState) -> bool:
    """Evaluate rules left-to-right with AND/OR as binary connectors.
    
    Each rule's `logic` field describes how it connects to the NEXT rule.
    No precedence — strictly left-to-right evaluation.
    """
    result = None
    ctx = state.memory.get("variables", {})
    for i, rule in enumerate(rules):
        expr = rule.get("value", "")
        if not expr:
            continue
        resolved = _resolve_expr(expr, state)
        rule_result = _eval_expr(resolved, ctx)
        if rule_result is None:
            rule_result = await _llm_judge(expr, ctx)

        if result is None:
            result = rule_result
        else:
            cur_logic = rules[i - 1].get("logic", "and")
            if cur_logic == "or":
                result = result or rule_result
            else:
                result = result and rule_result
                if result is False:
                    return False

    return result if result is not None else False


# ──────────────────────────────────────────────────────────────
# Input / Expression resolvers
# ──────────────────────────────────────────────────────────────
def _resolve_inputs(inputs: dict, state: ChainState) -> dict:
    resolved = {}
    for key, value in inputs.items():
        if isinstance(value, str) and value.startswith("/"):
            ref = value[1:]
            if ref == "input":
                resolved[key] = state.memory.get("input", "")
            elif ref in state.memory.get("variables", {}):
                resolved[key] = state.memory["variables"][ref]
            else:
                resolved[key] = value
        else:
            resolved[key] = value
    return resolved


def _interpolate(text: str, state: ChainState) -> str:
    """Replace {{varname}} tokens with values from state.memory (variables or input).

    Handles `{{input}}` and `{{node_output}}` style references.
    """
    if not isinstance(text, str) or not text:
        return text or ""

    variables = state.memory.get("variables", {})
    input_val = state.memory.get("input", "")

    def _repl(match):
        key = match.group(1).strip()
        if key == "input":
            return str(input_val)
        if key in variables:
            val = variables[key]
            return val if isinstance(val, str) else str(val)
        # leave token as-is if unresolved (avoids silent data loss)
        return match.group(0)

    return re.sub(r"\{\{\s*([a-zA-Z0-9_\u4e00-\u9fa5]+)\s*\}\}", _repl, text)


def _resolve_expr(expr: str, state: ChainState) -> str:
    resolved = expr
    for var_name, var_value in state.memory.get("variables", {}).items():
        ref = f"/{var_name}"
        if ref in resolved:
            resolved = resolved.replace(ref, repr(var_value))
    return resolved


# ──────────────────────────────────────────────────────────────
# DAG scheduler — tinyflow's ChainExecutor analog
# ──────────────────────────────────────────────────────────────
def _build_adj(edges: list) -> tuple:
    """Forward & reverse adjacency from edge list."""
    fwd: Dict[str, List[Dict]] = {}
    rev: Dict[str, List[Dict]] = {}
    for e in edges:
        frm = e.get("from")
        to = e.get("to")
        if frm:
            fwd.setdefault(frm, []).append(e)
        if to:
            rev.setdefault(to, []).append(e)
    return fwd, rev


def _find_entry(nodes: list, rev_adj: dict) -> List[str]:
    """Nodes with no incoming edges = entry points."""
    ids = {n["id"] for n in nodes}
    has_incoming = set(rev_adj.keys())
    return [nid for nid in ids if nid not in has_incoming]


def _find_exit(nodes: list, fwd_adj: dict) -> List[str]:
    """Nodes with no outgoing edges = exit points."""
    ids = {n["id"] for n in nodes}
    has_outgoing = set(fwd_adj.keys())
    return [nid for nid in ids if nid not in has_outgoing]


def _resolve_condition_output(node: dict, state: ChainState) -> Optional[str]:
    """Condition node: read chosen branch id from context."""
    var_key = f"{node.get('name', node['id'])}_output"
    return state.memory.get("variables", {}).get(var_key)


def _resolve_converge_node(node: dict, state: ChainState) -> Optional[str]:
    """Human_intervention: routes via branch edges using stored pause state."""
    paused = _paused_states.get(node["id"])
    if paused and "resume_choice" in paused:
        return paused["resume_choice"]
    return None


async def _exec_node_with_retry(node: dict, state: ChainState, db: AsyncSession) -> AsyncGenerator[dict, None]:
    """Dispatch to node handler + optional retry."""
    ntype = node.get("type", "")
    handler = _NODE_HANDLERS.get(ntype)
    if not handler:
        yield {"event": "error", "data": {"node_id": node["id"], "error": f"未知节点类型: {ntype}"}}
        return

    no_retry = {"start", "end", "parallel", "join", "human_intervention"}
    max_retries = node.get("max_retries", 0) if ntype not in no_retry else 0
    retry_interval = node.get("retry_interval", 1)

    for attempt in range(max_retries + 1):
        try:
            async for event in handler.exec(node, state, db):
                yield event
            if ntype not in no_retry:
                yield {"event": "node_end", "data": {"node_id": node["id"]}}
            break
        except Exception as e:
            if attempt < max_retries:
                yield {"event": "log_update", "data": {"node_id": node["id"], "log": f"重试 {attempt+1}/{max_retries}"}}
                await asyncio.sleep(retry_interval * (2 ** attempt))
            else:
                yield {"event": "log_update", "data": {"node_id": node["id"], "log": f"节点执行失败: {str(e)}"}}
                var_key = f"{node.get('name', node['id'])}_output"
                state.memory["variables"][var_key] = {"error": str(e)}
                return


def _schedule_downstream(node_id: str, state: ChainState, fwd_adj: dict, node_map: dict) -> List[str]:
    """Return downstream node ids to execute after node_id completes."""
    node = node_map.get(node_id)
    if not node:
        return []

    ntype = node.get("type", "")
    downstream = []

    if ntype == "condition":
        chosen = _resolve_condition_output(node, state)
        for br in node.get("branches", []):
            if br.get("id") == chosen:
                target = br.get("target")
                if target and target in node_map:
                    downstream.append(target)
                break
        # if no match, check edges for first else-like edge
        if not downstream:
            for edge in fwd_adj.get(node_id, []):
                target = edge.get("to")
                if target and target in node_map:
                    downstream.append(target)
                    break
        return downstream

    if ntype == "human_intervention":
        choice = _resolve_converge_node(node, state)
        if choice:
            # Route to the chosen branch's target (Dify-style: each branch binds a target node)
            branches = (node.get("config", {}) or {}).get("branches", []) or node.get("branches", [])
            chosen_branch = next((b for b in branches if b.get("id") == choice), None)
            if chosen_branch and chosen_branch.get("target"):
                if chosen_branch["target"] in node_map:
                    downstream.append(chosen_branch["target"])
            else:
                # Fallback: first outgoing edge (legacy behavior)
                for edge in fwd_adj.get(node_id, []):
                    target = edge.get("to")
                    if target and target in node_map:
                        downstream.append(target)
                        break
        return downstream

    if ntype == "parallel":
        # trigger all immediate downstream nodes
        for edge in fwd_adj.get(node_id, []):
            target = edge.get("to")
            if target and target in node_map:
                downstream.append(target)
        return downstream

    # default: first outgoing edge
    for edge in fwd_adj.get(node_id, []):
        target = edge.get("to")
        if target and target in node_map:
            downstream.append(target)
            break
    return downstream


# ──────────────────────────────────────────────────────────────
# Main executor (same public API as before)
# ──────────────────────────────────────────────────────────────
class WorkflowExecutor:
    """DAG-based workflow executor — tinyflow architecture adapted for Python."""

    def __init__(self, workflow: Workflow, db: AsyncSession):
        self.workflow = workflow
        self.db = db
        self.nodes: List[Dict] = workflow.nodes or []
        self.edges: List[Dict] = workflow.edges or []
        self.node_map = {n["id"]: n for n in self.nodes}
        self.state = ChainState()
        self.fwd_adj, self.rev_adj = _build_adj(self.edges)

    # ── Public API ────────────────────────────────────────────

    async def execute(self, message: str, history: list = None) -> AsyncGenerator[dict, None]:
        """Execute DAG: enqueue entry nodes, process queue topologically."""
        self.state.memory["input"] = message

        entry_ids = _find_entry(self.nodes, self.rev_adj)
        if not entry_ids:
            yield {"event": "error", "data": {"node_id": "", "error": "找不到入口节点"}}
            return

        # check start node exists
        start = next((n for n in self.nodes if n.get("type") == "start"), None)
        if not start:
            yield {"event": "error", "data": {"node_id": "", "error": "找不到开始节点"}}
            return

        # execute start node first
        async for event in _exec_node_with_retry(start, self.state, self.db):
            yield event
            if event["event"] in ("error", "human_intervention"):
                return

        self.state.executed.add(start["id"])

        # BFS-style DAG queue
        queue: List[str] = []
        for nid in _schedule_downstream(start["id"], self.state, self.fwd_adj, self.node_map):
            if nid not in self.state.executed:
                queue.append(nid)

        while queue and not self.state.interrupted:
            nid = queue.pop(0)
            if nid in self.state.executed:
                continue

            node = self.node_map.get(nid)
            if not node:
                continue

            # join node: wait for all upstream to complete
            if node.get("type") == "join":
                upstream = self.rev_adj.get(nid, [])
                if not all(e.get("from") in self.state.executed for e in upstream if e.get("from")):
                    queue.append(nid)
                    continue

            yield {"event": "node_start", "data": {"node_id": nid, "node_type": node.get("type", "")}}

            async for event in _exec_node_with_retry(node, self.state, self.db):
                yield event
                if event["event"] in ("error", "human_intervention"):
                    return

            self.state.executed.add(nid)

            # schedule downstream
            for dn in _schedule_downstream(nid, self.state, self.fwd_adj, self.node_map):
                if dn not in self.state.executed and dn not in queue:
                    queue.append(dn)

        if not self.state.interrupted:
            yield self._build_final_event()

    async def resume(self, workflow_id: int, node_id: str, choice: str) -> AsyncGenerator[dict, None]:
        """Resume from human_intervention pause."""
        pause_key = f"{workflow_id}:{node_id}"
        state_snapshot = _paused_states.pop(pause_key, None)

        # also check plain node_id key
        if not state_snapshot:
            state_snapshot = _paused_states.pop(node_id, None)

        if not state_snapshot:
            yield {"event": "error", "data": {"node_id": node_id, "error": "暂停状态不存在或已超时"}}
            return

        # Cancel any pending timeout task so it doesn't pop the resume_choice later
        timeout_task = state_snapshot.get("timeout_task")
        if timeout_task and not timeout_task.done():
            timeout_task.cancel()
            _timeout_tasks.discard(timeout_task)

        self.state.memory = state_snapshot.get("context", {"variables": {}})
        self.state.interrupted = False
        self.state.paused_node_id = None

        # store choice for human_intervention routing
        _paused_states[node_id] = {"resume_choice": choice}

        node = self.node_map.get(node_id)
        if not node:
            yield {"event": "error", "data": {"node_id": node_id, "error": "暂停节点不存在"}}
            return

        self.state.executed.add(node_id)

        # schedule downstream
        queue = list(_schedule_downstream(node_id, self.state, self.fwd_adj, self.node_map))
        yield {"event": "resumed", "data": {"node_id": node_id, "choice": choice}}

        while queue and not self.state.interrupted:
            nid = queue.pop(0)
            if nid in self.state.executed:
                continue

            nd = self.node_map.get(nid)
            if not nd:
                continue

            # join gate
            if nd.get("type") == "join":
                upstream = self.rev_adj.get(nid, [])
                if not all(e.get("from") in self.state.executed for e in upstream if e.get("from")):
                    queue.append(nid)
                    continue

            yield {"event": "node_start", "data": {"node_id": nid, "node_type": nd.get("type", "")}}

            async for event in _exec_node_with_retry(nd, self.state, self.db):
                yield event
                if event["event"] in ("error", "human_intervention"):
                    return

            self.state.executed.add(nid)

            for dn in _schedule_downstream(nid, self.state, self.fwd_adj, self.node_map):
                if dn not in self.state.executed and dn not in queue:
                    queue.append(dn)

        if not self.state.interrupted:
            yield self._build_final_event()

    # ── Final event ──────────────────────────────────────────

    def _build_final_event(self) -> dict:
        output = ""
        for var_name, var_value in reversed(list(self.state.memory.get("variables", {}).items())):
            if not var_name.endswith("_input"):
                output = var_value
                break
        return {"event": "final", "data": {"output": output}}
