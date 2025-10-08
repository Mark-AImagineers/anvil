# server/registry.py
import importlib
import pkgutil
import inspect
import sys
from typing import List, Callable, Dict
from mcp.types import Tool
import server.tools as tools_pkg


class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Dict] = {}
    
    def register(self, name: str, description: str, input_schema: dict):
        """Decorator to register a tool handler"""
        def decorator(func: Callable):
            self.tools[name] = {
                "description": description,
                "input_schema": input_schema,
                "handler": func
            }
            return func
        return decorator
    
    def get_tool_definitions(self) -> List[Tool]:
        """Get all tool definitions for list_tools()"""
        return [
            Tool(
                name=name,
                description=info["description"],
                inputSchema=info["input_schema"]
            )
            for name, info in self.tools.items()
        ]
    
    async def call_tool(self, name: str, arguments: dict):
        """Call a registered tool by name"""
        if name not in self.tools:
            raise ValueError(f"Unknown tool: {name}")
        
        handler = self.tools[name]["handler"]
        
        # Call handler (support both sync and async)
        if inspect.iscoroutinefunction(handler):
            return await handler(arguments)
        else:
            return handler(arguments)
    
    def load_tools(self):
        """Dynamically discover and import all tool modules"""
        for _, module_name, _ in pkgutil.iter_modules(tools_pkg.__path__):
            full_name = f"{tools_pkg.__name__}.{module_name}"
            try:
                importlib.import_module(full_name)
                print(f"Loaded tool module: {module_name}", file=sys.stderr)
            except Exception as e:
                print(f"Error loading {module_name}: {e}", file=sys.stderr)
        
        print(f"Total tools registered: {len(self.tools)}", file=sys.stderr)
        print(f"Available tools: {list(self.tools.keys())}", file=sys.stderr)


# Global registry instance
registry = ToolRegistry()