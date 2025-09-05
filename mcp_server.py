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

# Category mappings for Foursquare API
FOURSQUARE_CATEGORIES = {
    "indoor": {
        "culture": ["10000", "10027", "10028", "10029"],  # Arts & Entertainment, Museums, Galleries, Libraries
        "shopping": ["17000", "17001", "17069"],  # Retail, Shopping Malls, Markets
        "entertainment": ["10000", "10032", "10041"],  # Entertainment, Movie Theaters, Gaming
        "fitness": ["18000", "18021", "18001"],  # Sports & Recreation, Gyms, Fitness
        "learning": ["12000", "12062"],  # Education, Classes
        "relaxation": ["18058", "12000"]  # Spas, Wellness
    },
    "outdoor": {
        "nature": ["16000", "16032", "16014"],  # Outdoors & Recreation, Parks, Gardens  
        "water": ["16048", "16025"],  # Beaches, Water Sports
        "adventure": ["16000", "16034"],  # Outdoors, Hiking
        "sightseeing": ["15000", "15014"],  # Travel & Transport, Scenic Points
        "fitness": ["18000", "18042"]  # Sports, Outdoor Sports
    }
}

# Fallback activity data for when API is unavailable
FALLBACK_ACTIVITIES = {
    "indoor": [
        {"name": "Visit Museums", "category": "culture", "description": "Explore local museums and galleries"},
        {"name": "Shopping Malls", "category": "shopping", "description": "Browse shopping centers and markets"},
        {"name": "Movie Theaters", "category": "entertainment", "description": "Watch latest movies in cinemas"},
        {"name": "Indoor Climbing", "category": "fitness", "description": "Try rock climbing gyms"},
        {"name": "Escape Rooms", "category": "entertainment", "description": "Solve puzzles with friends"},
        {"name": "Cooking Classes", "category": "learning", "description": "Learn new culinary skills"},
        {"name": "Art Galleries", "category": "culture", "description": "Appreciate local and international art"},
        {"name": "Libraries & Bookstores", "category": "learning", "description": "Read and discover new books"},
        {"name": "Spa & Wellness", "category": "relaxation", "description": "Relax and rejuvenate"},
        {"name": "Indoor Sports", "category": "fitness", "description": "Bowling, pool, arcade games"}
    ],
    "outdoor": [
        {"name": "Parks & Gardens", "category": "nature", "description": "Enjoy green spaces and botanical gardens"},
        {"name": "Beach Activities", "category": "water", "description": "Swimming, surfing, beach volleyball"},
        {"name": "Hiking Trails", "category": "adventure", "description": "Explore nature trails and scenic walks"},
        {"name": "Outdoor Markets", "category": "shopping", "description": "Browse farmers markets and street vendors"},
        {"name": "Picnic Spots", "category": "relaxation", "description": "Enjoy meals in scenic outdoor locations"},
        {"name": "Cycling Routes", "category": "fitness", "description": "Bike through city paths and trails"},
        {"name": "Outdoor Sports", "category": "fitness", "description": "Tennis, golf, football in parks"},
        {"name": "River Activities", "category": "water", "description": "Kayaking, river cruises, fishing"},
        {"name": "Scenic Viewpoints", "category": "sightseeing", "description": "Visit lookouts and observation decks"},
        {"name": "Outdoor Festivals", "category": "entertainment", "description": "Attend local events and festivals"}
    ]
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
    import re
    
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
    """Weather API MCP Tool - Gets weather data from WeatherAPI.com with flexible date support"""
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
        
        # WeatherAPI.com endpoint for current weather + forecast
        url = f"{WEATHER_BASE_URL}/forecast.json"
        params = {
            "key": WEATHER_API_KEY,
            "q": location,
            "days": min(forecast_days, 10),  # WeatherAPI.com supports up to 10 days
            "aqi": "no",  # We don't need air quality data
            "alerts": "no"  # We don't need weather alerts
        }
        
        response = requests.get(url, params=params)
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
        # Determine categories to search for
        categories = []
        if category and activity_type in FOURSQUARE_CATEGORIES:
            if category in FOURSQUARE_CATEGORIES[activity_type]:
                categories = FOURSQUARE_CATEGORIES[activity_type][category]
        else:
            # Get all categories for the activity type
            if activity_type in FOURSQUARE_CATEGORIES:
                for cat_list in FOURSQUARE_CATEGORIES[activity_type].values():
                    categories.extend(cat_list)
        
        if not categories:
            return []
        
        # Search places using Foursquare Places API
        url = f"{FOURSQUARE_BASE_URL}/places/search"
        headers = {
            "Authorization": f"Bearer {FOURSQUARE_API_KEY}",
            "accept": "application/json",
            "X-Places-Api-Version": "2025-06-17"
        }
        params = {
            "near": location,  # Use "near" parameter for location
            "categories": ",".join(categories[:5]),  # Limit categories  
            "limit": 10
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Format results
        places = []
        for result in data.get("results", []):
            place = {
                "name": result["name"],
                "category": category or "general",
                "description": result.get("location", {}).get("formatted_address", ""),
                "rating": result.get("rating", 0) / 10.0 if result.get("rating") else None,  # Convert to 0-1 scale
                "source": "foursquare"
            }
            places.append(place)
        
        return places[:8]  # Limit to 8 results
        
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
        # Determine activity type based on weather if "both" is specified
        resolved_activity_type = activity_type
        if activity_type == "both":
            if any(word in weather_condition for word in ["rain", "storm", "snow", "drizzle", "shower"]):
                resolved_activity_type = "indoor"
            elif any(word in weather_condition for word in ["sunny", "clear", "fair"]):
                resolved_activity_type = "outdoor"
        
        recommended_activities = []
        
        # Try to get real data from Foursquare API
        if resolved_activity_type in ["indoor", "outdoor"]:
            foursquare_places = await get_foursquare_places(location, resolved_activity_type, category)
            recommended_activities.extend(foursquare_places)
        elif resolved_activity_type == "both":
            # Get both indoor and outdoor activities
            indoor_places = await get_foursquare_places(location, "indoor", category)
            outdoor_places = await get_foursquare_places(location, "outdoor", category)
            recommended_activities.extend(indoor_places[:4])
            recommended_activities.extend(outdoor_places[:4])
        
        # Fallback to static data if API fails or no results
        if not recommended_activities:
            print("Using fallback activity data")
            if resolved_activity_type == "both":
                recommended_activities.extend(FALLBACK_ACTIVITIES["indoor"][:3])
                recommended_activities.extend(FALLBACK_ACTIVITIES["outdoor"][:3])
            elif resolved_activity_type in FALLBACK_ACTIVITIES:
                recommended_activities = FALLBACK_ACTIVITIES[resolved_activity_type][:8]
            
            # Filter by category if specified
            if category and recommended_activities:
                recommended_activities = [act for act in recommended_activities if act["category"] == category]
        
        # Format the activity API response
        activity_result = {
            "success": True,
            "location": location,
            "query_parameters": {
                "weather_condition": weather_condition,
                "requested_activity_type": arguments.get("activity_type", "both"),
                "resolved_activity_type": resolved_activity_type,
                "category_filter": category
            },
            "activities": recommended_activities[:8],  # Limit to 8 results
            "total_results": len(recommended_activities[:8]),
            "data_source": "foursquare" if any(act.get("source") == "foursquare" for act in recommended_activities) else "fallback"
        }
        
        return [TextContent(type="text", text=json.dumps(activity_result, indent=2))]
        
    except Exception as e:
        error_result = {"success": False, "error": f"Activity API error: {str(e)}"}
        return [TextContent(type="text", text=json.dumps(error_result))]


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