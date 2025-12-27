# server/tools/git_issue.py
"""Issue management tools for GitHub and GitLab"""
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
            for line in result.stdout.split("\n"):
                if "gitlab" in line.lower():
                    if "@" in line:
                        host = line.split("@")[1].split(":")[0]
                    else:
                        parts = line.split("//")
                        if len(parts) > 1:
                            host = parts[1].split("/")[0]
                        else:
                            host = "gitlab.com"
                    if host != "gitlab.com":
                        return "gitlab", host
                    return "gitlab", None
        return "github", None
    except Exception:
        return "github", None


@registry.register(
    name="git_issue_create",
    description="Create a new issue on GitHub or GitLab",
    input_schema={
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Issue title"
            },
            "body": {
                "type": "string",
                "description": "Issue description",
                "default": ""
            },
            "labels": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Labels to apply",
                "default": []
            },
            "assignees": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Usernames to assign",
                "default": []
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
        "required": ["title"]
    }
)
def git_issue_create(arguments: dict) -> list[TextContent]:
    """Create a new issue"""
    title = arguments.get("title")
    body = arguments.get("body", "")
    labels = arguments.get("labels", [])
    assignees = arguments.get("assignees", [])
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
            cmd = ["gh", "issue", "create", "--title", title]
            if body:
                cmd.extend(["--body", body])
            for label in labels:
                cmd.extend(["--label", label])
            for assignee in assignees:
                cmd.extend(["--assignee", assignee])
        else:
            cmd = ["glab", "issue", "create", "--title", title, "--yes"]
            if body:
                cmd.extend(["--description", body])
            if labels:
                cmd.extend(["--label", ",".join(labels)])
            for assignee in assignees:
                cmd.extend(["--assignee", assignee])
            if gitlab_host:
                env["GITLAB_HOST"] = gitlab_host

        result = subprocess.run(cmd, cwd=path, capture_output=True, text=True, env=env)

        if result.returncode != 0:
            return [TextContent(type="text", text=f"Error: {result.stderr.strip()}")]

        return [TextContent(type="text", text=f"✅ Issue created:\n{result.stdout.strip()}")]

    except FileNotFoundError:
        cli = "gh" if platform == "github" else "glab"
        return [TextContent(type="text", text=f"Error: '{cli}' CLI not found")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


@registry.register(
    name="git_issue_list",
    description="List issues on GitHub or GitLab",
    input_schema={
        "type": "object",
        "properties": {
            "state": {
                "type": "string",
                "enum": ["open", "closed", "all"],
                "description": "Filter by state",
                "default": "open"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number to list",
                "default": 20
            },
            "labels": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Filter by labels",
                "default": []
            },
            "assignee": {
                "type": "string",
                "description": "Filter by assignee",
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
def git_issue_list(arguments: dict) -> list[TextContent]:
    """List issues"""
    state = arguments.get("state", "open")
    limit = arguments.get("limit", 20)
    labels = arguments.get("labels", [])
    assignee = arguments.get("assignee", "")
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
            cmd = ["gh", "issue", "list", "--limit", str(limit)]
            if state != "all":
                cmd.extend(["--state", state])
            for label in labels:
                cmd.extend(["--label", label])
            if assignee:
                cmd.extend(["--assignee", assignee])
        else:
            cmd = ["glab", "issue", "list", "--per-page", str(limit)]
            if state == "open":
                cmd.extend(["--state", "opened"])
            elif state != "all":
                cmd.extend(["--state", state])
            if labels:
                cmd.extend(["--label", ",".join(labels)])
            if assignee:
                cmd.extend(["--assignee", assignee])
            if gitlab_host:
                env["GITLAB_HOST"] = gitlab_host

        result = subprocess.run(cmd, cwd=path, capture_output=True, text=True, env=env)

        if result.returncode != 0:
            return [TextContent(type="text", text=f"Error: {result.stderr.strip()}")]

        output = result.stdout.strip() or "No issues found"
        return [TextContent(type="text", text=output)]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


@registry.register(
    name="git_issue_view",
    description="View details of an issue on GitHub or GitLab",
    input_schema={
        "type": "object",
        "properties": {
            "number": {
                "type": "integer",
                "description": "Issue number"
            },
            "web": {
                "type": "boolean",
                "description": "Open in web browser",
                "default": False
            },
            "comments": {
                "type": "boolean",
                "description": "Show comments",
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
def git_issue_view(arguments: dict) -> list[TextContent]:
    """View an issue"""
    number = arguments.get("number")
    web = arguments.get("web", False)
    comments = arguments.get("comments", False)
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
            cmd = ["gh", "issue", "view", str(number)]
            if web:
                cmd.append("--web")
            if comments:
                cmd.append("--comments")
        else:
            cmd = ["glab", "issue", "view", str(number)]
            if web:
                cmd.append("--web")
            if comments:
                cmd.append("--comments")
            if gitlab_host:
                env["GITLAB_HOST"] = gitlab_host

        result = subprocess.run(cmd, cwd=path, capture_output=True, text=True, env=env)

        if result.returncode != 0:
            return [TextContent(type="text", text=f"Error: {result.stderr.strip()}")]

        return [TextContent(type="text", text=result.stdout.strip())]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


@registry.register(
    name="git_issue_close",
    description="Close an issue on GitHub or GitLab",
    input_schema={
        "type": "object",
        "properties": {
            "number": {
                "type": "integer",
                "description": "Issue number"
            },
            "comment": {
                "type": "string",
                "description": "Closing comment",
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
def git_issue_close(arguments: dict) -> list[TextContent]:
    """Close an issue"""
    number = arguments.get("number")
    comment = arguments.get("comment", "")
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
            cmd = ["gh", "issue", "close", str(number)]
            if comment:
                cmd.extend(["--comment", comment])
        else:
            cmd = ["glab", "issue", "close", str(number)]
            if gitlab_host:
                env["GITLAB_HOST"] = gitlab_host

        result = subprocess.run(cmd, cwd=path, capture_output=True, text=True, env=env)

        if result.returncode != 0:
            return [TextContent(type="text", text=f"Error: {result.stderr.strip()}")]

        # Add comment separately for GitLab if provided
        if comment and platform == "gitlab":
            note_cmd = ["glab", "issue", "note", str(number), "--message", comment]
            subprocess.run(note_cmd, cwd=path, capture_output=True, text=True, env=env)

        return [TextContent(type="text", text=f"✅ Issue #{number} closed")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


@registry.register(
    name="git_issue_reopen",
    description="Reopen a closed issue on GitHub or GitLab",
    input_schema={
        "type": "object",
        "properties": {
            "number": {
                "type": "integer",
                "description": "Issue number"
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
def git_issue_reopen(arguments: dict) -> list[TextContent]:
    """Reopen an issue"""
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
            cmd = ["gh", "issue", "reopen", str(number)]
        else:
            cmd = ["glab", "issue", "reopen", str(number)]
            if gitlab_host:
                env["GITLAB_HOST"] = gitlab_host

        result = subprocess.run(cmd, cwd=path, capture_output=True, text=True, env=env)

        if result.returncode != 0:
            return [TextContent(type="text", text=f"Error: {result.stderr.strip()}")]

        return [TextContent(type="text", text=f"✅ Issue #{number} reopened")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


@registry.register(
    name="git_issue_comment",
    description="Add a comment to an issue on GitHub or GitLab",
    input_schema={
        "type": "object",
        "properties": {
            "number": {
                "type": "integer",
                "description": "Issue number"
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
def git_issue_comment(arguments: dict) -> list[TextContent]:
    """Add a comment to an issue"""
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
            cmd = ["gh", "issue", "comment", str(number), "--body", body]
        else:
            cmd = ["glab", "issue", "note", str(number), "--message", body]
            if gitlab_host:
                env["GITLAB_HOST"] = gitlab_host

        result = subprocess.run(cmd, cwd=path, capture_output=True, text=True, env=env)

        if result.returncode != 0:
            return [TextContent(type="text", text=f"Error: {result.stderr.strip()}")]

        return [TextContent(type="text", text=f"✅ Comment added to issue #{number}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


@registry.register(
    name="git_issue_edit",
    description="Edit an issue on GitHub or GitLab",
    input_schema={
        "type": "object",
        "properties": {
            "number": {
                "type": "integer",
                "description": "Issue number"
            },
            "title": {
                "type": "string",
                "description": "New title",
                "default": ""
            },
            "body": {
                "type": "string",
                "description": "New description",
                "default": ""
            },
            "add_labels": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Labels to add",
                "default": []
            },
            "remove_labels": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Labels to remove",
                "default": []
            },
            "add_assignees": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Assignees to add",
                "default": []
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
def git_issue_edit(arguments: dict) -> list[TextContent]:
    """Edit an issue"""
    number = arguments.get("number")
    title = arguments.get("title", "")
    body = arguments.get("body", "")
    add_labels = arguments.get("add_labels", [])
    remove_labels = arguments.get("remove_labels", [])
    add_assignees = arguments.get("add_assignees", [])
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
            cmd = ["gh", "issue", "edit", str(number)]
            if title:
                cmd.extend(["--title", title])
            if body:
                cmd.extend(["--body", body])
            for label in add_labels:
                cmd.extend(["--add-label", label])
            for label in remove_labels:
                cmd.extend(["--remove-label", label])
            for assignee in add_assignees:
                cmd.extend(["--add-assignee", assignee])
        else:
            cmd = ["glab", "issue", "update", str(number)]
            if title:
                cmd.extend(["--title", title])
            if body:
                cmd.extend(["--description", body])
            if add_labels:
                cmd.extend(["--label", ",".join(add_labels)])
            if add_assignees:
                cmd.extend(["--assignee", ",".join(add_assignees)])
            if gitlab_host:
                env["GITLAB_HOST"] = gitlab_host

        result = subprocess.run(cmd, cwd=path, capture_output=True, text=True, env=env)

        if result.returncode != 0:
            return [TextContent(type="text", text=f"Error: {result.stderr.strip()}")]

        return [TextContent(type="text", text=f"✅ Issue #{number} updated")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]
