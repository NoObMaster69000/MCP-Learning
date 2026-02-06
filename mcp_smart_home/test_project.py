import asyncio
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_smart_home():
    server_path = os.path.abspath("mcp_smart_home/server.py")

    server_params = StdioServerParameters(
        command="python3",
        args=[server_path],
    )

    print("--- Starting Smart Home Project Test ---")

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("[✓] Connection Initialized")

            # 1. Test Listing Tools
            tools = await session.list_tools()
            tool_names = [t.name for t in tools.tools]
            print(f"[✓] Tools Found: {tool_names}")
            assert "set_light" in tool_names
            assert "set_thermostat" in tool_names

            # 2. Test Resource Reading
            print("Reading home status...")
            status = await session.read_resource("home://status")
            print(f"[✓] Status Content:\n{status.contents[0].text}")

            # 3. Test Tool Calling
            print("Turning on kitchen lights...")
            result = await session.call_tool("set_light", arguments={"room": "kitchen", "power": True})
            print(f"[✓] Tool Result: {result.content[0].text}")

            # 4. Verify status change
            print("Verifying status change...")
            updated_status = await session.read_resource("home://status")
            assert "kitchen" in updated_status.contents[0].text.lower()
            print("[✓] Status updated successfully")

    print("\n--- All Tests Passed! ---")

if __name__ == "__main__":
    asyncio.run(test_smart_home())
