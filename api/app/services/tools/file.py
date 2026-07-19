from app.services.tools.base import BaseTool
from pathlib import Path


class ReadFileTool(BaseTool):
    name = "read_file"
    description = "读取指定文件的内容"
    parameters = [
        {"name": "file_path", "type": "str", "required": True, "description": "文件路径"},
    ]

    async def execute(self, **kwargs) -> str:
        file_path = kwargs.get("file_path")
        if not file_path:
            return "错误：缺少必要参数 file_path"
        
        try:
            path = Path(file_path)
            if not path.exists():
                return f"错误：文件不存在: {file_path}"
            
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return f"文件内容:\n{content}"
        except Exception as e:
            return f"读取文件失败: {str(e)}"


class WriteFileTool(BaseTool):
    name = "write_file"
    description = "写入内容到指定文件"
    parameters = [
        {"name": "file_path", "type": "str", "required": True, "description": "文件路径"},
        {"name": "content", "type": "str", "required": True, "description": "要写入的内容"},
        {"name": "append", "type": "bool", "required": False, "description": "是否追加模式，默认False"},
    ]

    async def execute(self, **kwargs) -> str:
        file_path = kwargs.get("file_path")
        content = kwargs.get("content")
        append = kwargs.get("append", False)
        
        if not file_path or content is None:
            return "错误：缺少必要参数 file_path 或 content"
        
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            mode = 'a' if append else 'w'
            with open(path, mode, encoding='utf-8') as f:
                f.write(content)
            
            return f"文件写入成功: {file_path}"
        except Exception as e:
            return f"写入文件失败: {str(e)}"


read_file = ReadFileTool()
write_file = WriteFileTool()