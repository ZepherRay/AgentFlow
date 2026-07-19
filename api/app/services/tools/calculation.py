from app.services.tools.base import BaseTool
import math
import ast


class CalculatorTool(BaseTool):
    name = "calculator"
    description = "执行数学计算"
    parameters = [
        {"name": "expression", "type": "str", "required": True, "description": "数学表达式"},
    ]

    async def execute(self, **kwargs) -> str:
        expression = kwargs.get("expression")
        if not expression:
            return "错误：缺少必要参数 expression"
        
        allowed_funcs = {
            'abs': abs, 'round': round, 'sqrt': math.sqrt, 'pow': pow,
            'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
            'log': math.log, 'log10': math.log10, 'exp': math.exp,
            'pi': math.pi, 'e': math.e,
        }
        
        try:
            code = ast.parse(expression, mode='eval')
            for node in ast.walk(code):
                if isinstance(node, ast.Call):
                    func_name = node.func.id if isinstance(node.func, ast.Name) else None
                    if func_name and func_name not in allowed_funcs:
                        return f"错误：不允许使用函数 {func_name}"
            
            result = eval(expression, {"__builtins__": {}}, allowed_funcs)
            return f"计算结果: {result}"
        except SyntaxError:
            return "错误：表达式语法错误"
        except Exception as e:
            return f"计算失败: {str(e)}"


class CodeExecutorTool(BaseTool):
    name = "code_executor"
    description = "执行Python代码片段"
    parameters = [
        {"name": "code", "type": "str", "required": True, "description": "Python代码"},
    ]

    async def execute(self, **kwargs) -> str:
        code = kwargs.get("code")
        if not code:
            return "错误：缺少必要参数 code"
        
        allowed_modules = {
            'math': math,
        }
        
        try:
            local_vars = {}
            exec(code, {"__builtins__": {}, **allowed_modules}, local_vars)
            
            if local_vars:
                results = []
                for key, value in local_vars.items():
                    if not key.startswith('_'):
                        results.append(f"{key} = {value}")
                return "\n".join(results)
            return "代码执行完成，无返回值"
        except Exception as e:
            return f"代码执行失败: {str(e)}"


calculator = CalculatorTool()
code_executor = CodeExecutorTool()