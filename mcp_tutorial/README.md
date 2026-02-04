# Model Context Protocol (MCP) Comprehensive Tutorial

Welcome to the ultimate guide to the **Model Context Protocol (MCP)**. This tutorial is designed for developers who want to bridge the gap between Large Language Models (LLMs) and the real world.

## 🌟 What is MCP?

The Model Context Protocol (MCP) is an open-source standard that enables AI applications to safely and easily connect to external data sources, tools, and prompts. It acts like a **standardized interface** (think USB-C for AI) that allows any AI agent to talk to any backend system without custom integration code for every pair.

## 📂 Tutorial Structure

This tutorial is organized into 10 structured Python Notebooks and a practical sample server:

1.  **01 Introduction**: Learn the "Why" and "What" of MCP.
2.  **02 Core Concepts**: Deep dive into the architecture (Host, Client, Server) and primitives (Tools, Resources, Prompts).
3.  **03 Setup and Installation**: Get your Python environment ready.
4.  **04 Building Your First Server**: Step-by-step guide to using `FastMCP`.
5.  **05 Connecting to Agents**: How to integrate your server with Claude Desktop or custom agents.
6.  **06 Advanced Concepts**: Security (Roots), Agentic Workflows (Sampling), and SSE.
7.  **07 Real-World Project**: Architecture of a "Personal Knowledge Assistant".
8.  **08 Best Practices**: Tips for production-ready MCP servers.
9.  **09 Troubleshooting**: Common pitfalls and how to use the MCP Inspector.
10. **10 Learning Path**: Resources to continue your journey.

## 🚀 Getting Started

### Standalone Code Samples

In addition to the notebooks, we've provided standalone Python scripts in the `samples/` directory for practical experimentation:

-   `samples/client_example.py`: A complete MCP client that connects to the sample server.
-   `samples/low_level_server.py`: Shows how to build a server using the base `mcp` SDK without `FastMCP`.
-   `samples/sse_server_example.py`: Demonstrates a remote server using the SSE transport.
-   `samples/advanced_features.py`: Showcases Pydantic models, progress reporting, and resource templates.

### Prerequisites

- Python 3.10 or higher
- `pip` or `uv`

### Installation

```bash
pip install mcp fastmcp
```

### Running the Sample Server

We have provided a `sample_server.py` which implements a "Knowledge Assistant" with tools to list and read notes.

```bash
python sample_server.py
```

### Testing with MCP Inspector

The best way to test your server during development is using the official MCP Inspector:

```bash
npx @modelcontextprotocol/inspector python sample_server.py
```

## 🛠️ Key Primitives

| Primitive | Description | Use Case |
| :--- | :--- | :--- |
| **Tools** | Executable functions called by the LLM. | Querying a DB, writing a file, sending an API request. |
| **Resources** | Read-only data sources (like URLs). | Reading logs, documentation, or user profile data. |
| **Prompts** | Reusable instruction templates. | "Code Review" template, "Summarize" workflow. |

## 🛡️ Security First

MCP is designed with a strong focus on security:
- **User Consent**: Clients should always prompt users before a tool performs a side effect.
- **Roots**: Limits the server's access to specific directories on the file system.
- **Stdio Isolation**: Standard input/output transport ensures that local servers run in a controlled environment.

## 🤝 Contributing

MCP is an evolving standard maintained by Anthropic and the open-source community. Check out the [official documentation](https://modelcontextprotocol.io) for more details.

---
*Happy Building!*
