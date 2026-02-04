from fastmcp import FastMCP
import uvicorn

# Create a FastMCP server
mcp = FastMCP("RemoteServer")

@mcp.tool()
def get_weather(city: str) -> str:
    """Returns the weather for a given city."""
    return f"The weather in {city} is sunny, 25°C."

if __name__ == "__main__":
    # Running FastMCP as an SSE server
    # This requires 'starlette' and 'uvicorn' which are installed with fastmcp
    print("Starting MCP SSE server on http://localhost:8000")
    print("Clients can connect to http://localhost:8000/sse")

    # FastMCP can be converted to a Starlette app
    # In recent versions of FastMCP, you can just use .run(transport="sse")
    # or run the http app directly.
    mcp.run(transport="sse", host="0.0.0.0", port=8000)
