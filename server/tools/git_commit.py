# server/tools/git_commit.py
import subprocess
from mcp.types import TextContent
from server.registry import registry


@registry.register(
    name="git_commit",
    description="Stage and commit changes with a message. Optionally push to remote.",
    input_schema={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to git repository",
                "default": "."
            },
            "message": {
                "type": "string",
                "description": "Commit message"
            },
            "files": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Specific files to stage. If empty, stages all changes.",
                "default": []
            },
            "push": {
                "type": "boolean",
                "description": "Push to remote after committing",
                "default": False
            }
        },
        "required": ["message"]
    }
)
def git_commit(arguments: dict) -> list[TextContent]:
    """Stage and commit changes"""
    path = arguments.get("path", ".")
    message = arguments.get("message")
    files = arguments.get("files", [])
    push = arguments.get("push", False)
    
    if not message:
        return [TextContent(type="text", text="Error: Commit message is required")]
    
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
        
        # Stage files
        if files:
            # Stage specific files
            add_result = subprocess.run(
                ["git", "add"] + files,
                cwd=path,
                capture_output=True,
                text=True
            )
            if add_result.returncode != 0:
                return [TextContent(type="text", text=f"Error staging files: {add_result.stderr}")]
            output_lines.append(f"Staged {len(files)} file(s)")
        else:
            # Stage all changes
            add_result = subprocess.run(
                ["git", "add", "-A"],
                cwd=path,
                capture_output=True,
                text=True
            )
            if add_result.returncode != 0:
                return [TextContent(type="text", text=f"Error staging files: {add_result.stderr}")]
            output_lines.append("Staged all changes")
        
        # Commit
        commit_result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=path,
            capture_output=True,
            text=True
        )
        
        if commit_result.returncode != 0:
            # Check if there's nothing to commit
            if "nothing to commit" in commit_result.stdout.lower():
                return [TextContent(type="text", text="Nothing to commit, working tree clean")]
            return [TextContent(type="text", text=f"Error committing: {commit_result.stderr}")]
        
        output_lines.append(f"✓ Committed: {message}")
        
        # Extract commit hash
        hash_result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=path,
            capture_output=True,
            text=True
        )
        if hash_result.returncode == 0:
            commit_hash = hash_result.stdout.strip()
            output_lines.append(f"  Commit: {commit_hash}")
        
        # Push if requested
        if push:
            push_result = subprocess.run(
                ["git", "push"],
                cwd=path,
                capture_output=True,
                text=True
            )
            
            if push_result.returncode != 0:
                output_lines.append(f"⚠ Push failed: {push_result.stderr}")
            else:
                output_lines.append("✓ Pushed to remote")
        
        return [TextContent(type="text", text="\n".join(output_lines))]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error during commit: {str(e)}")]
