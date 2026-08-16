import asyncio
from fastmcp import Client


async def main():
    async with Client("agentic/tools/cultpass_mcp_server.py") as client:
        tools = await client.list_tools()
        print("Tools disponibles:", [t.name for t in tools])

        result = await client.call_tool(
            "get_subscription_status",
            {"user_id": "a4ab87"},  # Alice
        )
        print("Resultado:", result.data)


asyncio.run(main())
