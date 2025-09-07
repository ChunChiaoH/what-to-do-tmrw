"""
Data extraction utilities for processing API responses
Extracts and transforms data from weather and activity API responses
"""
from typing import Dict, List, Any, Optional


class WeatherDataExtractor:
    """Extract and format weather data for different use cases"""
    
    @staticmethod
    def extract_for_decision_making(weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract weather data summary for LLM decision making"""
        if not weather_data.get("success"):
            return {"error": weather_data.get("error")}
        
        forecast = weather_data.get("forecast", [])
        if not forecast:
            return {"error": "no_forecast"}
        
        return {
            "location": weather_data["location"]["name"],
            "current_condition": weather_data["current"]["condition"],
            "tomorrow_forecast": forecast[0]["day_summary"]["condition"]
        }
    
    @staticmethod
    def extract_for_response_generation(weather_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract weather data for final response generation"""
        if not weather_data.get("success"):
            return None
        
        forecast = weather_data.get("forecast", [])
        target_date_info = weather_data.get("target_date", {})
        
        if not forecast:
            return None
        
        # Find the correct forecast day based on target date
        target_day_forecast = forecast[0]  # Default to first day
        target_date_str = target_date_info.get("resolved")
        
        if target_date_str:
            # Look for matching date in forecast
            for day_forecast in forecast:
                if day_forecast["date"] == target_date_str:
                    target_day_forecast = day_forecast
                    break
        
        return {
            "location": weather_data["location"]["name"],
            "target_date": target_date_info.get("requested", "unknown"),
            "condition": target_day_forecast["day_summary"]["condition"],
            "temp_range": f"{target_day_forecast['day_summary']['min_temp_c']}°C - {target_day_forecast['day_summary']['max_temp_c']}°C",
            "rain_chance": target_day_forecast["day_summary"]["chance_of_rain"],
            "date_found": target_day_forecast["date"] == target_date_str if target_date_str else True
        }


class ActivityDataExtractor:
    """Extract and format activity data for different use cases"""
    
    @staticmethod
    def extract_for_decision_making(activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract activity data summary for LLM decision making"""
        if not activity_data.get("success"):
            return {"error": activity_data.get("error")}
        
        return {
            "count": activity_data["total_results"],
            "type": activity_data["query_parameters"]["resolved_activity_type"],
            "data_source": activity_data.get("data_source", "unknown"),
            "activities": activity_data.get("activities", [])
        }
    
    @staticmethod
    def extract_unique_activities_for_response(activity_data_list: List[Dict[str, Any]], limit: int = 8) -> List[Dict[str, Any]]:
        """Extract unique activities from multiple API calls for response generation"""
        if not activity_data_list:
            return []
        
        all_activities = []
        for activity_data in activity_data_list:
            if activity_data.get("success"):
                all_activities.extend(activity_data["activities"])
        
        # Deduplicate by name
        seen_names = set()
        unique_activities = []
        for activity in all_activities:
            if activity["name"] not in seen_names:
                unique_activities.append({
                    "name": activity["name"],
                    "category": activity["category"],
                    "description": activity["description"]
                })
                seen_names.add(activity["name"])
        
        return unique_activities[:limit]


class ErrorExtractor:
    """Extract and format error information from API responses"""
    
    @staticmethod
    def extract_errors_from_context(context: Dict[str, Any]) -> List[str]:
        """Extract all errors from context for response generation"""
        errors = []
        
        # Weather errors
        if "weather_data" in context and not context["weather_data"].get("success"):
            errors.append(f"Weather data unavailable: {context['weather_data'].get('error')}")
        
        # Activity errors
        if "activity_data" in context and not context["activity_data"].get("success"):
            errors.append(f"Activity data unavailable: {context['activity_data'].get('error')}")
        
        return errors


class ContextDataExtractor:
    """High-level data extraction for different context stages"""
    
    @staticmethod
    def extract_for_decision_context(context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data for LLM decision making context"""
        context_summary = {
            "original_query": context["query"],
            "extracted_info": context.get("query_analysis", {}),
            "tools_used": context.get("tools_called", []),
            "data_collected": {}
        }
        
        # Add weather data if available
        if "weather_data" in context:
            weather_summary = WeatherDataExtractor.extract_for_decision_making(context["weather_data"])
            context_summary["data_collected"]["weather"] = weather_summary
        
        # Add activity data if available
        if "activity_data" in context:
            activity_summary = ActivityDataExtractor.extract_for_decision_making(context["activity_data"])
            context_summary["data_collected"]["activities"] = activity_summary
        
        return context_summary
    
    @staticmethod
    def extract_for_response_context(context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data for final response generation context"""
        response_context = {
            "original_query": context.get("query"),
            "user_preferences": context.get("query_analysis", {}),
            "weather_data": None,
            "activities": [],
            "errors": []
        }
        
        # Add weather data if available
        if "weather_data" in context:
            weather_data = WeatherDataExtractor.extract_for_response_generation(context["weather_data"])
            response_context["weather_data"] = weather_data
        
        # Add activity data if available
        if "activity_data_list" in context:
            activities = ActivityDataExtractor.extract_unique_activities_for_response(context["activity_data_list"])
            response_context["activities"] = activities
        
        # Add errors
        errors = ErrorExtractor.extract_errors_from_context(context)
        response_context["errors"] = errors
        
        return response_context