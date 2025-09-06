"""
What To Do Tomorrow MCP Server
Clean, modular MCP server following 2025 best practices
"""
import asyncio
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    TextContent,
    Tool,
)

# Import tools
from tools.weather_tool import weather_api_tool
from tools.activity_tool import activity_api_tool

# Initialize the server
server = Server("what-to-do-server")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available MCP tools"""
    return [
        Tool(
            name="weather_api",
            description="Get weather forecast data for any location with flexible date support",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "Location (city, address, etc.)"},
                    "forecast_days": {"type": "integer", "description": "Number of forecast days (1-10)", "default": 7},
                    "target_date": {"type": "string", "description": "Target date (today, tomorrow, weekend, next monday, YYYY-MM-DD)", "default": "tomorrow"},
                    "include_hourly": {"type": "boolean", "description": "Include hourly forecast data", "default": True}
                },
                "required": ["location"]
            }
        ),
        Tool(
            name="activity_api",
            description="Get activity recommendations based on location and preferences",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "Location (city, address, etc.)"},
                    "weather_condition": {"type": "string", "description": "Current weather condition to inform recommendations"},
                    "activity_type": {"type": "string", "enum": ["indoor", "outdoor", "both"], "description": "Type of activities", "default": "both"},
                    "category": {"type": "string", "description": "Specific category filter (culture, shopping, entertainment, fitness, etc.)"}
                },
                "required": ["location"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[TextContent]:
    """Handle MCP tool calls"""
    if arguments is None:
        arguments = {}
        
    if name == "weather_api":
        return await weather_api_tool(arguments)
    elif name == "activity_api":
        return await activity_api_tool(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """Run the MCP server"""
    # Run the server using stdio
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="what-to-do-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())