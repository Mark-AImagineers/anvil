# server/tools/git_pipeline.py
"""CI/CD Pipeline tools for GitHub Actions and GitLab CI"""
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
    name="git_pipeline_list",
    description="List CI/CD pipeline runs (GitHub Actions workflows or GitLab pipelines)",
    input_schema={
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Maximum number to list",
                "default": 10
            },
            "status": {
                "type": "string",
                "enum": ["all", "success", "failed", "running", "pending", "cancelled"],
                "description": "Filter by status",
                "default": "all"
            },
            "branch": {
                "type": "string",
                "description": "Filter by branch",
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
def git_pipeline_list(arguments: dict) -> list[TextContent]:
    """List pipeline runs"""
    limit = arguments.get("limit", 10)
    status = arguments.get("status", "all")
    branch = arguments.get("branch", "")
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
            cmd = ["gh", "run", "list", "--limit", str(limit)]
            if branch:
                cmd.extend(["--branch", branch])
            if status != "all":
                # Map status names
                status_map = {
                    "success": "success",
                    "failed": "failure",
                    "running": "in_progress",
                    "pending": "queued",
                    "cancelled": "cancelled"
                }
                cmd.extend(["--status", status_map.get(status, status)])
        else:
            cmd = ["glab", "ci", "list", "--per-page", str(limit)]
            if status != "all":
                cmd.extend(["--status", status])
            if gitlab_host:
                env["GITLAB_HOST"] = gitlab_host

        result = subprocess.run(cmd, cwd=path, capture_output=True, text=True, env=env)

        if result.returncode != 0:
            return [TextContent(type="text", text=f"Error: {result.stderr.strip()}")]

        output = result.stdout.strip() or "No pipeline runs found"
        return [TextContent(type="text", text=output)]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


@registry.register(
    name="git_pipeline_view",
    description="View details of a specific pipeline run",
    input_schema={
        "type": "object",
        "properties": {
            "run_id": {
                "type": "string",
                "description": "Pipeline/run ID"
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
        "required": ["run_id"]
    }
)
def git_pipeline_view(arguments: dict) -> list[TextContent]:
    """View a pipeline run"""
    run_id = arguments.get("run_id")
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
            cmd = ["gh", "run", "view", str(run_id)]
            if web:
                cmd.append("--web")
        else:
            cmd = ["glab", "ci", "view", str(run_id)]
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
    name="git_pipeline_logs",
    description="View logs from a pipeline run or job",
    input_schema={
        "type": "object",
        "properties": {
            "run_id": {
                "type": "string",
                "description": "Pipeline/run ID"
            },
            "job": {
                "type": "string",
                "description": "Specific job name (optional)",
                "default": ""
            },
            "failed": {
                "type": "boolean",
                "description": "Only show failed job logs",
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
        "required": ["run_id"]
    }
)
def git_pipeline_logs(arguments: dict) -> list[TextContent]:
    """View pipeline logs"""
    run_id = arguments.get("run_id")
    job = arguments.get("job", "")
    failed = arguments.get("failed", False)
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
            cmd = ["gh", "run", "view", str(run_id), "--log"]
            if failed:
                cmd.append("--log-failed")
            if job:
                cmd.extend(["--job", job])
        else:
            # GitLab uses job ID for logs
            if job:
                cmd = ["glab", "ci", "trace", job]
            else:
                cmd = ["glab", "ci", "trace", str(run_id)]
            if gitlab_host:
                env["GITLAB_HOST"] = gitlab_host

        result = subprocess.run(cmd, cwd=path, capture_output=True, text=True, env=env)

        if result.returncode != 0:
            return [TextContent(type="text", text=f"Error: {result.stderr.strip()}")]

        # Truncate very long logs
        output = result.stdout.strip()
        if len(output) > 50000:
            output = output[:50000] + "\n\n... [Output truncated, showing first 50KB]"

        return [TextContent(type="text", text=output)]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


@registry.register(
    name="git_pipeline_trigger",
    description="Trigger a new pipeline run (GitHub: re-run or dispatch, GitLab: trigger pipeline)",
    input_schema={
        "type": "object",
        "properties": {
            "workflow": {
                "type": "string",
                "description": "Workflow file name (GitHub) or pipeline trigger (GitLab)",
                "default": ""
            },
            "branch": {
                "type": "string",
                "description": "Branch to run on",
                "default": ""
            },
            "rerun_id": {
                "type": "string",
                "description": "Re-run a specific run/pipeline ID",
                "default": ""
            },
            "failed_only": {
                "type": "boolean",
                "description": "Only re-run failed jobs",
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
        }
    }
)
def git_pipeline_trigger(arguments: dict) -> list[TextContent]:
    """Trigger a pipeline run"""
    workflow = arguments.get("workflow", "")
    branch = arguments.get("branch", "")
    rerun_id = arguments.get("rerun_id", "")
    failed_only = arguments.get("failed_only", False)
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
            if rerun_id:
                cmd = ["gh", "run", "rerun", str(rerun_id)]
                if failed_only:
                    cmd.append("--failed")
            elif workflow:
                cmd = ["gh", "workflow", "run", workflow]
                if branch:
                    cmd.extend(["--ref", branch])
            else:
                return [TextContent(type="text", text="Error: Specify workflow or rerun_id")]
        else:
            if rerun_id:
                cmd = ["glab", "ci", "retry", str(rerun_id)]
            else:
                cmd = ["glab", "ci", "run"]
                if branch:
                    cmd.extend(["--branch", branch])
            if gitlab_host:
                env["GITLAB_HOST"] = gitlab_host

        result = subprocess.run(cmd, cwd=path, capture_output=True, text=True, env=env)

        if result.returncode != 0:
            return [TextContent(type="text", text=f"Error: {result.stderr.strip()}")]

        return [TextContent(type="text", text=f"✅ Pipeline triggered:\n{result.stdout.strip()}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


@registry.register(
    name="git_pipeline_cancel",
    description="Cancel a running pipeline",
    input_schema={
        "type": "object",
        "properties": {
            "run_id": {
                "type": "string",
                "description": "Pipeline/run ID to cancel"
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
        "required": ["run_id"]
    }
)
def git_pipeline_cancel(arguments: dict) -> list[TextContent]:
    """Cancel a pipeline run"""
    run_id = arguments.get("run_id")
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
            cmd = ["gh", "run", "cancel", str(run_id)]
        else:
            cmd = ["glab", "ci", "cancel", str(run_id)]
            if gitlab_host:
                env["GITLAB_HOST"] = gitlab_host

        result = subprocess.run(cmd, cwd=path, capture_output=True, text=True, env=env)

        if result.returncode != 0:
            return [TextContent(type="text", text=f"Error: {result.stderr.strip()}")]

        return [TextContent(type="text", text=f"✅ Pipeline {run_id} cancelled")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


@registry.register(
    name="git_workflow_list",
    description="List available workflows (GitHub Actions) or pipeline configs",
    input_schema={
        "type": "object",
        "properties": {
            "all": {
                "type": "boolean",
                "description": "Include disabled workflows",
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
        }
    }
)
def git_workflow_list(arguments: dict) -> list[TextContent]:
    """List workflows"""
    show_all = arguments.get("all", False)
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
            cmd = ["gh", "workflow", "list"]
            if show_all:
                cmd.append("--all")
        else:
            # GitLab doesn't have workflow list, show pipeline config
            cmd = ["glab", "ci", "config"]
            if gitlab_host:
                env["GITLAB_HOST"] = gitlab_host

        result = subprocess.run(cmd, cwd=path, capture_output=True, text=True, env=env)

        if result.returncode != 0:
            return [TextContent(type="text", text=f"Error: {result.stderr.strip()}")]

        output = result.stdout.strip() or "No workflows found"
        return [TextContent(type="text", text=output)]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


@registry.register(
    name="git_pipeline_status",
    description="Get the status of the latest pipeline for current branch",
    input_schema={
        "type": "object",
        "properties": {
            "branch": {
                "type": "string",
                "description": "Branch to check (default: current branch)",
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
def git_pipeline_status(arguments: dict) -> list[TextContent]:
    """Get latest pipeline status"""
    branch = arguments.get("branch", "")
    platform = arguments.get("platform", "auto")
    gitlab_host = arguments.get("gitlab_host", "")
    path = arguments.get("path", ".")

    env = _get_env()

    if platform == "auto":
        platform, detected_host = _detect_platform(path)
        if detected_host and not gitlab_host:
            gitlab_host = detected_host

    # Get current branch if not specified
    if not branch:
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=path,
                capture_output=True,
                text=True
            )
            branch = result.stdout.strip()
        except Exception:
            branch = "main"

    try:
        if platform == "github":
            cmd = ["gh", "run", "list", "--branch", branch, "--limit", "1"]
        else:
            cmd = ["glab", "ci", "status"]
            if gitlab_host:
                env["GITLAB_HOST"] = gitlab_host

        result = subprocess.run(cmd, cwd=path, capture_output=True, text=True, env=env)

        if result.returncode != 0:
            return [TextContent(type="text", text=f"Error: {result.stderr.strip()}")]

        output = result.stdout.strip() or f"No pipeline runs found for branch: {branch}"
        return [TextContent(type="text", text=f"Branch: {branch}\n\n{output}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]
