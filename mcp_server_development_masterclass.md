# MCP Server Development Masterclass
## From Zero to Production-Grade Server

---

# Table of Contents

1. [Lecture 1: Introduction to MCP](#lecture-1-introduction-to-mcp)
2. [Lecture 2: Architecture & Core Concepts](#lecture-2-architecture--core-concepts)
3. [Lecture 3: Transports & Protocol Mechanics](#lecture-3-transports--protocol-mechanics)
4. [Lecture 4: Setting Up Your Development Environment](#lecture-4-setting-up-your-development-environment)
5. [Lecture 5: Building Your First Server](#lecture-5-building-your-first-server)
6. [Lecture 6: Tools, Resources & Prompts](#lecture-6-tools-resources--prompts)
7. [Lecture 7: Testing & Debugging](#lecture-7-testing---debugging)
8. [Lecture 8: Security - The Make-or-Break Phase](#lecture-8-security---the-make-or-break-phase)
9. [Lecture 9: Production Deployment](#lecture-9-production-deployment)
10. [Lecture 10: Advanced Topics & Future Roadmap](#lecture-10-advanced-topics--future-roadmap)

---

# Lecture 1: Introduction to MCP

## What is MCP?

**Model Context Protocol (MCP)** is an open standard created by Anthropic in November 2024 (now stewarded by the Linux Foundation) that enables AI applications to connect to external tools, data, and workflows through one common protocol.

Think of it as **"USB-C for AI"** — one universal connector that works everywhere.

## The Problem MCP Solves

### Before MCP: The Integration Mess

```
+-------------+     custom glue     +-------------+
|   Claude    |<------------------->|   Slack API |
+-------------+                     +-------------+
       |
       | custom glue
       v
+-------------+
|  Database   |
+-------------+
       ^
       | different custom glue
+------+------+
|   ChatGPT   |<------------------->|  GitHub API |
+-------------+                     +-------------+
```

**N models x M tools = NxM integrations** — a maintenance nightmare.

### After MCP: One Protocol to Rule Them All

```
+-------------+                     +-------------+
|   Claude    |<------ MCP -------->|   Server    |
+-------------+                     |  (Slack)    |
       |                            +-------------+
       |                            +-------------+
       |<------ MCP --------------->|   Server    |
       |                            |  (Database) |
+------+------+                     +-------------+
|   ChatGPT   |<------ MCP -------->+-------------+
+-------------+                     |   Server    |
                                    |  (GitHub)   |
                                    +-------------+
```

**Build once, use everywhere.**

## MCP vs. Related Concepts

| Concept | What It Does | How MCP Differs |
|---------|-------------|-----------------|
| **Function Calling** | Per-request, vendor-specific JSON schema | MCP is vendor-neutral; stand up once, any host discovers |
| **RAG** | Retrieves text into context | MCP gives the model *actions* and live data access |
| **A2A (Agent-to-Agent)** | Connects agents to each other | MCP connects agent to tools ("its hands"); complementary, not competing |

## Key Resources

- [Anthropic's Launch Announcement](https://www.anthropic.com/news/model-context-protocol)
- [Official "What is MCP?" Intro](https://modelcontextprotocol.io/docs/getting-started/intro)
- [MCP Quick-Reference Cheat Sheet](https://www.webfuse.com/mcp-cheat-sheet)

---

# Lecture 2: Architecture & Core Concepts

## The Host / Client / Server Model

```
+-------------------------------------------------------------+
|                         HOST                                |
|  (AI Application: Claude Desktop, Cursor, VS Code Copilot)  |
|                                                             |
|  +-------------+    +-------------+    +-------------+    |
|  |   Client    |    |   Client    |    |   Client    |    |
|  |   (MCP)     |    |   (MCP)     |    |   (MCP)     |    |
|  +------+------+    +------+------+    +------+------+    |
|         |                  |                  |             |
+---------+------------------+------------------+-----------+
          |                  |                  |
          v                  v                  v
   +-------------+   +-------------+   +-------------+
   |   Server    |   |   Server    |   |   Server    |
   | (Database)  |   |   (Slack)   |   |  (Weather)  |
   +-------------+   +-------------+   +-------------+
```

### Roles Defined

| Component | Role | Example |
|-----------|------|---------|
| **Host** | The AI application that coordinates everything | Claude Desktop, Cursor, VS Code |
| **Client** | One per connected server, instantiated by host | MCP client instance |
| **Server** | What **you** build; exposes capabilities | Your custom tool server |

## Connection Lifecycle

```
+---------+              +---------+
| Client  |              | Server  |
+----+----+              +----+----+
     |                        |
     |---- Initialize ------->|  1. Handshake: negotiate protocol version
     |                        |
     |<--- Initialize Result -|  2. Server declares capabilities
     |                        |
     |---- Capability Check ->|  3. Confirm supported features
     |                        |
     |<--- Ready -------------|  4. Operational!
     |                        |
     |==== OPERATION =========|  5. Call tools, read resources, etc.
     |                        |
```

## The Three Server Primitives

These are the building blocks of every MCP server. **Learn these cold.**

### 1. Tools — Executable Actions

**Model-controlled.** Functions the AI can call to perform actions.

```python
# Example: A tool that queries a database
@mcp.tool()
async def query_database(sql: str) -> str:
    """
    Execute a read-only SQL query against the company database.

    Args:
        sql: A valid SELECT statement (read-only)
    """
    # Implementation here
    return results
```

**When to use:** Running queries, sending messages, hitting APIs, performing calculations.

### 2. Resources — Read-Only Data

**Application-controlled.** Data the model can load for context.

```python
# Example: A resource exposing database schema
@mcp.resource("db://schema/{table_name}")
async def get_table_schema(table_name: str) -> str:
    """Get the schema definition for a database table."""
    return schema_info
```

**When to use:** Files, database schemas, documents, configuration data.

### 3. Prompts — Reusable Templates

**User-invoked.** Parameterized prompt templates.

```python
# Example: A prompt template for code review
@mcp.prompt()
def code_review_prompt(code: str, language: str) -> str:
    """Generate a code review prompt."""
    return f"""Please review this {language} code:

```{language}
{code}
```

Check for:
1. Security vulnerabilities
2. Performance issues
3. Code style consistency
4. Error handling
"""
```

**When to use:** Standardized workflows, repetitive tasks, complex multi-step prompts.

## Client-Side Features (Know They Exist)

| Feature | Description |
|---------|-------------|
| **Sampling** | Server asks the host's LLM to generate something (human stays in loop) |
| **Elicitation** | Server requests additional input from user mid-operation |
| **Roots** | Client tells server which files/directories it may operate within |

## Key Resources

- [Core Concepts / Architecture Docs](https://modelcontextprotocol.io/docs/getting-started/intro)
- [Full Specification & Schema Repo](https://github.com/modelcontextprotocol/modelcontextprotocol)

---

# Lecture 3: Transports & Protocol Mechanics

## JSON-RPC 2.0 — The Wire Format

All MCP messages are JSON-RPC. Your SDK hides most of this, but understanding it makes debugging far easier.

### Message Types

```json
// 1. REQUEST (expects a response)
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "query_database",
    "arguments": {
      "sql": "SELECT * FROM users LIMIT 10"
    }
  }
}

// 2. RESPONSE
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "id|name|email\n1|Alice|alice@example.com"
      }
    ]
  }
}

// 3. NOTIFICATION (fire-and-forget)
{
  "jsonrpc": "2.0",
  "method": "notifications/progress",
  "params": {
    "progress": 50,
    "total": 100
  }
}
```

## Transport Options

### 1. stdio (Standard Input/Output)

```
+-------------+         stdin/stdout         +-------------+
|    Host     |<---------------------------->|   Server    |
|  (Claude)   |    (local subprocess)        |  (your app) |
+-------------+                              +-------------+
```

**Best for:** Local tools, development, fast iteration.

**Characteristics:**
- Server runs as subprocess of host
- No network exposure
- No built-in auth (relies on local environment)
- Fastest setup

```python
# stdio transport setup
from mcp.server import Server
from mcp.server.stdio import stdio_server

async def main():
    # Initialize the core MCP Server instance with a descriptive name
    server = Server("my-local-server")

    # Establish standard I/O communication channels to handle requests/responses
    async with stdio_server(server) as (read_stream, write_stream):
        await server.run(read_stream, write_stream)
```

### 2. Streamable HTTP (Current Standard for Remote)

```
+-------------+         HTTPS          +-------------+
|    Host     |<---------------------->|   Server    |
|  (Claude)   |   (stateless HTTP)     |  (cloud)    |
+-------------+                        +-------------+
```

**Best for:** Networked servers, production, multiple clients.

**Characteristics:**
- Over HTTPS
- Supports multiple clients
- Stateless core (scales horizontally)
- Requires authentication

```python
# Streamable HTTP transport setup (conceptual)
from mcp.server import Server
from mcp.server.http import http_server

async def main():
    # Initialize the remote server instance
    server = Server("my-remote-server")

    # Start HTTP-based transport listening on host port
    await http_server(server, host="0.0.0.0", port=8080)
```

### 3. SSE (Server-Sent Events) — LEGACY

> **Deprecated.** Recognize it in old tutorials, but don't build new servers on it.

## Stateful vs. Stateless

| Aspect | Stateful (Legacy) | Stateless (Current) |
|--------|-------------------|---------------------|
| Connections | Long-lived | Short request/response |
| Scaling | Harder | Horizontal scaling on ordinary HTTP |
| Complexity | Higher | Lower |
| Production | Not recommended | **Recommended** |

## Key Resources

- [Transports Section of Spec](https://github.com/modelcontextprotocol/modelcontextprotocol)
- [JSON-RPC 2.0 Spec](https://www.jsonrpc.org/specification)

---

# Lecture 4: Setting Up Your Development Environment

## Prerequisites Checklist

Before writing code, ensure you have:

- [ ] **Python 3.10+** installed
- [ ] **uv** (modern Python package manager) installed
- [ ] **Git** for version control
- [ ] **Node.js** (for MCP Inspector)
- Basic knowledge of:
  - [ ] JSON
  - [ ] Async programming (`async`/`await`)
  - [ ] Type hints
  - [ ] HTTP basics
  - [ ] CLI/terminal

## Step 1: Install uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Verify
uv --version
```

## Step 2: Create Your Project

```bash
# Create project directory
mkdir my-mcp-server
cd my-mcp-server

# Initialize with uv
uv init

# Create virtual environment
uv venv

# Activate (Unix/macOS)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate
```

## Step 3: Install Dependencies

```bash
# Option A: Official Python SDK (recommended for production)
uv pip install "mcp[cli]>=1.0,<2.0"

# Option B: FastMCP (higher-level, less boilerplate)
uv pip install "fastmcp>=1.0"

# Common additional dependencies
uv pip install httpx python-dotenv pydantic

# Pin exact versions in requirements.txt
echo "mcp[cli]==1.6.0" > requirements.txt
echo "httpx==0.27.0" >> requirements.txt
echo "python-dotenv==1.0.0" >> requirements.txt
```

> **Important:** Pin exact SDK versions. The spec moves fast, and minor releases can break things.

## Step 4: Project Structure

```
my-mcp-server/
├── pyproject.toml          # Project metadata
├── requirements.txt        # Pinned dependencies
├── .env                    # Environment variables (gitignored!)
├── .gitignore
├── src/
│   └── my_mcp_server/
│       ├── __init__.py
│       ├── server.py       # Main server implementation
│       ├── tools/          # Tool definitions
│       ├── resources/      # Resource definitions
│       ├── prompts/        # Prompt templates
│       └── utils/          # Helpers, validators
└── tests/
    ├── test_tools.py
    └── test_server.py
```

## Step 5: Configure pyproject.toml

```toml
[project]
name = "my-mcp-server"
version = "0.1.0"
description = "A production-ready MCP server"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "mcp[cli]>=1.0,<2.0",
    "httpx>=0.27.0",
    "python-dotenv>=1.0.0",
    "pydantic>=2.0.0",
]

[project.scripts]
my-mcp-server = "my_mcp_server.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

## Key Resources

- [Python Official Tutorial](https://docs.python.org/3/tutorial/)
- [uv Documentation](https://docs.astral.sh/uv/)
- [MDN JavaScript Async Guide](https://developer.mozilla.org/en-US/docs/Learn/JavaScript/Asynchronous)
- [FastMCP Quickstart](https://gofastmcp.com/getting-started/welcome)

---

# Lecture 5: Building Your First Server

## Approach A: High-Level with FastMCP

`FastMCP` (a high-level layer built atop the core SDK) minimizes boilerplate code. It automatically parses docstrings, function signatures, and type hints to generate correct JSON-RPC schemas.

Here is a fully functional, commented file assistant server:

```python
# src/my_mcp_server/server.py
import os
import sys
from fastmcp import FastMCP

# 1. Initialize FastMCP with your server name
mcp = FastMCP("Local-File-Assistant")

# WARNING: In stdio-transport-based servers, ALWAYS log debugging info to sys.stderr.
# Writing logs to sys.stdout corrupts JSON-RPC communication on stdio, breaking connection.
print("Server starting up...", file=sys.stderr)

# 2. Add a simple Tool using the @mcp.tool() decorator.
# FastMCP reads type annotations (path: str) and docstrings to auto-generate schema parameters.
@mcp.tool()
async def read_local_file(path: str) -> str:
    """
    Reads the content of a local text file.

    Args:
        path: Absolute file path to read.
    """
    # Defensive programming: Ensure path is safe and exists
    if not os.path.exists(path):
        return f"Error: File '{path}' does not exist."

    try:
        # Perform asynchronous or synchronous reading
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()
        return content
    except Exception as e:
        # Gracefully capture and return the error message as tool output
        return f"Failed to read file: {str(e)}"

# 3. Running the server
def main():
    # Runs the stdio-based transport layer by default
    mcp.run()

if __name__ == "__main__":
    main()
```

## Approach B: Low-Level with base mcp.server SDK

When building production enterprise integrations, you may want precise control over capabilities negotiation and customized lifecycle hooks. For that, use the base `mcp` SDK.

```python
# src/my_mcp_server/server.py (Low-Level SDK implementation)
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent

# Initialize the low-level Server
server = Server("Low-Level-Assistant")

# Register custom capabilities (like tools) manually
@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """Return the list of tools this server supports."""
    return [
        Tool(
            name="calculate_sum",
            description="Adds two numbers together.",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "First number"},
                    "b": {"type": "number", "description": "Second number"}
                },
                "required": ["a", "b"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute the specified tool based on client request."""
    if name == "calculate_sum":
        a = arguments.get("a", 0)
        b = arguments.get("b", 0)
        result = a + b
        # Always return structured content as specified by the protocol
        return [TextContent(type="text", text=f"The sum of {a} and {b} is {result}")]
    raise ValueError(f"Tool {name} not found")

async def main():
    # Use standard input/output streams to communicate with the client
    async with stdio_server(server) as (read_stream, write_stream):
        await server.run(read_stream, write_stream)

if __name__ == "__main__":
    asyncio.run(main())
```

---

# Lecture 6: Tools, Resources & Prompts

Let's dive deep into structural components with highly polished, functional code blocks.

## 1. Tools (Model-Controlled Executable Code)

Tools allow the model to interact with the external world. A tool must accept JSON-serializable parameters and return structured text, images, or files. We use **Pydantic** models inside FastMCP or standard type declarations.

```python
from pydantic import BaseModel, Field
from fastmcp import FastMCP
import httpx

mcp = FastMCP("Weather-Service")

# Define a clean request model using Pydantic for validation
class ForecastRequest(BaseModel):
    city: str = Field(description="Name of the city, e.g. London, Paris")
    days: int = Field(default=3, description="Forecast duration in days (1-7)")

# FastMCP fully supports Pydantic schemas as argument signatures
@mcp.tool()
async def get_weather_forecast(request: ForecastRequest) -> str:
    """
    Retrieves the weather forecast for a specified city.
    """
    # Strict validation inside the handler
    if request.days < 1 or request.days > 7:
        return "Error: Forecast duration must be between 1 and 7 days."

    # Perform external async HTTP request
    async with httpx.AsyncClient() as client:
        try:
            # Mock query to open-source or public weather API
            url = f"https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&daily=temperature_2m_max&timezone=GMT"
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            max_temp = data.get("daily", {}).get("temperature_2m_max", [20.0])[0]

            return f"Weather forecast for {request.city}: Sunny, Max Temperature of {max_temp}°C for the next {request.days} days."
        except Exception as e:
            return f"Error contacting weather service API: {str(e)}"
```

## 2. Resources (Read-Only Contextual Data)

Resources represent static or dynamic data files (like application configurations, database definitions, or server logs) that the model can load into context.

```python
from fastmcp import FastMCP

mcp = FastMCP("Log-Explorer")

# Declare a dynamic resource template with URI patterns
@mcp.resource("logs://system/{log_type}")
async def get_system_logs(log_type: str) -> str:
    """
    Retrieve real-time system log details by log type.

    Args:
        log_type: Type of logs to read (e.g., 'error', 'access', 'auth')
    """
    # Ensure standard types are enforced
    allowed_types = ["error", "access", "auth"]
    if log_type not in allowed_types:
        raise ValueError(f"Invalid log type '{log_type}'. Allowed: {allowed_types}")

    # Read relevant data. Here we provide simulated structured telemetry logs.
    if log_type == "error":
        return "[2025-10-10 14:32:01] ERROR: database connection pool exhausted in pool-1"
    elif log_type == "access":
        return "[2025-10-10 14:31:55] INFO: GET /api/v1/health status=200 duration=4ms"
    else:
        return "[2025-10-10 14:30:11] WARNING: failed login attempt for user 'admin' from IP 192.168.1.50"
```

## 3. Prompts (Parameterized Input Blueprints)

Prompts are predefined templates that orchestrate complex workflows or enforce system instructions for specialized tasks.

```python
from fastmcp import FastMCP

mcp = FastMCP("Code-Reviewer")

@mcp.prompt()
def analyze_sql_injection(sql_query: str) -> str:
    """
    Provides a detailed system security analysis prompt for detecting potential SQL injections.
    """
    return f"""Analyze the following user-supplied SQL query for potential SQL Injection (SQLi) vulnerabilities.

SQL query under test:
```sql
{sql_query}
```

Please perform the following reviews:
1. Identify any unparameterized user-input variables concatenated directly into the query string.
2. Outline potential risk levels (Low, Medium, Critical).
3. Provide the secured equivalent statement using parameterized or prepared queries.
"""
```

---

# Lecture 7: Testing & Debugging

Testing local servers over standard I/O pipes requires careful tooling because normal interactive debuggers can corrupt standard output communication.

## 1. Using the MCP Inspector

The official CLI Inspector is the best way to interactively inspect capabilities, run tools, and view raw JSON-RPC messages.

```bash
# Run the inspector with your script
npx @modelcontextprotocol/inspector python src/my_mcp_server/server.py
```

This launches a web page (typically at `http://localhost:3000`) showing available tools, resource schemas, and an interactive interface to query them.

## 2. Programmatic Testing with Pytest

To run tests in a CI/CD pipeline, write automated integration tests using the official MCP client SDK (`stdio_client`).

```python
# tests/test_server.py
import pytest
import sys
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Mark all test functions in this module as asynchronous
pytestmark = pytest.mark.asyncio

async def test_server_tools():
    """
    Launches the MCP server as a subprocess, initializes a client session,
    and queries the 'read_local_file' tool to verify functionality.
    """
    # 1. Define server parameters to run your script as a python subprocess
    # Point to the actual server entrypoint
    server_path = os.path.abspath("src/my_mcp_server/server.py")
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[server_path],
        env=os.environ.copy()
    )

    # 2. Establish connection client using the stdio transport
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # Step A: Perform handshake initialization
            await session.initialize()

            # Step B: List tools and verify registration
            tools_result = await session.list_tools()
            tools = tools_result.tools
            assert any(t.name == "read_local_file" for t in tools), "Tool 'read_local_file' was not registered"

            # Step C: Execute tool with a known test argument
            result = await session.call_tool(
                name="read_local_file",
                arguments={"path": "non_existent_file.txt"}
            )

            # Assert schema content
            assert len(result.content) > 0
            assert "does not exist" in result.content[0].text
```

---

# Lecture 8: Security - The Make-or-Break Phase

When a server runs as a local process or on production environments, it has access to resources and data. An AI model can fall victim to prompt injection, potentially executing destructive commands or exfiltrating data via parameters. **Security is non-negotiable.**

## 1. File Path Sandboxing (Roots Constraint)

Ensure files accessed by your server are strictly constrained to dedicated root directories. Never resolve arbitrary relative paths containing `..` sequences.

```python
import os
from fastmcp import FastMCP

mcp = FastMCP("Safe-File-Server")

# Restrict the tool to a secure sandbox directory
SAFE_DIR = os.path.abspath("./sandbox")

def is_safe_path(base: str, path: str) -> bool:
    """Verifies that the target path resides strictly inside the base directory."""
    resolved_target = os.path.abspath(path)
    # Check if the path begins with the safe directory path
    return resolved_target.startswith(base)

@mcp.tool()
async def write_sandbox_file(filename: str, content: str) -> str:
    """
    Writes data safely to a file within the secure sandbox directory.
    """
    target_path = os.path.join(SAFE_DIR, filename)

    if not is_safe_path(SAFE_DIR, target_path):
        return "Access Denied: Attempt to traverse out of the sandbox directory is blocked."

    try:
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File '{filename}' successfully saved inside the sandbox."
    except Exception as e:
        return f"System error writing file: {str(e)}"
```

## 2. Preventing Shell Injection

Avoid invoking subprocesses using shell interpreter strings (`shell=True` or `os.system`). Always pass arguments as an explicit array to bypass command-parsing injection.

```python
import subprocess
from fastmcp import FastMCP

mcp = FastMCP("System-Utilities")

# SECURE: Explicit array execution
@mcp.tool()
async def ping_host(host: str) -> str:
    """
    Pings a hostname to verify network connectivity.
    """
    # Defensive input validation: Allow only letters, numbers, and dots
    safe_host = "".join(char for char in host if char.isalnum() or char in ".-")

    try:
        # Pass parameters as a list to avoid shell parsing vulnerabilities
        # NEVER use shell=True with user/LLM input!
        result = subprocess.run(
            ["ping", "-c", "2", safe_host],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout
    except subprocess.TimeoutExpired:
        return "Connection timed out."
    except Exception as e:
        return f"Failed to execute command: {str(e)}"
```

## 3. Human-In-The-Loop Approvals

For tools that can modify, delete, or commit actions, require an explicit user confirmation or audit log step. On local clients like Claude Desktop, the client software is responsible for prompting the user for approval. If you are building custom clients, build a confirmation dialog before completing destructive tool invocations.

---

# Lecture 9: Production Deployment

When scaling up beyond local developer machine runs, MCP servers run inside isolated environments with networking boundaries.

## 1. Containerization (Multi-stage Dockerfile)

Deploying as a microservice using Docker keeps dependencies and runtimes clean.

```dockerfile
# Use a highly-optimized multi-stage build structure
FROM python:3.12-slim AS builder

# Install uv package manager
COPY --from=astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Install dependencies first (for layer caching)
COPY requirements.txt .
RUN uv pip install --no-cache -r requirements.txt --system

# Copy application source
COPY src/ /app/src/

# Final clean stage
FROM python:3.12-slim

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /app /app

ENV PYTHONUNBUFFERED=1
ENV PATH="/usr/local/bin:$PATH"

# Run our MCP server via HTTP transport for remote access
EXPOSE 8080
CMD ["python", "src/my_mcp_server/server.py"]
```

## 2. Remote Streamable HTTP Host & Security

Remote servers use HTTP as transport. You should always enforce standard TLS (HTTPS) and API authentication keys on the headers.

```python
# Production entrypoint using Streamable HTTP
import os
import sys
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
import uvicorn

mcp = FastMCP("Production-Cloud-Server")

# FastMCP can wrap standard ASGI (Starlette) apps for robust hosting
app = mcp.get_asgi_app()

# Secure HTTP middleware for API keys
@app.middleware("http")
async def verify_auth_token(request, call_next):
    # Retrieve bearer token from Authorization header
    auth_header = request.headers.get("Authorization")
    expected_token = os.environ.get("MCP_API_KEY")

    # Simple production token gate
    if not expected_token or auth_header != f"Bearer {expected_token}":
        return JSONResponse({"error": "Unauthorized Access"}, status_code=401)

    return await call_next(request)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

---

# Lecture 10: Advanced Topics & Future Roadmap

As you design world-class integration systems, harness these cutting-edge protocol patterns.

## 1. Sampling (LLM Delegation)

Sampling lets a server temporarily delegate a natural language sub-task back to the Client's LLM engine. For example, if your SQL tool retrieves a complex database payload, the server can request the client's LLM to summarize it *before* returning the final response.

```python
# Conceptual sampling flow
# Check if host client has sampling capability enabled
if client_session.capabilities.sampling:
    summary_request = await client_session.create_message(
        messages=[
            {
                "role": "user",
                "content": {"type": "text", "text": "Format this JSON payload nicely for a dashboard:" + str(raw_data)}
            }
        ],
        model_preferences={"type": "smart"} # Requests high-tier model
    )
    formatted_text = summary_request.content.text
```

## 2. Dynamic Resources and Pagination

When loading massive datasets as Resources, avoid loading everything at once into context. Instead, split resources into pages and define pagination links.

```python
from mcp.types import PaginatedResult

# A paginated resource loader
async def load_database_rows(table: str, cursor: int = 0, limit: int = 50):
    # Yields limited rows and provides a 'nextCursor' string
    rows = fetch_rows(table, cursor, limit)
    return PaginatedResult(
        items=[row_to_text(r) for r in rows],
        nextCursor=str(cursor + limit) if len(rows) == limit else None
    )
```

## 3. Protocol Evolution & Next-Gen Specs

MCP is rapidly evolving. Key initiatives currently driven by the open-source community:

- **Enhanced Multi-Agent Interoperability**: Seamless context swapping when an agent passes an execution chain to another agent sub-node.
- **Bi-directional Stream Handshakes**: Supporting streaming tool output (e.g., real-time progress on media rendering or complex compilation pipelines).
- **Global Discovery Hubs**: Centralized, secure registries for verified MCP servers, making it easy to download and spin up local sandboxed server environments on demand.

---
*End of Masterclass. Keep building safe and powerful servers!*
