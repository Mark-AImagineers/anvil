# server/tools/read_file.py
from mcp.types import TextContent
from server.registry import registry


@registry.register(
    name="read_file",
    description="Read the contents of a file",
    input_schema={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to read"
            }
        },
        "required": ["path"]
    }
)
def read_file(arguments: dict) -> list[TextContent]:
    """Read and return file contents"""
    path = arguments.get("path")
    
    if not path:
        return [TextContent(type="text", text="Error: path is required")]
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return [TextContent(type="text", text=content)]
    except Exception as e:
        return [TextContent(type="text", text=f"Error reading file: {str(e)}")]
