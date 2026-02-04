import asyncio
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server.stdio import stdio_server

# Create a low-level server instance
server = Server("low-level-demo")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools.
    In the low-level SDK, you manually return a list of Tool objects.
    """
    return [
        types.Tool(
            name="echo",
            description="Echoes back the input string",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string"}
                },
                "required": ["message"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str,
    arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResouce]:
    """
    Handle tool execution.
    In the low-level SDK, you manually route requests based on the tool name.
    """
    if name == "echo":
        message = arguments.get("message", "")
        return [types.TextContent(type="text", text=f"Echo: {message}")]

    raise ValueError(f"Unknown tool: {name}")

async def main():
    # Run the server using stdio transport
    async with stdio_server() as (read, write):
        await server.run(
            read,
            write,
            InitializationOptions(
                server_name="low-level-demo",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    # To run this, usually a client launches it.
    # For testing, you can use: npx @modelcontextprotocol/inspector python low_level_server.py
    asyncio.run(main())
