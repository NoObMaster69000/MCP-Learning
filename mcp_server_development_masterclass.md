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
7. [Lecture 6.5: Adding Skills & Integration Guide (Host Setup)](#lecture-65-adding-skills--integration-guide-host-setup)
   - [Step 1: Develop the Custom Skill (Python)](#step-1-develop-the-custom-skill-python)
   - [Step 2: Configure Claude Desktop to Use the Skill](#step-2-configure-claude-desktop-to-use-the-skill)
   - [Step 3: Verify the Integrated Skill](#step-3-verify-the-integrated-skill)
   - [Step 4: Accessing MCP Programmatically with Client-Side Code (Python Client)](#step-4-accessing-mcp-programmatically-with-client-side-code-python-client)
8. [Lecture 7: Testing & Debugging](#lecture-7-testing---debugging)
9. [Lecture 8: Security - The Make-or-Break Phase](#lecture-8-security---the-make-or-break-phase)
10. [Lecture 9: Production Deployment](#lecture-9-production-deployment)
11. [Lecture 10: Advanced Topics & Future Roadmap](#lecture-10-advanced-topics--future-roadmap)
12. [Lecture 11: Composing, Namespacing & Transforms](#lecture-11-composing-namespacing--transforms)
13. [Lecture 12: Interactive UIs & FastMCP UIs (FastMCPApp)](#lecture-12-interactive-uis--fastmcp-uis-fastmcpapp)
14. [Lecture 13: Advanced Authentication & Security Gating](#lecture-13-advanced-authentication--security-gating)
15. [Lecture 14: Next-Gen Utilities: Tasks, Telemetry & Versioning](#lecture-14-next-gen-utilities-tasks-telemetry--versioning)

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

# Lecture 6.5: Adding Skills & Integration Guide (Host Setup)

A **"Skill"** in MCP is simply a custom Tool registered with an MCP server that the AI model can dynamically invoke. Once registered, you integrate the server as a background service in your preferred AI Host (like **Claude Desktop**). The host client reads the server's registered tools and exposes them to the AI model as active skills.

This guide demonstrates how to create a custom **Text Formatting and Sentiment Extraction Skill**, integrate it with Claude Desktop, and write custom client-side code to access it programmatically.

## Step 1: Develop the Custom Skill (Python)

Create or update your server file to expose a new tool:

```python
# src/my_mcp_server/skills.py
import sys
from fastmcp import FastMCP
from pydantic import BaseModel, Field

# Initialize FastMCP server
mcp = FastMCP("Developer-Skills-Hub")

# Define parameter structure with explicit descriptions
class TextAnalyzerInput(BaseModel):
    text: str = Field(description="The target text string to be analyzed and reformatted.")
    uppercase: bool = Field(default=False, description="Set to True to convert text to uppercase.")

# Register the skill using the @mcp.tool decorator
@mcp.tool()
async def analyze_and_format_text(input_data: TextAnalyzerInput) -> str:
    """
    Exposes a text analysis skill that computes word count, estimates sentiment,
    and returns a formatted summary of the input text.
    """
    text = input_data.text
    if not text.strip():
        return "Error: Empty text provided."

    # Compute word count
    words = text.split()
    word_count = len(words)

    # Convert text layout based on argument flags
    formatted_text = text.upper() if input_data.uppercase else text

    # Simple sentiment estimation logic
    positive_words = {"good", "great", "excellent", "happy", "love", "awesome", "fast"}
    negative_words = {"bad", "slow", "error", "failed", "broken", "worst", "sad"}

    pos_score = sum(1 for w in words if w.lower().strip(",.!?") in positive_words)
    neg_score = sum(1 for w in words if w.lower().strip(",.!?") in negative_words)

    sentiment = "Neutral"
    if pos_score > neg_score:
        sentiment = "Positive"
    elif neg_score > pos_score:
        sentiment = "Negative"

    # Return structured summary for host ingestion
    return f"""### Text Analysis Results:
- **Original Word Count**: {word_count}
- **Estimated Sentiment**: {sentiment}
- **Formatted Output**:
"{formatted_text}"
"""

def main():
    # Run server on stdio transport
    mcp.run()

if __name__ == "__main__":
    main()
```

## Step 2: Configure Claude Desktop to Use the Skill

To make this custom skill active in Claude Desktop, register your server in Claude's global configuration file.

### Finding Claude Desktop's Configuration File
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### Creating the Configuration File
If the file doesn't exist, create it. Add your custom server mapping under `mcpServers`.

> **Crucial Warning:** You must use **absolute paths** for both the `command` (the python executable in your virtual environment) and your server script arguments. Local relative paths will fail because Claude Desktop runs from its own system directories.

```json
{
  "mcpServers": {
    "developer-skills-hub": {
      "command": "/Users/yourusername/my-mcp-server/.venv/bin/python",
      "args": [
        "/Users/yourusername/my-mcp-server/src/my_mcp_server/skills.py"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

*Replace `/Users/yourusername/my-mcp-server/` with the absolute path to your local repository directory.*

## Step 3: Verify the Integrated Skill

1. **Restart Claude Desktop**: Fully quit (Cmd+Q or Alt+F4) and reopen Claude Desktop to trigger a clean capabilities handshake.
2. **Look for the Hammer Icon**: When starting a new conversation, you should see a small hammer icon 🛠️ in the message box, indicating your custom MCP server has connected successfully.
3. **Ask Claude to Use Your Skill**: You do not need to invoke specific JSON commands. Prompt Claude in natural language:
   > *"Claude, can you analyze and format the text 'The service was incredibly fast and excellent' using my custom skills hub?"*
4. **LLM Invocation**: Claude will recognize the request, matching it against the registered tool parameters, invoke the `analyze_and_format_text` skill, and display the formatted output containing word count, sentiment analysis, and formatted text directly inside the chat interface.

## Step 4: Accessing MCP Programmatically with Client-Side Code (Python Client)

If you are building your own AI application or custom host, you need to connect to the MCP server programmatically from the client side. Below is a complete, production-ready Python script showing how to write a client that spawns the server, negotiates connection capabilities, and calls your custom tool.

```python
# src/my_mcp_client/client_example.py
import asyncio
import os
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run_custom_mcp_client():
    """
    Spawns the MCP server as a subprocess, connects via stdio,
    queries available tools, and executes the custom skill programmatically.
    """
    print("Initializing programmatic MCP Client...", file=sys.stderr)

    # 1. Configure the server parameters.
    # The client launches the server as a background subprocess using stdio.
    # We must use the absolute path to the target server python file.
    server_script_path = os.path.abspath("src/my_mcp_server/skills.py")

    server_parameters = StdioServerParameters(
        command=sys.executable,  # Uses the current active python interpreter
        args=[server_script_path],
        env=os.environ.copy()     # Copy parent environment variables
    )

    # 2. Establish connection to the server's standard input/output channels.
    print(f"Connecting to MCP server at: {server_script_path}...", file=sys.stderr)
    async with stdio_client(server_parameters) as (read_stream, write_stream):
        # 3. Instantiate the Client Session.
        async with ClientSession(read_stream, write_stream) as session:
            # 4. Perform handshaking initialization.
            # This negotiates protocol capabilities and protocol version support.
            print("Performing connection handshake...", file=sys.stderr)
            await session.initialize()
            print("Successfully connected and initialized session!", file=sys.stderr)

            # 5. List all available tools exposed by the server.
            print("\n--- Querying Server Capabilities ---", file=sys.stderr)
            tools_response = await session.list_tools()
            available_tools = tools_response.tools
            print(f"Detected {len(available_tools)} registered tools:", file=sys.stderr)
            for tool in available_tools:
                print(f"  - Tool Name: {tool.name}", file=sys.stderr)
                print(f"    Description: {tool.description}", file=sys.stderr)
                print(f"    Input Parameters Schema: {tool.inputSchema}", file=sys.stderr)

            # Check if our custom text analyzer skill exists
            skill_to_call = "analyze_and_format_text"
            if not any(t.name == skill_to_call for t in available_tools):
                print(f"Error: Required tool '{skill_to_call}' not found on server.", file=sys.stderr)
                return

            # 6. Invoke the custom tool/skill programmatically.
            print(f"\n--- Invoking Tool: '{skill_to_call}' programmatically ---", file=sys.stderr)
            tool_arguments = {
                "input_data": {
                    "text": "The implementation of the Model Context Protocol is clean and extremely fast!",
                    "uppercase": True
                }
            }

            print(f"Sending request arguments: {tool_arguments}", file=sys.stderr)
            call_result = await session.call_tool(
                name=skill_to_call,
                arguments=tool_arguments
            )

            # 7. Process and output the tool results.
            print("\n--- Executing Tool Result Summary ---", file=sys.stderr)
            for content_item in call_result.content:
                # Inspect the returned content type
                if content_item.type == "text":
                    print("Received Response Text:", file=sys.stdout)
                    print(content_item.text, file=sys.stdout)
                else:
                    print(f"Received non-text payload type: {content_item.type}", file=sys.stderr)

if __name__ == "__main__":
    # Ensure async loop is executed correctly
    try:
        asyncio.run(run_custom_mcp_client())
    except KeyboardInterrupt:
        print("\nClient terminated by user.", file=sys.stderr)
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

# Lecture 11: Composing, Namespacing & Transforms

As your Model Context Protocol deployments scale from a single server to complex enterprise ecosystems, you will inevitably hit the limit of monolithic code structures. Composing multiple decoupled servers into a unified API gateway, organizing tools using namespaces, and dynamically transforming component signatures are essential production techniques. Standalone FastMCP excels at these workflows through its **Provider** and **Transform** architectures.

```
                  +----------------------------------+
                  |           Parent Gateway         |
                  |          (FastMCP Server)        |
                  +-----------------+----------------+
                                    |
                  +-----------------+----------------+
                  |            Transforms            |
                  |  - Namespace    - ToolSearch     |
                  |  - ToolTransform - *AsTools      |
                  +-----------------+----------------+
                                    |
         +--------------------------+--------------------------+
         |                                                     |
         v                                                     v
+--------+---------+                                  +--------+---------+
|  Child Server A  |                                  |   Proxy Provider |
|  (LocalProvider) |                                  |  (Remote Server) |
+------------------+                                  +------------------+
```

---

## 1. Mounting and Composition

FastMCP allows you to compose multiple servers using the `.mount()` method. When you mount a child server, all of its tools, resources, templates, and prompts are linked dynamically to the parent.

```python
# composition_gateway.py
import asyncio
from fastmcp import FastMCP

# Define our parent orchestrator
gateway = FastMCP("Enterprise-Gateway")

# Define child domain server 1: Database Operations
db_server = FastMCP("Database-Subserver")

@db_server.tool()
def get_user_record(user_id: int) -> dict:
    """Retrieves a database row for a specific user ID."""
    return {"id": user_id, "status": "active", "tier": "enterprise"}

# Define child domain server 2: Billing & Subscriptions
billing_server = FastMCP("Billing-Subserver")

@billing_server.tool()
def process_invoice(user_id: int, amount: float) -> str:
    """Generates and processes a billing invoice."""
    return f"Invoice of ${amount:.2f} processed successfully for user #{user_id}."

# Mount both child subservers into our unified parent gateway.
# Namespacing avoids identifier collision.
gateway.mount(db_server, namespace="db")
gateway.mount(billing_server, namespace="billing")

# After composition, clients query a single parent endpoint and see namespaced tools:
# - db_get_user_record
# - billing_process_invoice
```

---

## 2. Proxying External Servers

Composing isn't limited to local Python instances. Using `create_proxy()`, you can mount remote servers running over HTTP/SSE, or external commands running in separate subprocesses (such as standard npm/uvx MCP packages).

```python
# proxy_composed_server.py
from fastmcp import FastMCP
from fastmcp.server import create_proxy

gateway = FastMCP("Multi-Language-Gateway")

# 1. Mount a remote HTTP/SSE weather server
remote_weather_proxy = create_proxy("https://weather-api.example.com/mcp", name="weather-service")
gateway.mount(remote_weather_proxy, namespace="weather")

# 2. Mount a local sqlite command-line server via uvx configuration
sqlite_config = {
    "mcpServers": {
        "default": {
            "command": "uvx",
            "args": ["mcp-server-sqlite", "--db", "company_records.db"]
        }
    }
}
sqlite_proxy = create_proxy(sqlite_config, name="sqlite-service")
gateway.mount(sqlite_proxy, namespace="records")

# 3. Cache Proxy listings to optimize network performance.
# By default, ProxyProvider caches tool/resource metadata lists to prevent
# redundant upstream roundtrips. Set cache_ttl to customize or disable (0).
from fastmcp.server.providers.proxy import ProxyProvider
# For highly dynamic servers, you can configure a short TTL or turn caching off:
# proxy_provider = ProxyProvider(lambda: create_client(), cache_ttl=60)
```

---

## 3. Namespacing and Identifier Mapping

The `Namespace` transform automatically prefixes all component names as they flow through the parent server, ensuring complete isolation.

| Component Type | Unnamespaced | Namespaced with `Namespace("infra")` |
|----------------|--------------|--------------------------------------|
| **Tool**       | `check_cpu`  | `infra_check_cpu`                    |
| **Prompt**     | `analyze`    | `infra_analyze`                      |
| **Resource**   | `data://sys` | `data://infra/sys`                   |
| **Template**   | `log://{id}` | `log://infra/{id}`                   |

```python
from fastmcp.server.transforms import Namespace

# Manually add a Namespace transform to a specific LocalProvider
from fastmcp.server.providers import LocalProvider

provider = LocalProvider()
# Prefix everything sourced from this local provider with "api"
provider.add_transform(Namespace("api"))
```

---

## 4. Advanced Tool Transformations (`ToolTransform`)

When you mount or proxy a third-party server, you do not control its code. The `ToolTransform` and `ToolTransformConfig` APIs allow you to rename tools, restructure argument properties, hide sensitive variables, or wrap tool execution in custom middleware.

```python
# tool_refactoring.py
from fastmcp import FastMCP
from fastmcp.server.transforms import ToolTransform
from fastmcp.tools.tool_transform import ToolTransformConfig, ArgTransform, forward

mcp = FastMCP("Refactored-Database-Service")

# Original tool with non-ideal argument naming and exposure
@mcp.tool()
def raw_fetch_data_from_db(usr_id: int, p_token: str, limit: int = 50) -> dict:
    """Low-level database fetch."""
    return {"user": usr_id, "limit": limit, "auth": p_token != ""}

# Apply a custom ToolTransform to modify the tool schema and argument behavior
mcp.add_transform(ToolTransform({
    "raw_fetch_data_from_db": ToolTransformConfig(
        name="query_db",  # Rename tool
        description="Safely queries user database records.", # Custom description
        transform_args={
            # 1. Rename 'usr_id' to 'user_id' for model readability
            "usr_id": ArgTransform(name="user_id", description="The target user identifier."),
            # 2. Hide 'p_token' from the model completely and inject a default factory
            "p_token": ArgTransform(hide=True, default_factory=lambda: "SECRET_SYSTEM_TOKEN"),
            # 3. Limit argument can be kept but restricted
            "limit": ArgTransform(name="page_size", default=10, description="Number of rows to fetch.")
        }
    )
}))

# Clients see:
# tool: query_db(user_id: integer, page_size: integer = 10)
# 'p_token' is hidden but automatically injected at runtime.
```

---

## 5. Tool Search Transforms

When a server contains hundreds or thousands of tools, listing them all in a single `list_tools` call overwhelms the LLM's context window. The `ToolSearch` transform replaces the entire catalog with a search interface—presenting only two synthetic meta-tools to the client:
1. `search_tools`: Returns matching tool schemas on-demand.
2. `call_tool`: An execution proxy to invoke a discovered tool by name.

```python
# scalable_search_server.py
from fastmcp import FastMCP
from fastmcp.server.transforms.search import BM25SearchTransform, RegexSearchTransform

# Initialize the server
mcp = FastMCP("Massive-API-Gateway")

# Add a BM25 Search Transform (ranks tools by semantic relevance using BM25 Okapi)
mcp.add_transform(BM25SearchTransform(max_results=5))

# Alternatively, you can use a Regex Search Transform for exact matching:
# mcp.add_transform(RegexSearchTransform(max_results=10))

# Any number of tools can be registered here:
@mcp.tool()
def search_invoices(invoice_id: str) -> str:
    """Retrieve invoicing details."""
    return f"Invoice data: {invoice_id}"

# The client will only detect:
# 1. search_tools(query: string)
# 2. call_tool(name: string, arguments: object)
```

---

## 6. Resources & Prompts as Tools

Some legacy or highly focused MCP clients only support the `Tools` capability, ignoring resource and prompt listings entirely. The `ResourcesAsTools` and `PromptsAsTools` transforms bridge this compatibility gap by generating equivalent tool mappings.

```python
# tool_compatibility_bridge.py
from fastmcp import FastMCP
from fastmcp.server.transforms import ResourcesAsTools, PromptsAsTools

mcp = FastMCP("Compatibility-Hub")

@mcp.resource("config://app")
def get_config() -> str:
    """Application config resource."""
    return '{"debug": false}'

@mcp.prompt()
def code_review(code: str) -> str:
    """Generate code review prompt."""
    return f"Review this code:\n{code}"

# Convert all resources and prompts to executable tools
mcp.add_transform(ResourcesAsTools(mcp))
mcp.add_transform(PromptsAsTools(mcp))

# Now, a tool-only client detects:
# - list_resources: lists available resource templates
# - read_resource: reads specific resources by URI
# - list_prompts: lists available prompt templates
# - get_prompt: retrieves and renders a prompt template
```

---
---

# Lecture 12: Interactive UIs & FastMCP UIs (FastMCPApp)

Model Context Protocol allows tools to go beyond simple text responses. By combining the **MCP Apps extension** (io.modelcontextprotocol/ui) with **Prefab UI components** (built on the `prefab-ui` package), your tools can return fully interactive, reactive user interfaces—such as charts, tables, forms, and custom dashboards—rendered right inside the client conversation window.

```
+--------------------------------------------------------------+
|                         HOST UI                              |
|                                                              |
|  +--------------------------------------------------------+  |
|  |                    Sandboxed iframe                    |  |
|  |                                                        |  |
|  |   [Prefab Renderer / React Application]                 |  |
|  |   Renders JSON component tree into a beautiful UI      |  |
|  |                                                        |  |
|  |         [Select: Region]      [Switch: Target]         |  |
|  |         [============Bar Chart Widget============]     |  |
|  |                                                        |  |
|  +---------------------------+----------------------------+  |
+------------------------------|-------------------------------+
                               | postMessage API
                               v
                     +-------------------+
                     |    MCP Host/Client|
                     +---------|---------+
                               | JSON-RPC (tools/call)
                               v
                     +-------------------+
                     |   FastMCP Server  |
                     +-------------------+
```

---

## 1. FastMCPApp Architecture & Lifecycle

`FastMCPApp` is a dedicated Provider class designed for building interactive applications. It separates your UI entry points (`@app.ui()`, which return a `PrefabApp` components canvas and are model-visible) from backend operations (`@app.tool()`, which handle data mutation and are typically hidden from the model).

```python
# src/my_mcp_server/app.py
from fastmcp import FastMCP, FastMCPApp
from prefab_ui.app import PrefabApp
from prefab_ui.components import Column, Heading, Text, Badge, Row, Button
from prefab_ui.actions import SetState, ShowToast
from prefab_ui.actions.mcp import CallTool
from prefab_ui.rx import RESULT

# 1. Initialize our dedicated MCP application
app = FastMCPApp("Inventory-Manager")
inventory_db: list[dict] = [{"id": 1, "name": "Item A", "quantity": 15}]

# 2. Register a backend tool (hidden from the model, visible only to the UI)
@app.tool()
def add_inventory_item(name: str, qty: int) -> list[dict]:
    """Adds an item to the local database and returns updated rows."""
    inventory_db.append({"id": len(inventory_db) + 1, "name": name, "quantity": qty})
    return list(inventory_db)

# 3. Register a UI entry-point (visible to the model)
@app.ui()
def show_manager_ui() -> PrefabApp:
    """Renders the inventory management dashboard."""
    with Column(gap=4, css_class="p-6") as view:
        Heading("Inventory Manager", level=1)
        Text("Clicking 'Restock' invokes our backend tool dynamically via CallTool.")

        # Add a button that triggers a backend tool call
        Button(
            "Restock Item",
            on_click=CallTool(
                add_inventory_item, # Reference function directly for namespace safety
                arguments={"name": "Restocked Item", "qty": 10},
                on_success=[
                    SetState("items", RESULT),
                    ShowToast("Stock updated!", variant="success")
                ]
            )
        )

    # Return PrefabApp with view and initial state
    return PrefabApp(view=view, state={"items": list(inventory_db)})

# 4. Bind the app to our main FastMCP Server
mcp = FastMCP("Office-Management-Server")
mcp.add_provider(app)
```

---

## 2. Prefab UI Components and Reactivity

Prefab UI provides over 100 components that compile to a React interface. By using the `Rx` state system, the UI can read and write state in the client browser—running interactive loops instantly without making slow network roundtrips back to your server.

```python
# reactive_dashboard.py
from fastmcp import FastMCP
from prefab_ui.app import PrefabApp
from prefab_ui.components import Column, Row, Select, SelectOption, Switch, Text, Metric
from prefab_ui.components.charts import BarChart, ChartSeries
from prefab_ui.components.control_flow import If
from prefab_ui.rx import Rx

mcp = FastMCP("Sales-Explorer")

@mcp.tool(app=True) # Shorthand to register a simple tool as a UI app
def sales_charts() -> PrefabApp:
    """Provides a interactive sales chart with client-side filters."""
    east_data = [{"month": "Jan", "sales": 15000}, {"month": "Feb", "sales": 18000}]
    west_data = [{"month": "Jan", "sales": 8000}, {"month": "Feb", "sales": 12000}]

    # Initialize state dictionary on PrefabApp
    initial_state = {
        "region": "east",
        "east": east_data,
        "west": west_data,
        "show_target": True
    }

    with PrefabApp(state=initial_state) as app:
        # Determine active data dynamically based on the current 'region' state key
        with Column(
            gap=6,
            css_class="p-6",
            let={"active_data": "{{ region == 'east' ? east : west }}"}
        ) as view:
            with Row(gap=4, align="center"):
                # Selector writes directly to the 'region' state key on change
                with Select(name="region", css_class="w-40"):
                    SelectOption(value="east", label="Eastern Region")
                    SelectOption(value="west", label="Western Region")

                # Switch toggles boolean target visibility state
                Switch(name="show_target", css_class="ml-auto")
                Text("Show Target Line", css_class="text-sm")

            # Render a responsive chart that binds to our reactive let variable
            BarChart(
                data=Rx("active_data"),
                series=[ChartSeries(data_key="sales", label="Monthly Revenue")],
                x_axis="month"
            )

            # Conditionally render elements in the browser without server roundtrips
            with If(Rx("show_target")):
                Metric(label="Q1 Regional Target", value="$20,000")

    return app
```

---

## 3. Built-in Capability Providers

FastMCP includes five production-ready interactive providers that can be registered in a single line of code to provide complex user-interaction paradigms.

### A. Drag-And-Drop File Upload (`FileUpload`)

Lets users upload files through an interactive UI zone, bypassing LLM context token limitations.

```python
from fastmcp import FastMCP
from fastmcp.apps.file_upload import FileUpload

mcp = FastMCP("Safe-File-Processor")

# Add FileUpload provider (handles storage, listing, and reading)
file_provider = FileUpload(max_file_size=10 * 1024 * 1024) # 10 MB limit
mcp.add_provider(file_provider)

# You can access uploaded files in your standard tools
@mcp.tool()
async def process_user_upload(filename: str) -> str:
    """Processes an uploaded file from the secure cache."""
    # FileUpload stores files scoped by MCP session in-memory by default.
    # To configure S3 or distributed file storage, subclass FileUpload
    # and override 'on_store', 'on_list', and 'on_read'.
    return f"Processed uploaded file: {filename}"
```

### B. Human-In-The-Loop Approvals (`Approval`)

Binds a security gate around critical tools. The model presents what it's about to do, the user approves or rejects, and the choice is messaged back.

```python
from fastmcp import FastMCP
from fastmcp.apps.approval import Approval

mcp = FastMCP("Deploy-System")
mcp.add_provider(Approval())

# The LLM calls `request_approval` with a summary before taking action.
# Once the user clicks "Approve", the confirmation is injected back as a message,
# and the LLM continues safely.
```

### C. Presenting Clickable Option Buttons (`Choice`)

Instead of asking the user to type a response, present a set of options as clickable buttons.

```python
from fastmcp import FastMCP
from fastmcp.apps.choice import Choice

mcp = FastMCP("Interactive-Survey")
mcp.add_provider(Choice())

# The LLM calls `choose(prompt="...", options=["Tacos", "Pizza"])`.
# The clicked selection is pushed back to the chat stream.
```

### D. Form Input from Pydantic Models (`FormInput`)

Generates a validated input form from any Pydantic model class.

```python
from pydantic import BaseModel, Field
from fastmcp import FastMCP
from fastmcp.apps.form import FormInput

class ContactCard(BaseModel):
    name: str = Field(description="Full name")
    email: str = Field(description="Valid email address")
    subscribe: bool = Field(default=True, description="Subscribe to updates")

mcp = FastMCP("Directory-Server")

# Add a form provider. On submit, validations run in the browser.
mcp.add_provider(FormInput(
    model=ContactCard,
    title="Add New Contact",
    submit_text="Create Card",
    # Pass an optional callback to handle the validated Pydantic model instance
    on_submit=lambda card: f"Created contact: {card.name} ({card.email})"
))
```

### E. Generative UI (`GenerativeUI`)

Empowers the LLM to write its own Prefab Python code at runtime. The user watches the components stream in as Pyodide executes the script progressively in the browser.

```python
from fastmcp import FastMCP
from fastmcp.apps.generative import GenerativeUI

mcp = FastMCP("Studio-Server")

# Registers 'generate_prefab_ui' (executes Python in a sandboxed Pyodide frame)
# and 'search_prefab_components' (introspects available Prefab UI classes)
mcp.add_provider(GenerativeUI())
```

---
---

# Lecture 13: Advanced Authentication & Security Gating

When deploying Model Context Protocol servers over remote HTTP transports, security is paramount. Since MCP clients expect to register automatically (via Dynamic Client Registration), traditional OAuth 2.0 architectures must be bridged safely. Standalone FastMCP provides robust security mitigations and first-class IDP integrations to protect your system.

---

## 1. The OAuth Proxy & Token Factory

Traditional OAuth providers (GitHub, Google, Azure, AWS, Auth0) require manual registration and fixed redirect URIs, making them incompatible with MCP clients that use dynamic localhost ports. FastMCP's **OAuth Proxy** bridges this gap: it presents a DCR-compliant interface to MCP clients while proxying credentials upstream.

```
                      +-------------------+
                      |     MCP Client    |
                      | (localhost:54321) |
                      +---------+---------+
                                |
                     1. register| (DCR)
                                v
+------------------+  2. auth   +-------------------+  3. proxy auth +------------------+
|                  |<-----------|  FastMCP Server   |--------------->|   Upstream IdP   |
|   OAuth User     |  redirect  |    (OAuth Proxy)  |    redirect    |  (GitHub, etc.)  |
|                  |----------->|  (server:8000)    |<---------------|                  |
+------------------+  4. approve+---------+---------+   5. auth code +------------------+
                                          |
                                          | 6. exchange
                                          v
                                +-------------------+
                                |  Issued JWT Token |
                                | (Aud: mcp-server) |
                                +-------------------+
```

### The Token Factory Architecture (Preventing Token Passthrough)

To comply with **MCP Security Best Practices**, the OAuth Proxy implements a Token Factory: **it never forwards the upstream identity provider's token to the client**.

1. The proxy receives the upstream token (e.g. from GitHub).
2. It encrypts and stores the upstream token inside a secure, persistent storage backend (e.g. Redis) using **Fernet encryption**.
3. It issues a fresh, minimal **FastMCP JWT** to the client. This token is scoped exclusively to your MCP server (`aud: your-mcp-server`), preventing the client from ever accessing or exfiltrating your upstream provider credentials.

```python
# secure_github_gateway.py
import os
from fastmcp import FastMCP
from fastmcp.server.auth.providers.github import GitHubProvider
from key_value.aio.stores.redis import RedisStore
from key_value.aio.wrappers.encryption import FernetEncryptionWrapper
from cryptography.fernet import Fernet

# 1. Initialize encrypted, persistent storage for OAuth sessions and registrations.
# Never store raw secrets in plaintext or local memory on production.
encryption_wrapper = FernetEncryptionWrapper(
    key_value=RedisStore(host="redis.internal", port=6379),
    fernet=Fernet(os.environ["STORAGE_ENCRYPTION_KEY"]) # 32-byte url-safe base64 key
)

# 2. Configure the GitHub Provider.
# It acts as an OAuthProxy, managing flow redirects and issuing secure local JWTs.
auth_provider = GitHubProvider(
    client_id=os.environ["GITHUB_CLIENT_ID"],
    client_secret=os.environ["GITHUB_CLIENT_SECRET"],
    base_url="https://mcp-gateway.production.com", # Public HTTPS URL

    # Secure Token Management parameters (Mandatory for Production)
    jwt_signing_key=os.environ["JWT_SIGNING_KEY"], # Signs the issued FastMCP JWTs
    client_storage=encryption_wrapper,             # Encrypted session cache
)

# 3. Create our secure server
mcp = FastMCP("Protected-Gateway", auth=auth_provider)
```

---

## 2. Client ID Metadata Documents (CIMD)

**CIMD** (Client ID Metadata Documents) is an alternative to Dynamic Client Registration. Instead of generating client registrations on the fly, the client hosts a static JSON metadata file at a public HTTPS URL. That URL serves as the client's verified identity.

```json
// https://myapp.example.com/oauth/client.json
{
  "client_id": "https://myapp.example.com/oauth/client.json",
  "client_name": "Verified Corporate Client",
  "redirect_uris": ["http://localhost:*/callback"],
  "token_endpoint_auth_method": "private_key_jwt",
  "jwks_uri": "https://myapp.example.com/.well-known/jwks.json"
}
```

The OAuth Proxy validates this file against the hosting domain, displaying a **verified domain badge** on the user consent screen, preventing phishing and spoofing attempts.

### Private Key JWT Authentication (`private_key_jwt`)

For high-security corporate clients, CIMD supports `private_key_jwt` (defined in RFC 7523). Instead of sending a static client secret, the client signs a transient JWT assertion using its private key. The OAuth Proxy fetches the client's public keys (`jwks_uri` or inline `jwks` in the CIMD) to verify the assertion, preventing credential replay attacks via automatic JTI tracking.

---

## 3. Strict JWT Validation and Opaque Token Introspection

For servers acting as resource servers, FastMCP provides robust verifiers that can be layered via `MultiAuth`.

### Symmetric (HMAC) & Asymmetric JWT Verification (`JWTVerifier`)

```python
from fastmcp.server.auth.providers.jwt import JWTVerifier

# Asymmetric validation using JWKS (OpenID Connect public keys)
jwt_verifier = JWTVerifier(
    jwks_uri="https://auth.company.com/.well-known/jwks.json",
    issuer="https://auth.company.com",
    audience="my-mcp-resource-server",
    required_scopes=["read:reports"]
)
```

### Opaque Token Introspection (`IntrospectionTokenVerifier`)

When identity providers issue opaque (non-JWT) strings, validation requires querying the provider's token introspection endpoint (RFC 7662).

```python
from fastmcp.server.auth.providers.introspection import IntrospectionTokenVerifier

opaque_verifier = IntrospectionTokenVerifier(
    introspection_url="https://auth.company.com/oauth/introspect",
    client_id="mcp-resource-server",
    client_secret=os.environ["INTROSPECT_CLIENT_SECRET"],
    client_auth_method="client_secret_basic", # or client_secret_post
    required_scopes=["admin:write"]
)
```

---

## 4. Confused Deputy and AS-in-the-Middle Protections

In multi-tenant or shared environments, an attacker can register a malicious client redirecting to their server, then trick a victim into authorizing the shared OAuth application.

FastMCP mitigates this through:
1. **Mandatory Consent Screens**: Displays the client's name, registered redirect URIs, and requested scopes. This is shown on every authorization flow by default (`require_authorization_consent=True`).
2. **Cryptographic Browser Binding**: Upon approval, FastMCP sets a signed cookie binding the active browser session to the transaction. If an attacker intercepts the callback code, they cannot exchange it from a different browser because the session-binding cookie will be missing, raising a 403 error.

---
---

# Lecture 14: Next-Gen Utilities: Tasks, Telemetry & Versioning

To run world-class, production-grade Model Context Protocol deployments, your systems must support long-running execution without blocking, provide distributed diagnostic instrumentation, and handle seamless API version migrations. Standalone FastMCP introduces robust primitives for these next-gen patterns.

---

## 1. Protocol-Native Background Tasks (SEP-1686)

In standard MCP, all tool calls are blocking. If a task takes minutes (e.g. data exporting or code compilation), the client connection hangs or times out. The **MCP background task protocol (SEP-1686)** allows servers to execute operations asynchronously.

FastMCP implements this using **Docket** (a high-performance, enterprise-grade task scheduler designed to process millions of tasks daily with Redis).

```
                      +-------------------+
                      |     MCP Client    |
                      +---------+---------+
                                |
                   1. call_tool | (task=True)
                                v
                      +-------------------+
                      |   FastMCP Server  |
                      +---------+---------+
                                |
                 2. enqueue     | 3. returns Task ID immediately
                 (Redis/Memory) v
+------------------+  4. fetch  +-------------------+  5. status polling+------------------+
|  Docket Worker   |<-----------|  Shared Database  |<------------------|    MCP Client    |
| (process/cloud)  |            |   (Redis Queue)   |   & progress      |                  |
+------------------+            +-------------------+                   +------------------+
```

### Step 1: Define the Asynchronous Task Server

```python
# task_server.py
import asyncio
from datetime import timedelta
from fastmcp import FastMCP
from fastmcp.dependencies import Progress
from fastmcp.server.tasks import TaskConfig

# Configure FastMCP to use Redis backend for distributed task execution.
# To run locally in-memory (no persistence), use "memory://"
mcp = FastMCP("Task-Gateway")

# Configure a tool to support optional or required background execution
@mcp.tool(task=TaskConfig(mode="optional", poll_interval=timedelta(seconds=2)))
async def process_dataset(data: str, progress: Progress = Progress()) -> str:
    """Processes a heavy dataset asynchronously with progress updates."""
    # 1. Declare total work steps to the progress reporter
    total_steps = 100
    await progress.set_total(total_steps)

    for i in range(total_steps):
        # ... perform dataset chunk processing logic ...
        await asyncio.sleep(0.1)

        # 2. Update progress and messages dynamically
        await progress.set_message(f"Analyzing chunk {i+1}/{total_steps}")
        await progress.increment()

    return f"Successfully processed {total_steps} chunks."
```

### Step 2: Running Distributed Workers

In production, you can scale execution horizontally by running separate background workers using the FastMCP CLI:

```bash
# Configure the shared Docket URL to use Redis
export FASTMCP_DOCKET_URL="redis://redis.internal:6379"

# Start the main server process
fastmcp run task_server.py --transport http --port 8000 &

# Spawn multiple isolated workers to handle background task loads
fastmcp tasks worker task_server.py --concurrency 5 &
```

*Docket workers automatically pull tasks from the Redis queue, update task statuses, and handle automatic retries or timeouts.*

---

## 2. OpenTelemetry Tracing and Observability

FastMCP implements native **OpenTelemetry (OTel)** instrumentation. It automatically generates spans for every MCP request (`tools/call`, `resources/read`, `prompts/get`), tracking execution latency, database operations, and provider delegation chains.

```python
# observable_server.py
from fastmcp import FastMCP
from fastmcp.telemetry import get_tracer

mcp = FastMCP("Observable-Database")

@mcp.tool()
async def query_user_portfolio(user_id: int) -> dict:
    """Retrieves and compiles a user's portfolio."""
    # Access the FastMCP tracer to record sub-operation spans
    tracer = get_tracer()

    # 1. Record database query span
    with tracer.start_as_current_span("db.fetch_assets") as span:
        span.set_attribute("db.user_id", user_id)
        # ... perform query ...
        assets = [{"symbol": "AAPL", "qty": 10}, {"symbol": "MSFT", "qty": 5}]
        span.set_attribute("db.results_count", len(assets))

    # 2. Record API pricing fetch span
    with tracer.start_as_current_span("api.fetch_pricing") as span:
        # ... query market pricing ...
        pass

    return {"user_id": user_id, "portfolio": assets}
```

Run with the standard OpenTelemetry instrument wrapper to export traces directly to your APM backend (e.g. Jaeger, Datadog, or Honeycomb):

```bash
export OTEL_SERVICE_NAME="mcp-observable-db"
export OTEL_EXPORTER_OTLP_ENDPOINT="http://jaeger.internal:4317"

opentelemetry-instrument fastmcp run observable_server.py
```

---

## 3. Component Versioning and Routing

When upgrading tool schemas or resource formats, you must support legacy clients while letting new clients access enhanced capabilities. FastMCP's **VersionFilter** transform allows you to serve multiple API versions from a single codebase.

```python
# versioned_api.py
from fastmcp import FastMCP
from fastmcp.server.providers import LocalProvider
from fastmcp.server.transforms import VersionFilter

# 1. Define versioned components on a shared LocalProvider
components = LocalProvider()

@components.tool(version="1.0")
def fetch_user_data(user_id: int) -> dict:
    """Legacy v1.0 fetch (returns limited fields)."""
    return {"id": user_id, "name": "Alice"}

@components.tool(version="2.0")
def fetch_user_data(user_id: int, include_billing: bool = False) -> dict:
    """Modern v2.0 fetch (supports optional billing details)."""
    return {"id": user_id, "name": "Alice", "billing_active": include_billing}

# 2. Expose distinct versioned API gateways using VersionFilter transforms
# v1.0 Gateway: Exposes only components with versions < 2.0
mcp_v1 = FastMCP("API-v1", providers=[components])
mcp_v1.add_transform(VersionFilter(version_lt="2.0"))

# v2.0 Gateway: Exposes only components with versions >= 2.0
mcp_v2 = FastMCP("API-v2", providers=[components])
mcp_v2.add_transform(VersionFilter(version_gte="2.0"))
```

*Version matching supports semantic PEP 440 formatting (e.g., `"1.0a1" < "1.0b1" < "1.0"`) and falls back to lexicographic string comparison for non-standard schemes like ISO dates.*

---
*End of Masterclass. Keep building safe and powerful servers!*
