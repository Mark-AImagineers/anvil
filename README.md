# Anvil
Anvil is my personal MCP (Model Context Protocol) server, designed to host and manage developer tools accessible through MCP-compatible clients.

## Overview
Anvil exposes modular tools that can be dynamically discovered and invoked by connected MCP clients.
Each tools is isolated within the /server/tools/ directory and registerted automatically through a lightweight loader system.

This project serves as the foundation for my personal developer automation, enabling consistent secure, and extensible access to system capabilities.

## Notes
 - Anvil communicates with clients via `STDIO` using JSON-RPC
 - Each tool should define its own metadata and handler function.
 - The server is intentionally minimal and will evolve as new tools are added.

 