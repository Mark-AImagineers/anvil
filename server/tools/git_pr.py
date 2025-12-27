# server/tools/git_pr.py
"""Pull Request / Merge Request tools for GitHub and GitLab"""
import subprocess
import os
from mcp.types import TextContent
from server.registry import registry


def _get_env():
    """Get environment with local bin in PATH"""
    env = os.environ.copy()
    local_bin = os.path.expanduser("~/.local/bin")
    if local_bin not in env.get("PATH", ""):
        env["PATH"] = f"{local_bin}:{env.get('PATH', '')}"
    return env


def _detect_platform(path: str = ".") -> tuple[str, str | None]:
    """Detect if repo is GitHub or GitLab based on remotes"""
    try:
        result = subprocess.run(
            ["git", "remote", "-v"],
            cwd=path,
            capture_output=True,
            text=True
        )
        output = result.stdout.lower()
        if "github.com" in output:
            return "github", None
        elif "gitlab" in output:
            # Extract GitLab host
            for line in result.stdout.split("\n"):
                if "gitlab" in line.lower():
                    # Parse URL to get host
                    if "@" in line:  # SSH format
                        host = line.split("@")[1].split(":")[0]
                    else:  # HTTPS format
                        parts = line.split("//")
                        if len(parts) > 1:
                            host = parts[1].split("/")[0]
                        else:
                            host = "gitlab.com"
                    if host != "gitlab.com":
                        return "gitlab", host
                    return "gitlab", None
        return "github", None  # Default to GitHub
    except Exception:
        return "github", None


