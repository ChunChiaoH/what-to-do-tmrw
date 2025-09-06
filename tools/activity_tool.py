"""
Activity API MCP Tool
"""
import json
from typing import List
from mcp.types import TextContent
from api_clients.foursquare_client import FoursquareClient


async def activity_api_tool(arguments: dict) -> List[TextContent]:
    """Activity API MCP Tool - Gets activity recommendations from Foursquare API"""
    location = arguments.get("location", "")
    weather_condition = arguments.get("weather_condition", "").lower()
    activity_type = arguments.get("activity_type", "both")
    category = arguments.get("category")
    
    try:
        # Auto-determine activity type from weather
        resolved_type = activity_type
        if activity_type == "both":
            bad_weather = ["rain", "storm", "snow", "drizzle", "shower"]
            good_weather = ["sunny", "clear", "fair"]
            if any(word in weather_condition for word in bad_weather):
                resolved_type = "indoor"
            elif any(word in weather_condition for word in good_weather):
                resolved_type = "outdoor"
        
        # Get activities from Foursquare
        client = FoursquareClient()
        activities = []
        
        if resolved_type in ["indoor", "outdoor"]:
            activities = await client.search_places(location, resolved_type, category, variety=True)
        elif resolved_type == "both":
            indoor = await client.search_places(location, "indoor", category, variety=True)
            outdoor = await client.search_places(location, "outdoor", category, variety=True)
            activities = indoor[:4] + outdoor[:4]
        
        if not activities:
            print("No activities found from Foursquare API")
        
        return [TextContent(type="text", text=json.dumps({
            "success": True,
            "location": location,
            "query_parameters": {
                "weather_condition": weather_condition,
                "requested_activity_type": activity_type,
                "resolved_activity_type": resolved_type,
                "category_filter": category
            },
            "activities": activities[:8],
            "total_results": len(activities[:8]),
            "data_source": "foursquare" if activities else "none"
        }, indent=2))]
        
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({
            "success": False, 
            "error": f"Activity API error: {str(e)}"
        }))]