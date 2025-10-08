# server/tools/git_branch.py
import subprocess
from mcp.types import TextContent
from server.registry import registry


@registry.register(
    name="git_branch",
    description="List, create, switch, or delete git branches",
    input_schema={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to git repository",
                "default": "."
            },
            "action": {
                "type": "string",
                "enum": ["list", "create", "switch", "delete"],
                "description": "Action to perform",
                "default": "list"
            },
            "branch_name": {
                "type": "string",
                "description": "Branch name (required for create, switch, delete)"
            },
            "force": {
                "type": "boolean",
                "description": "Force delete branch (for delete action)",
                "default": False
            }
        }
    }
)
def git_branch(arguments: dict) -> list[TextContent]:
    """Manage git branches"""
    path = arguments.get("path", ".")
    action = arguments.get("action", "list")
    branch_name = arguments.get("branch_name")
    force = arguments.get("force", False)
    
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
        
        if action == "list":
            # List all branches
            branch_result = subprocess.run(
                ["git", "branch", "-a", "-vv"],
                cwd=path,
                capture_output=True,
                text=True
            )
            
            if branch_result.returncode != 0:
                return [TextContent(type="text", text=f"Error listing branches: {branch_result.stderr}")]
            
            output = "Branches:\n\n"
            output += branch_result.stdout
            output += "\n\nLegend:\n"
            output += "  * = Current branch\n"
            output += "  remotes/ = Remote branches\n"
            
            return [TextContent(type="text", text=output)]
        
        elif action == "create":
            if not branch_name:
                return [TextContent(type="text", text="Error: branch_name is required for create action")]
            
            # Create new branch
            create_result = subprocess.run(
                ["git", "branch", branch_name],
                cwd=path,
                capture_output=True,
                text=True
            )
            
            if create_result.returncode != 0:
                return [TextContent(type="text", text=f"Error creating branch: {create_result.stderr}")]
            
            return [TextContent(type="text", text=f"✓ Created branch: {branch_name}")]
        
        elif action == "switch":
            if not branch_name:
                return [TextContent(type="text", text="Error: branch_name is required for switch action")]
            
            # Switch to branch
            switch_result = subprocess.run(
                ["git", "checkout", branch_name],
                cwd=path,
                capture_output=True,
                text=True
            )
            
            if switch_result.returncode != 0:
                return [TextContent(type="text", text=f"Error switching branch: {switch_result.stderr}")]
            
            return [TextContent(type="text", text=f"✓ Switched to branch: {branch_name}")]
        
        elif action == "delete":
            if not branch_name:
                return [TextContent(type="text", text="Error: branch_name is required for delete action")]
            
            # Delete branch
            delete_flag = "-D" if force else "-d"
            delete_result = subprocess.run(
                ["git", "branch", delete_flag, branch_name],
                cwd=path,
                capture_output=True,
                text=True
            )
            
            if delete_result.returncode != 0:
                return [TextContent(type="text", text=f"Error deleting branch: {delete_result.stderr}")]
            
            return [TextContent(type="text", text=f"✓ Deleted branch: {branch_name}")]
        
        else:
            return [TextContent(type="text", text=f"Error: Unknown action: {action}")]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error managing branches: {str(e)}")]
