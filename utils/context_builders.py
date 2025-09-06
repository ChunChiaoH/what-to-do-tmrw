"""
Context building utilities for agent loop stages
Centralizes context preparation logic for different LLM interactions
"""
import json
from typing import Dict, Any
from .data_extractors import ContextDataExtractor


class AgentContextBuilder:
    """Build context objects for different agent loop stages"""
    
    @staticmethod
    def build_initial_context(query: str, query_analysis: Dict[str, Any], max_loops: int = 5) -> Dict[str, Any]:
        """Build initial context for agent loop"""
        return {
            "query": query,
            "query_analysis": query_analysis,
            "tools_called": [],
            "loop_count": 0,
            "max_loops": max_loops
        }
    
    @staticmethod
    def add_weather_data(context: Dict[str, Any], weather_result: Dict[str, Any]) -> None:
        """Add weather data to context"""
        context["weather_data"] = weather_result
        if "weather_api" not in context["tools_called"]:
            context["tools_called"].append("weather_api")
    
    @staticmethod
    def add_activity_data(context: Dict[str, Any], activity_result: Dict[str, Any]) -> None:
        """Add activity data to context (can have multiple calls)"""
        # Store activity data (can have multiple calls)
        if "activity_data_list" not in context:
            context["activity_data_list"] = []
        context["activity_data_list"].append(activity_result)
        context["activity_data"] = activity_result  # Keep latest for decision making
        context["tools_called"].append("activity_api")
    
    @staticmethod
    def increment_loop_count(context: Dict[str, Any]) -> None:
        """Increment loop counter"""
        context["loop_count"] += 1


class LLMContextBuilder:
    """Build context for LLM API calls"""
    
    @staticmethod
    def build_decision_context(context: Dict[str, Any]) -> str:
        """Build context string for decision engine LLM call"""
        context_summary = ContextDataExtractor.extract_for_decision_context(context)
        return json.dumps(context_summary, indent=2)
    
    @staticmethod
    def build_response_context(context: Dict[str, Any]) -> str:
        """Build context string for response generation LLM call"""
        response_context = ContextDataExtractor.extract_for_response_context(context)
        return json.dumps(response_context, indent=2)


class WeatherParamsBuilder:
    """Build parameters for weather API calls"""
    
    @staticmethod
    def build_weather_params(decision: Dict[str, Any], query_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Build weather API parameters from LLM decision and query analysis"""
        # Use LLM-provided parameters, but add fallback logic
        weather_params = decision.get("params", {})
        
        if "target_date" not in weather_params and "time_context" in query_analysis:
            weather_params["target_date"] = query_analysis["time_context"]
        elif "target_date" not in weather_params:
            weather_params["target_date"] = "tomorrow"  # Only as last resort
        
        return weather_params


class ValidationContextBuilder:
    """Build context for validation checks"""
    
    @staticmethod
    def validate_query_analysis(query_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Validate query analysis and return validation result"""
        if "error" in query_analysis:
            return {"valid": False, "error": query_analysis["error"]}
        
        if not query_analysis.get("location"):
            return {
                "valid": False, 
                "error": "I couldn't determine which location you're asking about. Please specify a city."
            }
        
        return {"valid": True}
    
    @staticmethod
    def should_continue_loop(context: Dict[str, Any]) -> bool:
        """Check if agent loop should continue"""
        return context["loop_count"] < context["max_loops"]