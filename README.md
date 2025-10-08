# Anvil

**Anvil** is my personal **MCP (Model Context Protocol)** server — a local, modular, and self-extending development engine designed to host and manage tools accessible through MCP-compatible clients such as Claude Desktop.

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
| `git_status` | Get git repository status with clean, readable formatting. |
| `git_commit` | Stage and commit changes with optional push to remote. |
| `git_branch` | List, create, switch, or delete git branches. |
| `git_diff` | Show git diff of changes (unstaged, staged, or both). |
| `git_log` | Show git commit history with clean formatting. |
| `run_tests` | Run tests with auto-detected framework (pytest, unittest, Django, jest). |
| `homelab_status` | Comprehensive Homelab homelab dashboard showing all VMs, containers, services, and resources. |

---

## Architecture
```
[ MCP Client (e.g. Claude Desktop) ]
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
[ Local File System / Apps / Remote Infrastructure ]
```

## 🚀 Vision

Anvil is built to evolve into a **practical AI development engine** that automates real workflows.

### Phase 1 – Core Foundation ✅
Enable reading, writing, searching, and executing on local files safely.

### Phase 2A – Git & Testing ✅
Build version control and testing automation tools.

### Phase 2B – Homelab Management (Homelab) 🏠 ← **CURRENT FOCUS**
Remote management and monitoring of production homelab infrastructure via SSH.

### Phase 3 – Frontend Development 🎨
Solve the "refresh hell" problem and streamline Django + Bootstrap development.

### Phase 4 – Project-Specific Tools 🎯
Create tools tailored to Django, FastAPI, and AImagineers.io workflows.

### Phase 5 – Cross-Project Integration 🌐
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
- **SSH access configured** to Homelab homelab for remote infrastructure management.

---

## 🗺️ Tool Development Pipeline

### ✅ Phase 1 – Foundation (Complete)
| Tool | Status | Purpose |
|------|--------|----------|
| `list_files` | ✅ | List directory contents |
| `read_file` | ✅ | Read file contents |
| `write_file` | ✅ | Write to files |
| `run_command` | ✅ | Execute shell commands |
| `search_files` | ✅ | Search by filename/content with gitignore support |

### ✅ Phase 2A – Git & Testing (Complete)
| Tool | Status | Purpose |
|------|--------|----------|
| `git_status` | ✅ | Git status with clean formatting |
| `git_commit` | ✅ | Stage and commit with optional push |
| `git_branch` | ✅ | Manage branches (list, create, switch, delete) |
| `git_diff` | ✅ | Show file changes (unstaged/staged/both) |
| `git_log` | ✅ | Commit history with formatting |
| `run_tests` | ✅ | Smart test runner with framework detection |

---

## 🏠 Phase 2B – Homelab Management (Homelab) - **IN PROGRESS**

**Infrastructure:** KVM/libvirt hypervisor (Homelab) managing 5 VMs across VLANs  
**Access:** Full SSH access configured to host + all VMs  
**Goal:** Conversational debugging and management of production infrastructure

### Homelab Infrastructure Overview

**Host:** Homelab
- Ryzen 7 5700X, 32GB RAM
- KVM/libvirt hypervisor
- VLAN-segmented networking

**Virtual Machines:**
| VM | IP | VLAN | Purpose | Key Services |
|----|----|----- |---------|--------------|
| apps01 | 192.168.x.x | br20 | Application host | Docker (6 containers), Node Exporter |
| db01 | 192.168.x.x | br30 | Database | PostgreSQL 16 |
| gitlab01 | 192.168.x.x | br40 | Version control | GitLab CE |
| gitrunner01 | 192.168.x.x | br20 | CI/CD | GitLab Runner |
| ops01 | 192.168.x.x | br40 | Monitoring | Grafana, Prometheus |

### Sprint 1: VM & Infrastructure Management
| Tool | Priority | Purpose | Status |
|------|----------|---------|--------|
| `homelab_status` | 🔥 Critical | Dashboard: VMs, containers, services, resources | ✅ Complete |
| `homelab_vm` | 🔥 High | Start/stop/restart VMs | 🔨 Building |
| `homelab_network` | 🔥 High | Check VLAN/bridge configs, routing | 📋 Planned |
| `homelab_ping` | Medium | Test connectivity between VMs/services | 📋 Planned |
| `homelab_firewall` | Medium | Check/manage firewall rules | 📋 Planned |

**Goal:** Complete visibility and control over VM infrastructure

### Sprint 2: Container & Application Management
| Tool | Priority | Purpose | Status |
|------|----------|---------|--------|
| `homelab_containers` | 🔥 High | List/manage Docker containers on apps01 | 📋 Planned |
| `homelab_logs` | 🔥 High | Stream container/service logs | 📋 Planned |
| `homelab_restart` | 🔥 High | Restart containers/services | 📋 Planned |
| `homelab_exec` | Medium | Execute commands in containers | 📋 Planned |
| `homelab_tunnel` | Medium | Manage Cloudflare tunnels | 📋 Planned |

**Goal:** Full Docker container lifecycle management

