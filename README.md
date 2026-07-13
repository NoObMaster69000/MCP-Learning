# MCP Tutorial Project

This repository contains a comprehensive, beginner-to-advanced tutorial on the **Model Context Protocol (MCP)**.

The tutorial is structured as a series of 10 Python notebooks located in the `mcp_tutorial/` directory, along with a newly added **MCP Server Development Masterclass**.

## 🎓 MCP Server Development Masterclass

To help developers master the protocol from zero to production-grade, we have added a comprehensive text-based masterclass:

-   **[MCP Server Development Masterclass (mcp_server_development_masterclass.md)](mcp_server_development_masterclass.md)**: A complete, fully implemented masterclass that covers:
    -   *Lecture 1*: Introduction to MCP (Why, What, Problem, Concepts)
    -   *Lecture 2*: Architecture & Core Concepts (Host, Client, Server, Connections)
    -   *Lecture 3*: Transports & Protocol Mechanics (JSON-RPC, stdio, Streamable HTTP, SSE)
    -   *Lecture 4*: Setting Up Your Development Environment (uv, pyproject, layout)
    -   *Lecture 5*: Building Your First Server (FastMCP vs base SDK with commented code)
    -   *Lecture 6*: Tools, Resources & Prompts (Detailed, commented Pydantic & API examples)
    -   *Lecture 6.5*: **Adding Skills & Integration Guide (Host Setup & Client Code)** (Exposing skills, host config guide for Claude Desktop, and full programmatic Python client implementation)
    -   *Lecture 7*: Testing & Debugging (MCP Inspector & automated pytest integration)
    -   *Lecture 8*: Security - The Make-or-Break Phase (Sandboxing, shell injection, approvals)
    -   *Lecture 9*: Production Deployment (Multi-stage Docker, remote streamable HTTP + API key authentication)
    -   *Lecture 10*: Advanced Topics & Future Roadmap (Sampling, dynamic resources, pagination, evolution)
    -   *Lecture 11*: Composing, Namespacing & Transforms (Mounting, proxying remote servers, namespacing, ToolTransform/search/AsTools)
    -   *Lecture 12*: Interactive UIs & FastMCP UIs (FastMCPApp architecture, Prefab UI elements, Reactivity with Rx, built-in FileUpload/Approval/Choice/FormInput/GenerativeUI)
    -   *Lecture 13*: Advanced Authentication & Security Gating (OAuth Proxies, Token Factory encrypted storage, Client ID Metadata Documents, Private Key JWT, Opaque Introspection, Confused Deputy protection)
    -   *Lecture 14*: Next-Gen Utilities: Tasks, Telemetry & Versioning (Docket Background Tasks with SEP-1686, OpenTelemetry tracing spans, component VersionFilter routing)

## Quick Start

1.  **Explore the Masterclass**: Read through the [MCP Server Development Masterclass](mcp_server_development_masterclass.md) for a comprehensive deep-dive.
2.  **Explore the Notebooks**: Head over to [mcp_tutorial/README.md](mcp_tutorial/README.md) for a detailed overview of the notebook-based tutorial.
3.  **Install Dependencies**:
    ```bash
    pip install mcp fastmcp
    ```
4.  **Run the Sample Server**:
    ```bash
    python mcp_tutorial/sample_server.py
    ```

## Contents

- `mcp_server_development_masterclass.md`: Comprehensive, step-by-step masterclass guiding you from zero to production-ready MCP servers.
- `mcp_tutorial/`: Contains 10 Jupyter notebooks covering everything from basics to advanced MCP patterns.
- `mcp_tutorial/sample_server.py`: A fully functional example of an MCP Knowledge Assistant.
- `mcp_smart_home/`: A comprehensive, production-style Smart Home Manager project demonstrating state persistence, complex validation, and workflow prompts.