@registry.register(
    name="git_pr_create",
    description="Create a pull request (GitHub) or merge request (GitLab)",
    input_schema={
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "PR/MR title"
            },
            "body": {
                "type": "string",
                "description": "PR/MR description body",
                "default": ""
            },
            "base": {
                "type": "string",
                "description": "Base branch to merge into (default: main/master)",
                "default": ""
            },
            "head": {
                "type": "string",
                "description": "Head branch with changes (default: current branch)",
                "default": ""
            },
            "draft": {
                "type": "boolean",
                "description": "Create as draft PR/MR",
                "default": False
            },
            "platform": {
                "type": "string",
                "enum": ["auto", "github", "gitlab"],
                "description": "Platform to use (auto-detects from remote)",
                "default": "auto"
            },
            "gitlab_host": {
                "type": "string",
                "description": "GitLab host for self-hosted instances",
                "default": ""
            },
            "path": {
                "type": "string",
                "description": "Path to git repository",
                "default": "."
            }
        },
        "required": ["title"]
    }
)
def git_pr_create(arguments: dict) -> list[TextContent]:
    """Create a pull request or merge request"""
    title = arguments.get("title")
    body = arguments.get("body", "")
    base = arguments.get("base", "")
    head = arguments.get("head", "")
    draft = arguments.get("draft", False)
    platform = arguments.get("platform", "auto")
    gitlab_host = arguments.get("gitlab_host", "")
    path = arguments.get("path", ".")

    env = _get_env()

    # Auto-detect platform if needed
    if platform == "auto":
        platform, detected_host = _detect_platform(path)
        if detected_host and not gitlab_host:
            gitlab_host = detected_host

    try:
        if platform == "github":
            cmd = ["gh", "pr", "create", "--title", title]
            if body:
                cmd.extend(["--body", body])
            if base:
                cmd.extend(["--base", base])
            if head:
                cmd.extend(["--head", head])
            if draft:
                cmd.append("--draft")
        else:
            cmd = ["glab", "mr", "create", "--title", title, "--yes"]
            if body:
                cmd.extend(["--description", body])
            if base:
                cmd.extend(["--target-branch", base])
            if head:
                cmd.extend(["--source-branch", head])
            if draft:
                cmd.append("--draft")
            if gitlab_host:
                env["GITLAB_HOST"] = gitlab_host

        result = subprocess.run(cmd, cwd=path, capture_output=True, text=True, env=env)

        if result.returncode != 0:
            return [TextContent(type="text", text=f"Error: {result.stderr.strip()}")]

        return [TextContent(type="text", text=f"✅ Created {'PR' if platform == 'github' else 'MR'}:\n{result.stdout.strip()}")]

    except FileNotFoundError:
        cli = "gh" if platform == "github" else "glab"
        return [TextContent(type="text", text=f"Error: '{cli}' CLI not found")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


@registry.register(
    name="git_pr_list",
    description="List pull requests (GitHub) or merge requests (GitLab)",
    input_schema={
        "type": "object",
        "properties": {
            "state": {
                "type": "string",
                "enum": ["open", "closed", "merged", "all"],
                "description": "Filter by state",
                "default": "open"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number to list",
                "default": 20
            },
            "author": {
                "type": "string",
                "description": "Filter by author username",
                "default": ""
            },
            "platform": {
                "type": "string",
                "enum": ["auto", "github", "gitlab"],
                "default": "auto"
            },
            "gitlab_host": {
                "type": "string",
                "default": ""
            },
            "path": {
                "type": "string",
                "default": "."
            }
        }
    }
)
def git_pr_list(arguments: dict) -> list[TextContent]:
    """List pull requests or merge requests"""
    state = arguments.get("state", "open")
    limit = arguments.get("limit", 20)
    author = arguments.get("author", "")
    platform = arguments.get("platform", "auto")
    gitlab_host = arguments.get("gitlab_host", "")
    path = arguments.get("path", ".")

    env = _get_env()

    if platform == "auto":
        platform, detected_host = _detect_platform(path)
        if detected_host and not gitlab_host:
            gitlab_host = detected_host

    try:
        if platform == "github":
            cmd = ["gh", "pr", "list", "--limit", str(limit)]
            if state != "all":
                cmd.extend(["--state", state])
            if author:
                cmd.extend(["--author", author])
        else:
            cmd = ["glab", "mr", "list", "--per-page", str(limit)]
            if state == "open":
                cmd.extend(["--state", "opened"])
            elif state != "all":
                cmd.extend(["--state", state])
            if author:
                cmd.extend(["--author", author])
            if gitlab_host:
                env["GITLAB_HOST"] = gitlab_host

        result = subprocess.run(cmd, cwd=path, capture_output=True, text=True, env=env)

        if result.returncode != 0:
            return [TextContent(type="text", text=f"Error: {result.stderr.strip()}")]

        output = result.stdout.strip() or f"No {'PRs' if platform == 'github' else 'MRs'} found"
        return [TextContent(type="text", text=output)]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


@registry.register(
    name="git_pr_view",
    description="View details of a pull request (GitHub) or merge request (GitLab)",
    input_schema={
        "type": "object",
        "properties": {
            "number": {
                "type": "integer",
                "description": "PR/MR number"
            },
            "web": {
                "type": "boolean",
                "description": "Open in web browser",
                "default": False
            },
            "platform": {
                "type": "string",
                "enum": ["auto", "github", "gitlab"],
                "default": "auto"
            },
            "gitlab_host": {
                "type": "string",
                "default": ""
            },
            "path": {
                "type": "string",
                "default": "."
            }
        },
        "required": ["number"]
    }
)
def git_pr_view(arguments: dict) -> list[TextContent]:
    """View a pull request or merge request"""
    number = arguments.get("number")
    web = arguments.get("web", False)
    platform = arguments.get("platform", "auto")
    gitlab_host = arguments.get("gitlab_host", "")
    path = arguments.get("path", ".")

    env = _get_env()

    if platform == "auto":
        platform, detected_host = _detect_platform(path)
        if detected_host and not gitlab_host:
            gitlab_host = detected_host

    try:
        if platform == "github":
            cmd = ["gh", "pr", "view", str(number)]
            if web:
                cmd.append("--web")
        else:
            cmd = ["glab", "mr", "view", str(number)]
            if web:
                cmd.append("--web")
            if gitlab_host:
                env["GITLAB_HOST"] = gitlab_host

        result = subprocess.run(cmd, cwd=path, capture_output=True, text=True, env=env)

        if result.returncode != 0:
            return [TextContent(type="text", text=f"Error: {result.stderr.strip()}")]

        return [TextContent(type="text", text=result.stdout.strip())]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


@registry.register(
    name="git_pr_merge",
    description="Merge a pull request (GitHub) or merge request (GitLab)",
    input_schema={
        "type": "object",
        "properties": {
            "number": {
                "type": "integer",
                "description": "PR/MR number"
            },
            "method": {
                "type": "string",
                "enum": ["merge", "squash", "rebase"],
                "description": "Merge method",
                "default": "merge"
            },
            "delete_branch": {
                "type": "boolean",
                "description": "Delete source branch after merge",
                "default": True
            },
            "platform": {
                "type": "string",
                "enum": ["auto", "github", "gitlab"],
                "default": "auto"
            },
            "gitlab_host": {
                "type": "string",
                "default": ""
            },
            "path": {
                "type": "string",
                "default": "."
            }
        },
        "required": ["number"]
    }
)
def git_pr_merge(arguments: dict) -> list[TextContent]:
    """Merge a pull request or merge request"""
    number = arguments.get("number")
    method = arguments.get("method", "merge")
    delete_branch = arguments.get("delete_branch", True)
    platform = arguments.get("platform", "auto")
    gitlab_host = arguments.get("gitlab_host", "")
    path = arguments.get("path", ".")

    env = _get_env()

    if platform == "auto":
        platform, detected_host = _detect_platform(path)
        if detected_host and not gitlab_host:
            gitlab_host = detected_host

    try:
        if platform == "github":
            cmd = ["gh", "pr", "merge", str(number)]
            if method == "squash":
                cmd.append("--squash")
            elif method == "rebase":
                cmd.append("--rebase")
            else:
                cmd.append("--merge")
            if delete_branch:
                cmd.append("--delete-branch")
        else:
            cmd = ["glab", "mr", "merge", str(number), "--yes"]
            if method == "squash":
                cmd.append("--squash")
            elif method == "rebase":
                cmd.append("--rebase")
            if delete_branch:
                cmd.append("--remove-source-branch")
            if gitlab_host:
                env["GITLAB_HOST"] = gitlab_host

        result = subprocess.run(cmd, cwd=path, capture_output=True, text=True, env=env)

        if result.returncode != 0:
            return [TextContent(type="text", text=f"Error: {result.stderr.strip()}")]

        return [TextContent(type="text", text=f"✅ Merged {'PR' if platform == 'github' else 'MR'} #{number}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


@registry.register(
    name="git_pr_checkout",
    description="Check out a pull request (GitHub) or merge request (GitLab) locally",
    input_schema={
        "type": "object",
        "properties": {
            "number": {
                "type": "integer",
                "description": "PR/MR number"
            },
            "platform": {
                "type": "string",
                "enum": ["auto", "github", "gitlab"],
                "default": "auto"
            },
            "gitlab_host": {
                "type": "string",
                "default": ""
            },
            "path": {
                "type": "string",
                "default": "."
            }
        },
        "required": ["number"]
    }
)
def git_pr_checkout(arguments: dict) -> list[TextContent]:
    """Check out a pull request or merge request"""
    number = arguments.get("number")
    platform = arguments.get("platform", "auto")
    gitlab_host = arguments.get("gitlab_host", "")
    path = arguments.get("path", ".")

    env = _get_env()

    if platform == "auto":
        platform, detected_host = _detect_platform(path)
        if detected_host and not gitlab_host:
            gitlab_host = detected_host

    try:
        if platform == "github":
            cmd = ["gh", "pr", "checkout", str(number)]
        else:
            cmd = ["glab", "mr", "checkout", str(number)]
            if gitlab_host:
                env["GITLAB_HOST"] = gitlab_host

        result = subprocess.run(cmd, cwd=path, capture_output=True, text=True, env=env)

        if result.returncode != 0:
            return [TextContent(type="text", text=f"Error: {result.stderr.strip()}")]

        return [TextContent(type="text", text=f"✅ Checked out {'PR' if platform == 'github' else 'MR'} #{number}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


@registry.register(
    name="git_pr_comment",
    description="Add a comment to a pull request (GitHub) or merge request (GitLab)",
    input_schema={
        "type": "object",
        "properties": {
            "number": {
                "type": "integer",
                "description": "PR/MR number"
            },
            "body": {
                "type": "string",
                "description": "Comment text"
            },
            "platform": {
                "type": "string",
                "enum": ["auto", "github", "gitlab"],
                "default": "auto"
            },
            "gitlab_host": {
                "type": "string",
                "default": ""
            },
            "path": {
                "type": "string",
                "default": "."
            }
        },
        "required": ["number", "body"]
    }
)
def git_pr_comment(arguments: dict) -> list[TextContent]:
    """Add a comment to a pull request or merge request"""
    number = arguments.get("number")
    body = arguments.get("body")
    platform = arguments.get("platform", "auto")
    gitlab_host = arguments.get("gitlab_host", "")
    path = arguments.get("path", ".")

    env = _get_env()

    if platform == "auto":
        platform, detected_host = _detect_platform(path)
        if detected_host and not gitlab_host:
            gitlab_host = detected_host

    try:
        if platform == "github":
            cmd = ["gh", "pr", "comment", str(number), "--body", body]
        else:
            cmd = ["glab", "mr", "note", str(number), "--message", body]
            if gitlab_host:
                env["GITLAB_HOST"] = gitlab_host

        result = subprocess.run(cmd, cwd=path, capture_output=True, text=True, env=env)

        if result.returncode != 0:
            return [TextContent(type="text", text=f"Error: {result.stderr.strip()}")]

        return [TextContent(type="text", text=f"✅ Comment added to {'PR' if platform == 'github' else 'MR'} #{number}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


@registry.register(
    name="git_pr_review",
    description="Submit a review for a pull request (GitHub) or approve/revoke a merge request (GitLab)",
    input_schema={
        "type": "object",
        "properties": {
            "number": {
                "type": "integer",
                "description": "PR/MR number"
            },
            "action": {
                "type": "string",
                "enum": ["approve", "request-changes", "comment"],
                "description": "Review action",
                "default": "approve"
            },
            "body": {
                "type": "string",
                "description": "Review comment (required for request-changes)",
                "default": ""
            },
            "platform": {
                "type": "string",
                "enum": ["auto", "github", "gitlab"],
                "default": "auto"
            },
            "gitlab_host": {
                "type": "string",
                "default": ""
            },
            "path": {
                "type": "string",
                "default": "."
            }
        },
        "required": ["number"]
    }
)
def git_pr_review(arguments: dict) -> list[TextContent]:
    """Submit a review for a pull request or merge request"""
    number = arguments.get("number")
    action = arguments.get("action", "approve")
    body = arguments.get("body", "")
    platform = arguments.get("platform", "auto")
    gitlab_host = arguments.get("gitlab_host", "")
    path = arguments.get("path", ".")

    env = _get_env()

    if platform == "auto":
        platform, detected_host = _detect_platform(path)
        if detected_host and not gitlab_host:
            gitlab_host = detected_host

    try:
        if platform == "github":
            cmd = ["gh", "pr", "review", str(number)]
            if action == "approve":
                cmd.append("--approve")
            elif action == "request-changes":
                cmd.append("--request-changes")
            else:
                cmd.append("--comment")
            if body:
                cmd.extend(["--body", body])
        else:
            if gitlab_host:
                env["GITLAB_HOST"] = gitlab_host
            if action == "approve":
                cmd = ["glab", "mr", "approve", str(number)]
            elif action == "request-changes":
                # GitLab doesn't have request-changes, use note instead
                cmd = ["glab", "mr", "note", str(number), "--message", body or "Changes requested"]
            else:
                cmd = ["glab", "mr", "note", str(number), "--message", body or "Comment"]

        result = subprocess.run(cmd, cwd=path, capture_output=True, text=True, env=env)

        if result.returncode != 0:
            return [TextContent(type="text", text=f"Error: {result.stderr.strip()}")]

        return [TextContent(type="text", text=f"✅ Review submitted for {'PR' if platform == 'github' else 'MR'} #{number}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


@registry.register(
    name="git_pr_close",
    description="Close a pull request (GitHub) or merge request (GitLab) without merging",
    input_schema={
        "type": "object",
        "properties": {
            "number": {
                "type": "integer",
                "description": "PR/MR number"
            },
            "platform": {
                "type": "string",
                "enum": ["auto", "github", "gitlab"],
                "default": "auto"
            },
            "gitlab_host": {
                "type": "string",
                "default": ""
            },
            "path": {
                "type": "string",
                "default": "."
            }
        },
        "required": ["number"]
    }
)
def git_pr_close(arguments: dict) -> list[TextContent]:
    """Close a pull request or merge request"""
    number = arguments.get("number")
    platform = arguments.get("platform", "auto")
    gitlab_host = arguments.get("gitlab_host", "")
    path = arguments.get("path", ".")

    env = _get_env()

    if platform == "auto":
        platform, detected_host = _detect_platform(path)
        if detected_host and not gitlab_host:
            gitlab_host = detected_host

    try:
        if platform == "github":
            cmd = ["gh", "pr", "close", str(number)]
        else:
            cmd = ["glab", "mr", "close", str(number)]
            if gitlab_host:
                env["GITLAB_HOST"] = gitlab_host

        result = subprocess.run(cmd, cwd=path, capture_output=True, text=True, env=env)

        if result.returncode != 0:
            return [TextContent(type="text", text=f"Error: {result.stderr.strip()}")]

        return [TextContent(type="text", text=f"✅ Closed {'PR' if platform == 'github' else 'MR'} #{number}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]
