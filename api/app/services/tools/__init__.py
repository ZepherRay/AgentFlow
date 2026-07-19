from app.services.tools.base import BaseTool, ToolConfig
from app.services.tools.retrieval import search_knowledge_base, vector_search, graph_search
from app.services.tools.calculation import calculator, code_executor
from app.services.tools.file import read_file, write_file
from app.services.tools.system import get_current_time

ALL_TOOLS = [
    search_knowledge_base,
    vector_search,
    graph_search,
    calculator,
    code_executor,
    read_file,
    write_file,
    get_current_time,
]

def get_tool_by_name(name: str):
    for tool in ALL_TOOLS:
        if tool.name == name:
            return tool
    return None

def get_all_tool_names():
    return [tool.name for tool in ALL_TOOLS]