"""
Weather API client for WeatherAPI.com
"""
import os
import requests
from typing import Dict, Any
from utils.date_utils import parse_target_date


class WeatherAPIClient:
    """Client for WeatherAPI.com service"""
    
    def __init__(self):
        # Try Streamlit secrets first, then environment variables
        try:
            import streamlit as st
            self.api_key = st.secrets.get("WEATHERAPI_KEY") or os.getenv("WEATHERAPI_KEY")
        except (ImportError, AttributeError):
            self.api_key = os.getenv("WEATHERAPI_KEY")
        self.base_url = "http://api.weatherapi.com/v1"
    
    async def get_forecast(self, location: str, forecast_days: int = 7, target_date: str = None, include_hourly: bool = True) -> Dict[str, Any]:
        """Get weather forecast from WeatherAPI.com"""
        if not self.api_key:
            return {"success": False, "error": "Weather API key not configured"}
        
        try:
            # Parse target date if provided
            date_info = parse_target_date(target_date) if target_date else None
            
            # Get weather data
            response = requests.get(
                f"{self.base_url}/forecast.json",
                params={
                    "key": self.api_key,
                    "q": location,
                    "days": min(forecast_days, 10),
                    "aqi": "no",
                    "alerts": "no"
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # Format forecast data
            forecast = []
            for day in data["forecast"]["forecastday"]:
                day_data = {
                    "date": day["date"],
                    "day_summary": {
                        "condition": day["day"]["condition"]["text"],
                        "max_temp_c": day["day"]["maxtemp_c"],
                        "min_temp_c": day["day"]["mintemp_c"],
                        "chance_of_rain": day["day"]["daily_chance_of_rain"],
                        "humidity": day["day"]["avghumidity"],
                        "uv_index": day["day"]["uv"]
                    }
                }
                
                if include_hourly and "hour" in day:
                    day_data["hourly"] = [
                        {
                            "time": hour["time"],
                            "temp_c": hour["temp_c"],
                            "condition": hour["condition"]["text"],
                            "chance_of_rain": hour["chance_of_rain"]
                        }
                        for hour in day["hour"]
                    ]
                
                forecast.append(day_data)
            
            return {
                "success": True,
                "location": {
                    "name": data["location"]["name"],
                    "country": data["location"]["country"],
                    "region": data["location"]["region"]
                },
                "current": {
                    "temp_c": data["current"]["temp_c"],
                    "condition": data["current"]["condition"]["text"],
                    "humidity": data["current"]["humidity"],
                    "last_updated": data["current"]["last_updated"]
                },
                "forecast": forecast,
                "target_date": {
                    "requested": target_date or "tomorrow",
                    "resolved": date_info["date"].strftime("%Y-%m-%d") if date_info else None,
                    "description": date_info["description"] if date_info else "tomorrow"
                } if date_info else None
            }
            
        except Exception as e:
            return {"success": False, "error": f"Weather API error: {str(e)}"}