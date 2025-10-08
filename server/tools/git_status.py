# server/tools/git_status.py
import subprocess
from mcp.types import TextContent
from server.registry import registry


@registry.register(
    name="git_status",
    description="Get git repository status with clean, readable formatting",
    input_schema={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to git repository",
                "default": "."
            },
            "show_untracked": {
                "type": "boolean",
                "description": "Show untracked files",
                "default": True
            }
        }
    }
)
def git_status(arguments: dict) -> list[TextContent]:
    """Get formatted git status"""
    path = arguments.get("path", ".")
    show_untracked = arguments.get("show_untracked", True)
    
    try:
        # Check if it's a git repository
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=path,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return [TextContent(type="text", text=f"Error: Not a git repository: {path}")]
        
        # Get current branch
        branch_result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=path,
            capture_output=True,
            text=True
        )
        current_branch = branch_result.stdout.strip()
        
        # Get short status
        status_cmd = ["git", "status", "--short"]
        if not show_untracked:
            status_cmd.append("--untracked-files=no")
        
        status_result = subprocess.run(
            status_cmd,
            cwd=path,
            capture_output=True,
            text=True
        )
        
        # Get ahead/behind info
        tracking_result = subprocess.run(
            ["git", "rev-list", "--left-right", "--count", f"HEAD...@{{u}}"],
            cwd=path,
            capture_output=True,
            text=True
        )
        
        ahead_behind = ""
        if tracking_result.returncode == 0:
            counts = tracking_result.stdout.strip().split()
            if len(counts) == 2:
                ahead, behind = counts
                if ahead != "0" or behind != "0":
                    ahead_behind = f" [ahead {ahead}, behind {behind}]" if ahead != "0" and behind != "0" else \
                                  f" [ahead {ahead}]" if ahead != "0" else f" [behind {behind}]"
        
        # Format output
        output = f"On branch: {current_branch}{ahead_behind}\n\n"
        
        if status_result.stdout.strip():
            output += "Changes:\n"
            output += status_result.stdout
            
            # Add legend
            output += "\n\nLegend:\n"
            output += "  M  = Modified\n"
            output += "  A  = Added\n"
            output += "  D  = Deleted\n"
            output += "  R  = Renamed\n"
            output += "  ?? = Untracked\n"
        else:
            output += "✓ Working tree clean"
        
        return [TextContent(type="text", text=output)]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error getting git status: {str(e)}")]
