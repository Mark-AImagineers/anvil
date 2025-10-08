import asyncio
import json
import sys

from server.registry import load_tools

async def main():
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await asyncio.get_running_loop().connect_read_pipe(lambda: protocol, sys.stdin)
    writer_transport, writer_protocol = await asyncio.get_running_loop().connect_write_pipe(asyncio.streams.FlowControlMixin, sys.stdout)
    writer = asyncio.StreamWriter(writer_transport, writer_protocol, reader, asyncio.get_running_loop())

    print("Anvil MCP server started.", file=sys.stderr)
    tools = load_tools()
    print(f"Loaded {len(tools)} tool(s).", file=sys.stderr)

    while True:
        line = await reader.readline()
        if not line:
            break

        try:
            message = json.loads(line.decode().strip())
            response = await handle_message(message, tools)
            if response:
                writer.write((json.dumps(response) + "\n").encode())
                await writer.drain()
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)

async def handle_message(message, tools):
    method = message.get("method")
    id_ = message.get("id")

    if method == "initialize":
        tools_info = [
            {
                "name": getattr(t, "name", "unknown"),
                "description": getattr(t, "description", ""),
            }
            for t in tools
        ]

        return {
            "jsonrpc": "2.0",
            "id": id_,
            "result": {
                "serverInfo": {
                    "name": "Anvil",
                    "version": "0.1.0"
                },
                "capabilities": {
                    "tools": tools_info
                }
            }
        }
    
    elif method == "ping":
        return {
            "jsonrpc": "2.0",
            "id": id_,
            "result": "pong"
        }
    
    elif method == "run_tool":
        params = message.get("params", {})
        tool_name = params.get("name")
        tools_args = params.get("args", {})

        for tool in tools:
            if getattr(tool, "name", None) == tool_name:
                try:
                    result = tool.run(tools_args)
                    return {
                        "jsonrpc": "2.0",
                        "id": id_,
                        "result": result
                    }
                except Exception as e:
                    return {
                        "jsonrpc": "2.0",
                        "id": id_,
                        "error": {"code": -32000, "message": str(e)}
                    }
    
    return {
        "jsonrpc": "2.0",
        "id": id_,
        "error": {
            "code": -32601,
            "message": f"Unknown method: {method}"
        }
    }

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Anvil MCP server stopped.", file=sys.stderr)