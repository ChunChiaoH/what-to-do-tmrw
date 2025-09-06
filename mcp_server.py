"""
What To Do Tomorrow MCP Server
Provides two MCP tools: weather API (weatherapi.com) and activity API
"""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional
import requests
from dotenv import load_dotenv
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    TextContent,
    Tool,
)

load_dotenv()

# Initialize the server
server = Server("what-to-do-server")

# Weather API configuration for weatherapi.com
WEATHER_API_KEY = os.getenv("WEATHERAPI_KEY")
WEATHER_BASE_URL = "http://api.weatherapi.com/v1"

# Foursquare Places API configuration
FOURSQUARE_API_KEY = os.getenv("FOURSQUARE_API_KEY")
FOURSQUARE_BASE_URL = "https://places-api.foursquare.com"

# Foursquare category mappings
FOURSQUARE_CATEGORIES = {
    "indoor": {
        "culture": ["10000", "10027", "10028", "10029"],
        "shopping": ["17000", "17001", "17069"],
        "entertainment": ["10000", "10032", "10041"],
        "fitness": ["18000", "18021", "18001"],
        "learning": ["12000", "12062"],
        "relaxation": ["18058", "12000"]
    },
    "outdoor": {
        "nature": ["16000", "16032", "16014"],
        "water": ["16048", "16025"],
        "adventure": ["16000", "16034"],
        "sightseeing": ["15000", "15014"],
        "fitness": ["18000", "18042"]
    }
}



