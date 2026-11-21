from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    ListToolsResult,
    TextContent,
    Tool,
)


async def main() -> None:
    """Start a local MCP server for integration testing."""

    async def list_tools(
        context: object,
        params: object,
    ) -> ListToolsResult:
        return ListToolsResult(
            tools=[
                Tool(
                    name="read_message",
                    description="Return a test message.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"},
                        },
                        "required": ["message"],
                    },
                ),
                Tool(
                    name="write_message",
                    description="A write operation used to test authorization.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"},
                        },
                        "required": ["message"],
                    },
                ),
            ]
        )

    async def call_tool(
        context: object,
        params: object,
    ) -> CallToolResult:
        name = params.name
        arguments = params.arguments or {}

        if name == "read_message":
            message = arguments.get("message", "")

            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Read successfully: {message}",
                    )
                ],
                isError=False,
            )

        if name == "write_message":
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Write operation executed.",
                    )
                ],
                isError=False,
            )

        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text="Unknown tool.",
                )
            ],
            isError=True,
        )

    server = Server(
        "aegis-test-server",
        on_list_tools=list_tools,
        on_call_tool=call_tool,
    )

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
