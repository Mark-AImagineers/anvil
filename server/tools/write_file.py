# server/tools/write_file.py
from mcp.types import TextContent
from server.registry import registry


@registry.register(
    name="write_file",
    description="Write content to a file",
    input_schema={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to write"
            },
            "content": {
                "type": "string",
                "description": "Content to write to the file"
            }
        },
        "required": ["path", "content"]
    }
)
def write_file(arguments: dict) -> list[TextContent]:
    """Write content to a file"""
    path = arguments.get("path")
    content = arguments.get("content")
    
    if not path or content is None:
        return [TextContent(type="text", text="Error: path and content are required")]
    
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return [TextContent(type="text", text=f"Successfully wrote to {path}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error writing file: {str(e)}")]