@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List the two available MCP tools"""
    return [
        Tool(
            name="weather_api",
            description="Get weather information for any location using WeatherAPI.com",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name (e.g., 'Brisbane', 'Sydney', 'Melbourne')"
                    },
                    "forecast_days": {
                        "type": "integer",
                        "description": "Number of forecast days to retrieve (1-10, default: 3)",
                        "default": 3
                    },
                    "target_date": {
                        "type": "string", 
                        "description": "Target date for weather (e.g., 'today', 'tomorrow', 'this weekend', or specific date like '2025-09-07')"
                    },
                    "include_hourly": {
                        "type": "boolean",
                        "description": "Include hourly forecast (default: true)",
                        "default": True
                    }
                },
                "required": ["location"]
            }
        ),
        Tool(
            name="activity_api",
            description="Get activity recommendations based on conditions and preferences",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name for location-specific activities"
                    },
                    "weather_condition": {
                        "type": "string",
                        "description": "Current weather condition (sunny, rainy, cloudy, etc.)"
                    },
                    "activity_type": {
                        "type": "string",
                        "description": "Preferred activity type",
                        "enum": ["indoor", "outdoor", "both"]
                    },
                    "category": {
                        "type": "string",
                        "description": "Activity category filter (optional)",
                        "enum": ["culture", "shopping", "entertainment", "fitness", "learning", "relaxation", "nature", "water", "adventure", "sightseeing"]
                    }
                },
                "required": ["location"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[TextContent]:
    """Handle tool calls for weather_api and activity_api"""
    
    if name == "weather_api":
        return await weather_api_tool(arguments)
    elif name == "activity_api":
        return await activity_api_tool(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


def parse_target_date(target_date: str) -> Dict[str, Any]:
    """Parse target date string and return date info"""
    from datetime import datetime, timedelta
    
    today = datetime.now().date()
    result = {"date": None, "description": target_date or "tomorrow"}
    
    if not target_date or target_date.lower() in ["tomorrow", "tmrw"]:
        result["date"] = today + timedelta(days=1)
    elif target_date.lower() == "today":
        result["date"] = today
    elif target_date.lower() in ["this weekend", "weekend"]:
        # Find next Saturday
        days_until_saturday = (5 - today.weekday()) % 7
        if days_until_saturday == 0 and today.weekday() == 5:  # It's Saturday
            result["date"] = today
        else:
            result["date"] = today + timedelta(days=days_until_saturday if days_until_saturday > 0 else 6)
    elif target_date.lower() in ["next week", "next monday"]:
        days_until_monday = (7 - today.weekday()) % 7
        result["date"] = today + timedelta(days=days_until_monday if days_until_monday > 0 else 7)
    else:
        # Try to parse as date string (YYYY-MM-DD format)
        try:
            result["date"] = datetime.strptime(target_date, "%Y-%m-%d").date()
        except ValueError:
            # Default to tomorrow if parsing fails
            result["date"] = today + timedelta(days=1)
            result["description"] = "tomorrow (default)"
    
    return result


async def weather_api_tool(arguments: dict) -> list[TextContent]:
    """Weather API MCP Tool - Gets weather data from WeatherAPI.com"""
    location = arguments.get("location")
    forecast_days = arguments.get("forecast_days", 3)
    target_date = arguments.get("target_date")
    include_hourly = arguments.get("include_hourly", True)
    
    if not location:
        return [TextContent(type="text", text=json.dumps({"error": "Location is required"}))]
    if not WEATHER_API_KEY:
        return [TextContent(type="text", text=json.dumps({"error": "Weather API key not configured"}))]
    
    try:
        # Parse target date
        date_info = parse_target_date(target_date)
        target_date_obj = date_info["date"]
        
        # Get weather data
        response = requests.get(
            f"{WEATHER_BASE_URL}/forecast.json",
            params={
                "key": WEATHER_API_KEY,
                "q": location,
                "days": min(forecast_days, 10),
                "aqi": "no",
                "alerts": "no"
            }
        )
        response.raise_for_status()
        data = response.json()
        
        # Format the weather API response
        weather_result = {
            "success": True,
            "location": {
                "name": data["location"]["name"],
                "region": data["location"]["region"],
                "country": data["location"]["country"],
                "coordinates": {
                    "lat": data["location"]["lat"],
                    "lon": data["location"]["lon"]
                },
                "timezone": data["location"]["tz_id"],
                "local_time": data["location"]["localtime"]
            },
            "target_date": {
                "requested": target_date or "tomorrow",
                "resolved": target_date_obj.isoformat(),
                "description": date_info["description"]
            },
            "current_weather": {
                "temperature_c": data["current"]["temp_c"],
                "temperature_f": data["current"]["temp_f"],
                "feels_like_c": data["current"]["feelslike_c"],
                "feels_like_f": data["current"]["feelslike_f"],
                "condition": data["current"]["condition"]["text"],
                "humidity": data["current"]["humidity"],
                "wind_kph": data["current"]["wind_kph"],
                "wind_mph": data["current"]["wind_mph"],
                "wind_direction": data["current"]["wind_dir"],
                "pressure_mb": data["current"]["pressure_mb"],
                "visibility_km": data["current"]["vis_km"],
                "uv_index": data["current"]["uv"],
                "is_day": data["current"]["is_day"] == 1
            },
            "forecast": []
        }
        
        # Add forecast data
        for forecast_day in data["forecast"]["forecastday"]:
            day_data = {
                "date": forecast_day["date"],
                "day_summary": {
                    "max_temp_c": forecast_day["day"]["maxtemp_c"],
                    "min_temp_c": forecast_day["day"]["mintemp_c"],
                    "avg_temp_c": forecast_day["day"]["avgtemp_c"],
                    "condition": forecast_day["day"]["condition"]["text"],
                    "chance_of_rain": forecast_day["day"]["daily_chance_of_rain"],
                    "chance_of_snow": forecast_day["day"]["daily_chance_of_snow"],
                    "max_wind_kph": forecast_day["day"]["maxwind_kph"],
                    "avg_humidity": forecast_day["day"]["avghumidity"],
                    "uv_index": forecast_day["day"]["uv"]
                }
            }
            
            # Add hourly data if requested
            if include_hourly and "hour" in forecast_day:
                day_data["hourly"] = []
                for hour_data in forecast_day["hour"]:
                    day_data["hourly"].append({
                        "time": hour_data["time"],
                        "temp_c": hour_data["temp_c"],
                        "condition": hour_data["condition"]["text"],
                        "chance_of_rain": hour_data["chance_of_rain"],
                        "wind_kph": hour_data["wind_kph"],
                        "humidity": hour_data["humidity"],
                        "is_day": hour_data["is_day"] == 1
                    })
            
            weather_result["forecast"].append(day_data)
        
        return [TextContent(type="text", text=json.dumps(weather_result, indent=2))]
        
    except requests.RequestException as e:
        error_result = {"success": False, "error": f"Weather API request failed: {str(e)}"}
        return [TextContent(type="text", text=json.dumps(error_result))]
    except Exception as e:
        error_result = {"success": False, "error": f"Unexpected error: {str(e)}"}
        return [TextContent(type="text", text=json.dumps(error_result))]


async def get_foursquare_places(location: str, activity_type: str, category: str = None) -> List[Dict]:
    """Get places from Foursquare API"""
    if not FOURSQUARE_API_KEY:
        return []
    
    try:
        # Get category IDs to search for
        type_categories = FOURSQUARE_CATEGORIES.get(activity_type, {})
        if category and category in type_categories:
            categories = type_categories[category]
        else:
            categories = [cat for cat_list in type_categories.values() for cat in cat_list]
        
        if not categories:
            return []
        
        # Call Foursquare API
        response = requests.get(
            f"{FOURSQUARE_BASE_URL}/places/search",
            headers={
                "Authorization": f"Bearer {FOURSQUARE_API_KEY}",
                "accept": "application/json",
                "X-Places-Api-Version": "2025-06-17"
            },
            params={
                "near": location,
                "categories": ",".join(categories[:5]),
                "limit": 10
            }
        )
        response.raise_for_status()
        data = response.json()
        
        # Format results
        return [{
            "name": result["name"],
            "category": category or "general",
            "description": result.get("location", {}).get("formatted_address", ""),
            "rating": result.get("rating", 0) / 10.0 if result.get("rating") else None,
            "source": "foursquare"
        } for result in data.get("results", [])][:8]
        
    except Exception as e:
        print(f"Foursquare API error: {e}")
        return []


async def activity_api_tool(arguments: dict) -> list[TextContent]:
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
        activities = []
        if resolved_type in ["indoor", "outdoor"]:
            activities = await get_foursquare_places(location, resolved_type, category)
        elif resolved_type == "both":
            indoor = await get_foursquare_places(location, "indoor", category)
            outdoor = await get_foursquare_places(location, "outdoor", category)
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


async def main():
    """Run the MCP server"""
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