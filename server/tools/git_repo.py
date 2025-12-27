# server/tools/git_repo.py
import subprocess
import os
from mcp.types import TextContent
from server.registry import registry


@registry.register(
    name="git_repo_create",
    description="Create a new repository on GitHub and/or GitLab. Can also initialize locally and push.",
    input_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Repository name (e.g., 'my-project')"
            },
            "description": {
                "type": "string",
                "description": "Repository description",
                "default": ""
            },
            "private": {
                "type": "boolean",
                "description": "Make repository private",
                "default": True
            },
            "platforms": {
                "type": "array",
                "items": {"type": "string", "enum": ["github", "gitlab"]},
                "description": "Platforms to create repo on",
                "default": ["github", "gitlab"]
            },
            "github_org": {
                "type": "string",
                "description": "GitHub organization (optional, uses personal account if not specified)",
                "default": ""
            },
            "gitlab_group": {
                "type": "string",
                "description": "GitLab group/namespace (optional, uses personal namespace if not specified)",
                "default": ""
            },
            "local_path": {
                "type": "string",
                "description": "Local path to initialize repo. If provided, will init and push.",
                "default": ""
            },
            "gitlab_host": {
                "type": "string",
                "description": "GitLab host URL (for self-hosted instances)",
                "default": ""
            }
        },
        "required": ["name"]
    }
)
def git_repo_create(arguments: dict) -> list[TextContent]:
    """Create repository on GitHub and/or GitLab"""
    name = arguments.get("name")
    description = arguments.get("description", "")
    private = arguments.get("private", True)
    platforms = arguments.get("platforms", ["github", "gitlab"])
    github_org = arguments.get("github_org", "")
    gitlab_group = arguments.get("gitlab_group", "")
    local_path = arguments.get("local_path", "")
    gitlab_host = arguments.get("gitlab_host", "")
    
    if not name:
        return [TextContent(type="text", text="Error: Repository name is required")]
    
    output_lines = []
    github_url = None
    gitlab_url = None
    
    # Ensure gh and glab are in PATH
    env = os.environ.copy()
    local_bin = os.path.expanduser("~/.local/bin")
    if local_bin not in env.get("PATH", ""):
        env["PATH"] = f"{local_bin}:{env.get('PATH', '')}"
    
    # Create on GitHub
    if "github" in platforms:
        try:
            # Build repo name with org if specified
            full_name = f"{github_org}/{name}" if github_org else name
            
            cmd = ["gh", "repo", "create", full_name]
            if private:
                cmd.append("--private")
            else:
                cmd.append("--public")
            if description:
                cmd.extend(["--description", description])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env
            )
            
            if result.returncode != 0:
                output_lines.append(f"❌ GitHub: {result.stderr.strip()}")
            else:
                github_url = result.stdout.strip()
                output_lines.append(f"✅ GitHub: {github_url}")
        except FileNotFoundError:
            output_lines.append("❌ GitHub: 'gh' CLI not found. Run: gh auth login")
        except Exception as e:
            output_lines.append(f"❌ GitHub: {str(e)}")
    
    # Create on GitLab
    if "gitlab" in platforms:
        try:
            cmd = ["glab", "repo", "create", name]
            if private:
                cmd.extend(["--private"])
            else:
                cmd.extend(["--public"])
            if description:
                cmd.extend(["--description", description])
            if gitlab_group:
                cmd.extend(["--group", gitlab_group])
            
            # Set GitLab host if specified
            cmd_env = env.copy()
            if gitlab_host:
                cmd_env["GITLAB_HOST"] = gitlab_host
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=cmd_env
            )
            
            if result.returncode != 0:
                output_lines.append(f"❌ GitLab: {result.stderr.strip()}")
            else:
                # Extract URL from output
                for line in result.stdout.split("\n"):
                    if "http" in line.lower():
                        gitlab_url = line.strip()
                        break
                output_lines.append(f"✅ GitLab: {gitlab_url or 'Created'}")
        except FileNotFoundError:
            output_lines.append("❌ GitLab: 'glab' CLI not found. Run: glab auth login")
        except Exception as e:
            output_lines.append(f"❌ GitLab: {str(e)}")
    
    # Initialize local repo if path provided
    if local_path:
        try:
            # Create directory if it doesn't exist
            os.makedirs(local_path, exist_ok=True)
            
            # Check if already a git repo
            git_dir = os.path.join(local_path, ".git")
            if not os.path.exists(git_dir):
                subprocess.run(["git", "init"], cwd=local_path, capture_output=True)
                output_lines.append(f"✅ Initialized git repo at {local_path}")
            
            # Add remotes
            if github_url:
                subprocess.run(
                    ["git", "remote", "add", "origin", github_url],
                    cwd=local_path,
                    capture_output=True
                )
                subprocess.run(
                    ["git", "remote", "add", "gh", github_url],
                    cwd=local_path,
                    capture_output=True
                )
                output_lines.append(f"✅ Added remote 'gh' → {github_url}")
            
            if gitlab_url:
                remote_name = "gl" if github_url else "origin"
                subprocess.run(
                    ["git", "remote", "add", remote_name, gitlab_url],
                    cwd=local_path,
                    capture_output=True
                )
                output_lines.append(f"✅ Added remote 'gl' → {gitlab_url}")
                
        except Exception as e:
            output_lines.append(f"❌ Local setup: {str(e)}")
    
    return [TextContent(type="text", text="\n".join(output_lines))]