### Sprint 3: Database Management
| Tool | Priority | Purpose | Status |
|------|----------|---------|--------|
| `homelab_db_status` | 🔥 High | PostgreSQL health on db01 | 📋 Planned |
| `homelab_db_query` | Medium | Run SQL queries | 📋 Planned |
| `homelab_db_connections` | Medium | Show active DB connections | 📋 Planned |
| `homelab_db_backup` | Low | Backup databases | 📋 Planned |

**Goal:** Database monitoring and management

### Sprint 4: Diagnostic & Debugging
| Tool | Priority | Purpose | Status |
|------|----------|---------|--------|
| `homelab_diagnose` | 🔥 High | Auto-diagnose common issues | 📋 Planned |
| `homelab_ports` | Medium | Show listening ports on VMs | 📋 Planned |
| `homelab_routes` | Medium | Check routing tables | 📋 Planned |
| `homelab_resources` | Medium | CPU/RAM/disk usage across infrastructure | 📋 Planned |

**Goal:** Rapid problem identification and resolution

### Sprint 5: GitLab & CI/CD
| Tool | Priority | Purpose | Status |
|------|----------|---------|--------|
| `homelab_gitlab` | Medium | GitLab status & management | 📋 Planned |
| `homelab_runner` | Medium | CI runner status & jobs | 📋 Planned |
| `homelab_pipeline` | Low | Trigger/monitor pipelines | 📋 Planned |

**Goal:** CI/CD pipeline visibility and control

---

### 🎨 Phase 3 – Frontend Development (Future Priority)

Solving the **"refresh hell"** problem for Django + Bootstrap + Vanilla CSS development.

#### Sprint 1: Emergency Relief (Debug & Fix Tools)
| Tool | Priority | Purpose | Status |
|------|----------|---------|--------|
| `check_frontend` | 🔥 Critical | Validate HTML/CSS/JS, find errors, check Bootstrap conflicts | 📋 Planned |
| `clear_django_cache` | 🔥 Critical | Clear static files cache, template cache, cache-busting | 📋 Planned |
| `validate_html` | 🔥 Critical | Check template syntax, Bootstrap usage, Django tags | 📋 Planned |

#### Sprint 2: Modern Workflow (Live Development Tools)
| Tool | Priority | Purpose | Status |
|------|----------|---------|--------|
| `watch_static` | 🔥 High | Auto-reload on changes, validate code, collectstatic | 📋 Planned |
| `hot_reload_css` | 🔥 High | Inject CSS changes without page reload | 📋 Planned |

#### Sprint 3: Design Bridge (Figma Integration)
| Tool | Priority | Purpose | Status |
|------|----------|---------|--------|
| `extract_figma_tokens` | Medium | Pull colors, fonts, spacing from Figma → CSS variables | 📋 Planned |
| `figma_blueprint` | Medium | Analyze Figma frame structure, suggest Bootstrap approach | 📋 Planned |
| `design_to_bootstrap` | Medium | Screenshot → Bootstrap HTML/CSS (AI vision-based) | 📋 Planned |

#### Sprint 4: Code Quality (Bootstrap Mastery)
| Tool | Priority | Purpose | Status |
|------|----------|---------|--------|
| `reconcile_styles` | Low | Fix Bootstrap vs custom CSS conflicts | 📋 Planned |
| `bootstrap_component_generator` | Low | Generate Bootstrap components from description | 📋 Planned |
| `optimize_templates` | Low | Analyze Django templates, suggest improvements | 📋 Planned |

---

### 🎯 Phase 4 – Project-Specific Tools (Future)

#### Django/FastAPI Helpers
| Tool | Purpose | Status |
|------|----------|--------|
| `django_manage` | Run Django management commands | 📋 Planned |
| `create_migration` | Create and apply migrations | 📋 Planned |
| `run_server` | Start dev server with options | 📋 Planned |
| `shell_plus` | Interactive Django/IPython shell | 📋 Planned |

#### AImagineers.io Workflows
| Tool | Purpose | Status |
|------|----------|--------|
| `project_init` | Initialize new client project structure | 📋 Planned |
| `deploy_staging` | Deploy to staging environment | 📋 Planned |
| `deploy_prod` | Deploy to production | 📋 Planned |
| `backup_db` | Backup databases | 📋 Planned |

---

## 📈 Progress

**Total Tools Built:** 12  
**Phase 1:** 5/5 complete ✅  
**Phase 2A:** 6/6 complete ✅  
**Phase 2B Sprint 1:** 1/5 complete - `homelab_status` ✅  

---

## 🎯 Current Focus

**Problem:** Managing production homelab infrastructure requires constant SSH sessions, manual checks, and troubleshooting across 5 VMs.

**Solution:** Building conversational AI-assisted homelab management tools for instant visibility and control over entire infrastructure.

**Latest:** `homelab_status` complete! Full dashboard showing 5 VMs, 6 containers, 5 services - all healthy ✅

**Next Tool:** `homelab_vm` - VM lifecycle management (start/stop/restart)

---

*Built with purpose — to automate real work, not imaginary problems.*
