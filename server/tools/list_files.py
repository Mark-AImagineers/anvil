# server/tools/list_files.py
import os
from mcp.types import TextContent
from server.registry import registry


@registry.register(
    name="list_files",
    description="List files and directories within a given path",
    input_schema={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Directory path to list files from",
                "default": "."
            }
        },
        "required": []
    }
)
def list_files(arguments: dict) -> list[TextContent]:
    """List files in the specified directory"""
    path = arguments.get("path", ".")
    
    try:
        items = os.listdir(path)
        abs_path = os.path.abspath(path)
        result = f"Path: {abs_path}\n\nFiles and directories:\n" + "\n".join(items)
        return [TextContent(type="text", text=result)]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]