@registry.register(
    name="git_repo_delete",
    description="Delete a repository from GitHub and/or GitLab. USE WITH CAUTION.",
    input_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Repository name or full path (e.g., 'my-project' or 'org/my-project')"
            },
            "platforms": {
                "type": "array",
                "items": {"type": "string", "enum": ["github", "gitlab"]},
                "description": "Platforms to delete repo from",
                "default": ["github"]
            },
            "confirm": {
                "type": "boolean",
                "description": "Must be true to confirm deletion",
                "default": False
            },
            "gitlab_host": {
                "type": "string",
                "description": "GitLab host URL (for self-hosted instances)",
                "default": ""
            }
        },
        "required": ["name", "confirm"]
    }
)
def git_repo_delete(arguments: dict) -> list[TextContent]:
    """Delete repository from GitHub and/or GitLab"""
    name = arguments.get("name")
    platforms = arguments.get("platforms", ["github"])
    confirm = arguments.get("confirm", False)
    gitlab_host = arguments.get("gitlab_host", "")
    
    if not name:
        return [TextContent(type="text", text="Error: Repository name is required")]
    
    if not confirm:
        return [TextContent(type="text", text="Error: Must set confirm=true to delete repository")]
    
    output_lines = []
    
    # Ensure gh and glab are in PATH
    env = os.environ.copy()
    local_bin = os.path.expanduser("~/.local/bin")
    if local_bin not in env.get("PATH", ""):
        env["PATH"] = f"{local_bin}:{env.get('PATH', '')}"
    
    # Delete from GitHub
    if "github" in platforms:
        try:
            result = subprocess.run(
                ["gh", "repo", "delete", name, "--yes"],
                capture_output=True,
                text=True,
                env=env
            )
            
            if result.returncode != 0:
                output_lines.append(f"❌ GitHub: {result.stderr.strip()}")
            else:
                output_lines.append(f"✅ GitHub: Deleted {name}")
        except FileNotFoundError:
            output_lines.append("❌ GitHub: 'gh' CLI not found")
        except Exception as e:
            output_lines.append(f"❌ GitHub: {str(e)}")
    
    # Delete from GitLab
    if "gitlab" in platforms:
        try:
            cmd_env = env.copy()
            if gitlab_host:
                cmd_env["GITLAB_HOST"] = gitlab_host
            
            result = subprocess.run(
                ["glab", "repo", "delete", name, "--yes"],
                capture_output=True,
                text=True,
                env=cmd_env
            )
            
            if result.returncode != 0:
                output_lines.append(f"❌ GitLab: {result.stderr.strip()}")
            else:
                output_lines.append(f"✅ GitLab: Deleted {name}")
        except FileNotFoundError:
            output_lines.append("❌ GitLab: 'glab' CLI not found")
        except Exception as e:
            output_lines.append(f"❌ GitLab: {str(e)}")
    
    return [TextContent(type="text", text="\n".join(output_lines))]


