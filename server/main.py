# server/main.py
from mcp.server import Server
from mcp.server.stdio import stdio_server
import asyncio
import sys
from server.registry import registry

# Create server
app = Server("anvil")

# Load all tools from the tools directory
print("Loading tools...", file=sys.stderr)
registry.load_tools()

# Register list_tools handler
@app.list_tools()
async def list_tools():
    """Return all registered tools"""
    return registry.get_tool_definitions()

# Register call_tool handler
@app.call_tool()
async def call_tool(name: str, arguments: dict):
    """Call a registered tool by name"""
    return await registry.call_tool(name, arguments)

# Start the server
async def main():
    """Main entry point for the MCP server"""
    print("Starting Anvil MCP server...", file=sys.stderr)
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream, 
            write_stream, 
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())