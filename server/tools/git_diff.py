# server/tools/git_diff.py
import subprocess
from mcp.types import TextContent
from server.registry import registry


@registry.register(
    name="git_diff",
    description="Show git diff of changes. Can show unstaged, staged, or both.",
    input_schema={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to git repository",
                "default": "."
            },
            "mode": {
                "type": "string",
                "enum": ["unstaged", "staged", "both"],
                "description": "What changes to show",
                "default": "unstaged"
            },
            "files": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Specific files to diff. If empty, shows all changes.",
                "default": []
            },
            "compact": {
                "type": "boolean",
                "description": "Show compact diff (stat only)",
                "default": False
            }
        }
    }
)
def git_diff(arguments: dict) -> list[TextContent]:
    """Show git diff"""
    path = arguments.get("path", ".")
    mode = arguments.get("mode", "unstaged")
    files = arguments.get("files", [])
    compact = arguments.get("compact", False)
    
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
        
        output_lines = []
        
        # Build diff command
        if mode == "unstaged":
            cmd = ["git", "diff"]
            if compact:
                cmd.append("--stat")
            cmd.extend(files)
            
            diff_result = subprocess.run(
                cmd,
                cwd=path,
                capture_output=True,
                text=True
            )
            
            if diff_result.returncode != 0:
                return [TextContent(type="text", text=f"Error getting diff: {diff_result.stderr}")]
            
            if diff_result.stdout.strip():
                output_lines.append("=== UNSTAGED CHANGES ===\n")
                output_lines.append(diff_result.stdout)
            else:
                output_lines.append("No unstaged changes")
        
        elif mode == "staged":
            cmd = ["git", "diff", "--cached"]
            if compact:
                cmd.append("--stat")
            cmd.extend(files)
            
            diff_result = subprocess.run(
                cmd,
                cwd=path,
                capture_output=True,
                text=True
            )
            
            if diff_result.returncode != 0:
                return [TextContent(type="text", text=f"Error getting diff: {diff_result.stderr}")]
            
            if diff_result.stdout.strip():
                output_lines.append("=== STAGED CHANGES ===\n")
                output_lines.append(diff_result.stdout)
            else:
                output_lines.append("No staged changes")
        
        elif mode == "both":
            # Unstaged
            cmd_unstaged = ["git", "diff"]
            if compact:
                cmd_unstaged.append("--stat")
            cmd_unstaged.extend(files)
            
            unstaged_result = subprocess.run(
                cmd_unstaged,
                cwd=path,
                capture_output=True,
                text=True
            )
            
            # Staged
            cmd_staged = ["git", "diff", "--cached"]
            if compact:
                cmd_staged.append("--stat")
            cmd_staged.extend(files)
            
            staged_result = subprocess.run(
                cmd_staged,
                cwd=path,
                capture_output=True,
                text=True
            )
            
            if unstaged_result.stdout.strip():
                output_lines.append("=== UNSTAGED CHANGES ===\n")
                output_lines.append(unstaged_result.stdout)
                output_lines.append("\n")
            else:
                output_lines.append("No unstaged changes\n")
            
            if staged_result.stdout.strip():
                output_lines.append("=== STAGED CHANGES ===\n")
                output_lines.append(staged_result.stdout)
            else:
                output_lines.append("No staged changes")
        
        return [TextContent(type="text", text="".join(output_lines))]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error getting diff: {str(e)}")]
