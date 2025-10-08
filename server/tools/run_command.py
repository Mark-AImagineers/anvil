# server/tools/run_command.py
import subprocess
from mcp.types import TextContent
from server.registry import registry


@registry.register(
    name="run_command",
    description="Execute a shell command and return its output",
    input_schema={
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to execute"
            },
            "cwd": {
                "type": "string",
                "description": "Working directory for the command",
                "default": "."
            }
        },
        "required": ["command"]
    }
)
def run_command(arguments: dict) -> list[TextContent]:
    """Execute a shell command"""
    command = arguments.get("command")
    cwd = arguments.get("cwd", ".")
    
    if not command:
        return [TextContent(type="text", text="Error: command is required")]
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = f"Exit code: {result.returncode}\n\n"
        if result.stdout:
            output += f"STDOUT:\n{result.stdout}\n"
        if result.stderr:
            output += f"STDERR:\n{result.stderr}"
            
        return [TextContent(type="text", text=output)]
    except subprocess.TimeoutExpired:
        return [TextContent(type="text", text="Error: Command timed out after 30 seconds")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error executing command: {str(e)}")]
