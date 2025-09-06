"""
Weather API MCP Tool
"""
import json
from typing import List
from mcp.types import TextContent
from api_clients.weather_client import WeatherAPIClient


async def weather_api_tool(arguments: dict) -> List[TextContent]:
    """Weather API MCP Tool - Gets weather data from WeatherAPI.com"""
    location = arguments.get("location")
    forecast_days = arguments.get("forecast_days", 7)  # Default to 7 days to cover future dates
    target_date = arguments.get("target_date")
    include_hourly = arguments.get("include_hourly", True)
    
    if not location:
        return [TextContent(type="text", text=json.dumps({"error": "Location is required"}))]
    
    # Use weather client to get forecast
    client = WeatherAPIClient()
    result = await client.get_forecast(location, forecast_days, target_date, include_hourly)
    
    return [TextContent(type="text", text=json.dumps(result, indent=2))]