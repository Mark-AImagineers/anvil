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
| `homelab_status` | Comprehensive Homelab dashboard showing all VMs, containers, services, and resources. |
| `homelab_vm` | Manage VM lifecycle: start, stop, restart, suspend, resume VMs on homelab. |
| `email_list` | List emails from inbox/folder with advanced filtering. |
| `email_read` | Read full email content including attachments info. |
| `email_search` | Advanced search across emails with multiple criteria. |
| `email_send` | Send new emails with attachments support. |
| `email_reply` | Reply to emails with quote and reply-all support. |
| `email_folders` | List all email folders/mailboxes in account. |
| `playwright` | Browser automation using Playwright. Launch browser, navigate, click, fill forms, extract data, capture screenshots. |
| `chrome_devtools` | Debug web apps using Chrome DevTools Protocol. Connect to Opera GX/Chrome, execute JavaScript, inspect network, analyze DOM, capture screenshots, monitor performance. |
| `read_page` | Read and extract content from web pages open in browser. Get clean text, markdown, or specific data (links, images, emails, prices, tables). |
| `research_tools` | Multi-source research and synthesis. Compare info from multiple tabs, fact-check claims, build timelines, extract references. |
| `clipboard_tools` | Cross-context data handling via clipboard. Capture history, transform formats (JSON/CSV/Markdown/Base64), save reusable snippets with tags. |

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
[ Local File System / Apps / Remote Infrastructure / Email ]
```

## 🚀 Vision

Anvil is built to evolve into a **practical AI development engine** that automates real workflows.

### Phase 1 – Core Foundation ✅
Enable reading, writing, searching, and executing on local files safely.

### Phase 2A – Git & Testing ✅
Build version control and testing automation tools.

### Phase 2B – Homelab Management 🏠
Remote management and monitoring of production homelab infrastructure via SSH.

### Phase 2C – Email Management 📧 ✅ **COMPLETE**
Full control over PrivateEmail accounts (markb@aimagineers.io, hello@aimagineers.io).

### Phase 2D – Browser Automation & Web Research 🌐 ✅ **COMPLETE**
Automate browser interactions, extract web content, and enable multi-source research workflows.

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
- **SSH access configured** to Homelab for remote infrastructure management.
- **Email access configured** for PrivateEmail accounts via IMAP/SMTP.

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

## 📧 Phase 2C – Email Management (PrivateEmail) - ✅ **COMPLETE**

**Accounts:** markb@aimagineers.io, hello@aimagineers.io  
**Provider:** PrivateEmail (Namecheap)  
**Protocol:** IMAP/SMTP over SSL  
**Goal:** Full conversational control over business email

### Email Tools
| Tool | Status | Purpose |
|------|--------|---------|
| `email_list` | ✅ Complete | List emails with filters (unread, from, subject, date range) |
| `email_read` | ✅ Complete | Read full email content with attachments info |
| `email_search` | ✅ Complete | Advanced search (query, sender, subject, body, attachments) |
| `email_send` | ✅ Complete | Send new emails with CC/BCC/attachments |
| `email_reply` | ✅ Complete | Reply to emails with quote, reply-all support |
| `email_folders` | ✅ Complete | List all mailbox folders |

**Features:**
- 📥 Read & manage emails from both accounts
- 📤 Send emails with attachments
- 🔍 Advanced search with multiple criteria
- 💬 Reply with automatic quoting
- 📁 Multi-folder support
- 🔒 Secure SSL/TLS connections

---

## 🏠 Phase 2B – Homelab Management (In Progress)

**Infrastructure:** KVM/libvirt hypervisor managing 5 VMs across VLANs  
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
| `homelab_vm` | 🔥 High | Start/stop/restart VMs | ✅ Complete |
| `homelab_network` | 🔥 High | Check VLAN/bridge configs, routing | 📋 Planned |
| `homelab_ping` | Medium | Test connectivity between VMs/services | 📋 Planned |
| `homelab_firewall` | Medium | Check/manage firewall rules | 📋 Planned |

---

## 🌐 Phase 2D – Browser Automation & Web Research - ✅ **COMPLETE**

**Goal:** Automate browser interactions, extract web content, and enable multi-source research workflows.

### Browser Automation & Research Tools
| Tool | Status | Purpose |
|------|--------|---------|
| `playwright` | ✅ Complete | Browser automation: launch, navigate, click, fill, extract, screenshot |
| `chrome_devtools` | ✅ Complete | Debug web apps via CDP: execute JS, inspect DOM, network monitoring, performance |
| `read_page` | ✅ Complete | Extract clean text, markdown, or structured data from browser tabs |
| `research_tools` | ✅ Complete | Multi-source research: compare sources, fact-check, timelines, references |
| `clipboard_tools` | ✅ Complete | Clipboard management: history, format transformations, snippets |

**Features:**
- 🤖 Full browser automation with Playwright (Chromium, Firefox, WebKit)
- 🔍 Chrome DevTools Protocol integration for debugging live apps
- 📄 Clean content extraction from web pages
- 🔬 Multi-tab research and fact-checking
- 📋 Cross-context data handling via clipboard

---

### 🎨 Phase 3 – Frontend Development (Future Priority)

Solving the **"refresh hell"** problem for Django + Bootstrap + Vanilla CSS development.

#### Sprint 1: Emergency Relief (Debug & Fix Tools)
| Tool | Priority | Purpose | Status |
|------|----------|---------|--------|
| `check_frontend` | 🔥 Critical | Validate HTML/CSS/JS, find errors, check Bootstrap conflicts | 📋 Planned |
| `clear_django_cache` | 🔥 Critical | Clear static files cache, template cache, cache-busting | 📋 Planned |
| `validate_html` | 🔥 Critical | Check template syntax, Bootstrap usage, Django tags | 📋 Planned |

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

**Total Tools Built:** 24
**Phase 1:** 5/5 complete ✅
**Phase 2A:** 6/6 complete ✅
**Phase 2B Sprint 1:** 2/5 in progress
**Phase 2C:** 6/6 complete ✅
**Phase 2D:** 5/5 complete ✅ **NEW!**

---

## 🎯 Current Status

**Latest Achievement:** Browser automation & web research tools complete! ✅
Full browser automation with Playwright, Chrome DevTools integration, and multi-source research capabilities.

**Previous Achievement:** Email management tools complete! ✅
Full control over markb@aimagineers.io and hello@aimagineers.io via conversational interface.

**Active Development:**
- Homelab infrastructure management (networking, connectivity, firewall)
- Planning frontend development tools for Django + Bootstrap workflows

---

*Built with purpose — to automate real work, not imaginary problems.*
