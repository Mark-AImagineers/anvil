# Anvil

**Anvil** is my personal **MCP (Model Context Protocol)** server — a local, modular, and self-extending development engine designed to host and manage tools accessible through MCP-compatible clients such as OpenAI Codex.

---

## Overview

Anvil exposes modular tools that can be dynamically discovered and invoked by connected MCP clients.  
Each tool is isolated within the `/server/tools/` directory and registered automatically through a lightweight loader system.

This project serves as the foundation for my **personal developer automation layer**, enabling consistent, secure, and extensible access to system capabilities.

Anvil is not just a host for tools — it's built to help me **build tools**, **inspect code**, and **support active development** across all my projects.

---

## Current Capabilities

| Tool | Description |
|------|--------------|
| `list_files` | Lists files and directories within a given path. |
| `read_file` | Reads and returns the contents of a file. |
| `write_file` | Writes text content to a file, creating or overwriting as needed. |
| `run_command` | Executes safe shell commands and returns output. |
| `search_files` | Search for files by name pattern and/or content with advanced filtering. |
| *(and growing)* | Tools are dynamically discovered at startup. |

---

## Architecture
```
[ MCP Client (e.g. Codex) ]
│
▼
(stdin/stdout)
│
┌───────────┐
│ Anvil │
├───────────┤
│ Registry │ → auto-discovers tools from /server/tools/
│ Tools │ → modular, callable units (read, write, exec)
│ Runtime │ → handles JSON-RPC messages from clients
└───────────┘
│
[ Local File System / Apps ]
```

## 🚀 Vision

Anvil is built to evolve into a **practical AI development engine** that automates real workflows.

### Phase 1 – Core Foundation ✅
Enable reading, writing, searching, and executing on local files safely.

### Phase 2 – Developer Workflows 🔨
Build practical tools for Git, Docker, testing, package management, and project automation.

### Phase 3 – Project-Specific Tools 🎯
Create tools tailored to Django, FastAPI, and AImagineers.io workflows.

### Phase 4 – Cross-Project Integration 🌐
Connect Anvil to multiple projects as a unified automation layer.

---

## 🧠 Philosophy

> *Build tools that solve real problems, not theoretical ones.*

Anvil embodies the principle of **practical automation** — every tool should eliminate friction from actual development workflows.  
Focus on what matters: shipping code faster, testing easier, and managing projects better.

---

## 🔒 Notes

- Anvil communicates with clients via `STDIO` using **JSON-RPC**.
- Each tool defines its own metadata and handler function.
- The system is intentionally minimal and will continue to evolve.
- Designed for **local and internal** use — not intended for public deployment.

---

## 🗺️ Tool Development Pipeline

### ✅ Phase 1 – Foundation (Complete)
| Tool | Status | Purpose |
|------|--------|----------|
| `list_files` | ✅ | List directory contents |
| `read_file` | ✅ | Read file contents |
| `write_file` | ✅ | Write to files |
| `run_command` | ✅ | Execute shell commands |
| `search_files` | ✅ | Search by filename/content |

### 🔨 Phase 2 – Developer Workflows (Next)

#### Version Control
| Tool | Priority | Purpose |
|------|----------|----------|
| `git_status` | 🔥 High | Quick git status with clean formatting |
| `git_commit` | 🔥 High | Stage and commit with message |
| `git_branch` | 🔥 High | List, create, switch branches |
| `git_diff` | Medium | Show file changes |
| `git_log` | Medium | Show commit history |

#### Testing & Quality
| Tool | Priority | Purpose |
|------|----------|----------|
| `run_tests` | 🔥 High | Run pytest/jest/unittest with unified output |
| `run_linter` | Medium | Run pylint, flake8, eslint, etc. |
| `check_types` | Low | Run mypy, TypeScript checks |

#### Container Management
| Tool | Priority | Purpose |
|------|----------|----------|
| `docker_ps` | 🔥 High | List running containers with clean output |
| `docker_compose` | 🔥 High | Up, down, restart services |
| `docker_logs` | Medium | Stream container logs |
| `docker_exec` | Medium | Execute commands in containers |

#### Package Management
| Tool | Priority | Purpose |
|------|----------|----------|
| `pip_install` | Medium | Install Python packages in active venv |
| `npm_install` | Medium | Install Node packages |
| `requirements_check` | Low | Check if requirements are installed |

### 🎯 Phase 3 – Project-Specific Tools (Future)

#### Django/FastAPI Helpers
| Tool | Purpose |
|------|----------|
| `django_manage` | Run Django management commands |
| `create_migration` | Create and apply migrations |
| `run_server` | Start dev server with options |
| `shell_plus` | Interactive Django/IPython shell |

#### AImagineers.io Workflows
| Tool | Purpose |
|------|----------|
| `project_init` | Initialize new client project structure |
| `deploy_staging` | Deploy to staging environment |
| `deploy_prod` | Deploy to production |
| `backup_db` | Backup databases |

---

*Built with purpose — to automate real work, not imaginary problems.*