@registry.register(
    name="git_repo_list",
    description="List repositories from GitHub and/or GitLab",
    input_schema={
        "type": "object",
        "properties": {
            "platform": {
                "type": "string",
                "enum": ["github", "gitlab"],
                "description": "Platform to list repos from",
                "default": "github"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of repos to list",
                "default": 20
            },
            "gitlab_host": {
                "type": "string",
                "description": "GitLab host URL (for self-hosted instances)",
                "default": ""
            }
        }
    }
)
def git_repo_list(arguments: dict) -> list[TextContent]:
    """List repositories from GitHub or GitLab"""
    platform = arguments.get("platform", "github")
    limit = arguments.get("limit", 20)
    gitlab_host = arguments.get("gitlab_host", "")
    
    # Ensure gh and glab are in PATH
    env = os.environ.copy()
    local_bin = os.path.expanduser("~/.local/bin")
    if local_bin not in env.get("PATH", ""):
        env["PATH"] = f"{local_bin}:{env.get('PATH', '')}"
    
    try:
        if platform == "github":
            result = subprocess.run(
                ["gh", "repo", "list", "--limit", str(limit)],
                capture_output=True,
                text=True,
                env=env
            )
        else:
            cmd_env = env.copy()
            if gitlab_host:
                cmd_env["GITLAB_HOST"] = gitlab_host
            result = subprocess.run(
                ["glab", "repo", "list", "--per-page", str(limit)],
                capture_output=True,
                text=True,
                env=cmd_env
            )
        
        if result.returncode != 0:
            return [TextContent(type="text", text=f"Error: {result.stderr.strip()}")]
        
        return [TextContent(type="text", text=result.stdout.strip() or "No repositories found")]
    
    except FileNotFoundError:
        cli = "gh" if platform == "github" else "glab"
        return [TextContent(type="text", text=f"Error: '{cli}' CLI not found")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


@registry.register(
    name="git_repo_clone",
    description="Clone a repository from GitHub or GitLab",
    input_schema={
        "type": "object",
        "properties": {
            "repo": {
                "type": "string",
                "description": "Repository to clone (e.g., 'owner/repo' or full URL)"
            },
            "path": {
                "type": "string",
                "description": "Local path to clone to",
                "default": ""
            },
            "platform": {
                "type": "string",
                "enum": ["github", "gitlab"],
                "description": "Platform to clone from (if repo is not a full URL)",
                "default": "github"
            },
            "gitlab_host": {
                "type": "string",
                "description": "GitLab host URL (for self-hosted instances)",
                "default": ""
            }
        },
        "required": ["repo"]
    }
)
def git_repo_clone(arguments: dict) -> list[TextContent]:
    """Clone a repository"""
    repo = arguments.get("repo")
    path = arguments.get("path", "")
    platform = arguments.get("platform", "github")
    gitlab_host = arguments.get("gitlab_host", "")
    
    if not repo:
        return [TextContent(type="text", text="Error: Repository is required")]
    
    # Ensure gh and glab are in PATH
    env = os.environ.copy()
    local_bin = os.path.expanduser("~/.local/bin")
    if local_bin not in env.get("PATH", ""):
        env["PATH"] = f"{local_bin}:{env.get('PATH', '')}"
    
    try:
        if platform == "github" or "github.com" in repo:
            cmd = ["gh", "repo", "clone", repo]
            if path:
                cmd.append(path)
            result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        else:
            cmd_env = env.copy()
            if gitlab_host:
                cmd_env["GITLAB_HOST"] = gitlab_host
            cmd = ["glab", "repo", "clone", repo]
            if path:
                cmd.append(path)
            result = subprocess.run(cmd, capture_output=True, text=True, env=cmd_env)
        
        if result.returncode != 0:
            return [TextContent(type="text", text=f"Error: {result.stderr.strip()}")]
        
        return [TextContent(type="text", text=f"✅ Cloned {repo}" + (f" to {path}" if path else ""))]
    
    except FileNotFoundError:
        return [TextContent(type="text", text="Error: CLI not found")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]
