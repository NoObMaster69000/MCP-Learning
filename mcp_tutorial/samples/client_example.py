import asyncio
import os
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    """
    A simple MCP client that connects to the sample_server.py via stdio.
    """
    # Path to the sample server
    # We assume this script is run from the project root or the tutorial folder
    server_script = os.path.join(os.path.dirname(__file__), "..", "sample_server.py")
    server_script = os.path.abspath(server_script)

    if not os.path.exists(server_script):
        print(f"Error: Could not find server script at {server_script}")
        return

    # Define the server parameters
    server_params = StdioServerParameters(
        command="python3",
        args=[server_script],
        env=os.environ.copy()
    )

    print(f"Connecting to server at {server_script}...")

    try:
        # Establish the stdio connection
        async with stdio_client(server_params) as (read, write):
            # Create a session
            async with ClientSession(read, write) as session:
                # 1. Initialize the connection
                await session.initialize()
                print("Connection initialized successfully!")

                # 2. List available tools
                print("\n--- Listing Tools ---")
                tools_result = await session.list_tools()
                for tool in tools_result.tools:
                    print(f"- {tool.name}: {tool.description}")

                # 3. List available resources
                print("\n--- Listing Resources ---")
                resources_result = await session.list_resources()
                for resource in resources_result.resources:
                    print(f"- {resource.uri}: {resource.name}")

                # 4. Call a tool
                if any(t.name == "list_notes" for t in tools_result.tools):
                    print("\n--- Calling tool: list_notes ---")
                    result = await session.call_tool("list_notes", arguments={})
                    # result is a list of content blocks
                    for content in result.content:
                        if content.type == 'text':
                            print(f"Result: {content.text}")

                # 5. Read a resource
                print("\n--- Reading resource: notes://index ---")
                resource_content = await session.read_resource("notes://index")
                for content in resource_content.contents:
                    print(f"Content: {content.text}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
