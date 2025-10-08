# server/tools/git_log.py
import subprocess
from mcp.types import TextContent
from server.registry import registry


@registry.register(
    name="git_log",
    description="Show git commit history with clean formatting",
    input_schema={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to git repository",
                "default": "."
            },
            "count": {
                "type": "integer",
                "description": "Number of commits to show",
                "default": 10
            },
            "author": {
                "type": "string",
                "description": "Filter by author name or email"
            },
            "since": {
                "type": "string",
                "description": "Show commits since date (e.g., '2 weeks ago', '2024-01-01')"
            },
            "oneline": {
                "type": "boolean",
                "description": "Show compact one-line format",
                "default": True
            }
        }
    }
)
def git_log(arguments: dict) -> list[TextContent]:
    """Show git commit history"""
    path = arguments.get("path", ".")
    count = arguments.get("count", 10)
    author = arguments.get("author")
    since = arguments.get("since")
    oneline = arguments.get("oneline", True)
    
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
        
        # Build log command
        if oneline:
            cmd = ["git", "log", f"-{count}", "--oneline", "--decorate", "--graph"]
        else:
            cmd = ["git", "log", f"-{count}", "--pretty=format:%h - %an, %ar : %s", "--decorate", "--graph"]
        
        # Add filters
        if author:
            cmd.extend(["--author", author])
        
        if since:
            cmd.extend(["--since", since])
        
        log_result = subprocess.run(
            cmd,
            cwd=path,
            capture_output=True,
            text=True
        )
        
        if log_result.returncode != 0:
            return [TextContent(type="text", text=f"Error getting log: {log_result.stderr}")]
        
        if not log_result.stdout.strip():
            return [TextContent(type="text", text="No commits found")]
        
        output = f"Last {count} commits:\n\n"
        output += log_result.stdout
        
        # Add summary
        total_result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=path,
            capture_output=True,
            text=True
        )
        
        if total_result.returncode == 0:
            total_commits = total_result.stdout.strip()
            output += f"\n\nTotal commits: {total_commits}"
        
        return [TextContent(type="text", text=output)]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error getting log: {str(e)}")]
