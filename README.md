# Anvil

**Anvil** is my personal **MCP (Model Context Protocol)** server — a local, modular, and self-extending development engine designed to host and manage tools accessible through MCP-compatible clients such as OpenAI Codex.

---

## Overview

Anvil exposes modular tools that can be dynamically discovered and invoked by connected MCP clients.  
Each tool is isolated within the `/server/tools/` directory and registered automatically through a lightweight loader system.

This project serves as the foundation for my **personal developer automation layer**, enabling consistent, secure, and extensible access to system capabilities.

Anvil is not just a host for tools — it’s built to help me **build tools**, **inspect code**, and **support active development** across all my projects.

---

## Current Capabilities

| Tool | Description |
|------|--------------|
| `list_files` | Lists files and directories within a given path. |
| `read_file` | Reads and returns the contents of a file. |
| `write_file` | Writes text content to a file, creating or overwriting as needed. |
| `run_command` | Executes safe shell commands and returns output. |
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

Anvil is built to evolve into a **self-building AI development engine**.

### Phase 1 – Core Tools  
Enable reading, writing, and executing local files safely.

### Phase 2 – Self-awareness  
Allow Anvil to inspect and understand its own tools — with features like code search, linting, and auto-documentation.

### Phase 3 – Self-extension  
Let Anvil generate, modify, and register new tools automatically, effectively helping me write code, extend itself, and support live development.

### Phase 4 – Integration  
Use Anvil beyond itself — connect it to other apps and projects as a shared local automation layer, powering developer workflows and AI-assisted coding tasks.

---

## 🧠 Philosophy

> *Tools shouldn’t just work — they should grow.*

Anvil embodies the principle of **living infrastructure** — software that evolves alongside its creator.  
Every tool, command, and capability is designed to be composable, understandable, and reusable across my ecosystem of projects.

---

## 🔒 Notes

- Anvil communicates with clients via `STDIO` using **JSON-RPC**.
- Each tool defines its own metadata and handler function.
- The system is intentionally minimal and will continue to evolve.
- Designed for **local and internal** use — not intended for public deployment.

---

## 🗺️ Future Roadmap

| Planned Tool | Purpose |
|---------------|----------|
| `search_files` | Search for filenames or content patterns. |
| `describe_tool` | Analyze and summarize tool definitions. |
| `generate_tool` | Create new tool modules dynamically. |
| `lint_tool` | Run code quality checks on tools. |
| `reload_tools` | Reload the registry without restarting. |
| `inspect_env` | Report system and environment status. |

---

*Built with purpose — to assist, extend, and eventually co-create.*
