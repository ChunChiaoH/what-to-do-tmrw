"""
Prompt templates for the What To Do Agent
"""

def get_query_analyzer_prompt():
    """Get query analyzer prompt with current date context"""
    from datetime import datetime
    current_date = datetime.now().strftime('%Y-%m-%d (%A)')
    
    return f"""Extract info from user query. Today is {current_date}.

Return JSON with:
- location: city name or null
- activity_preferences: activity types mentioned or null  
- time_context: when (tomorrow/today/weekend/null)
- activity_type: "indoor"/"outdoor"/"both"/null

Examples:
"What to do tomorrow in Sydney?" → {{"location": "Sydney", "activity_preferences": null, "time_context": "tomorrow", "activity_type": null}}
"Indoor activities today" → {{"location": null, "activity_preferences": "indoor", "time_context": "today", "activity_type": "indoor"}}"""

QUERY_ANALYZER_PROMPT = get_query_analyzer_prompt()

def get_decision_engine_prompt():
    """Get decision engine prompt with current date context"""  
    from datetime import datetime
    current_date = datetime.now().strftime('%Y-%m-%d (%A)')
    
    return f"""Decision engine for activity agent. Today is {current_date}.

Actions: "call_weather_api" | "call_activity_api" | "respond_to_user"

Logic:
- No location: respond asking for location
- Indoor only: call activity_api (no weather needed)  
- Outdoor + date: call weather_api first
- General query: call activity_api with "both" type
- Have data: respond_to_user

For weather_api calls, include "target_date" in params:
- "today" for today's weather
- "tomorrow" for tomorrow's weather  
- "weekend" for weekend weather
- Or specific date from user query

Return JSON:
{{"action": "...", "tool": "...", "params": {{"location": "...", "target_date": "..."}}, "reasoning": "..."}}"""

DECISION_ENGINE_PROMPT = get_decision_engine_prompt()

def get_response_generator_prompt():
    """Get response generator prompt with current date context"""
    from datetime import datetime
    current_date = datetime.now().strftime('%Y-%m-%d (%A)')
    
    return f"""Generate natural activity recommendations. Today is {current_date}.

Be conversational and personalized:
- Address user's specific location, time, preferences
- Include weather info for outdoor activities  
- Respect indoor/outdoor preferences
- If no location given, ask politely
- If no activities found, explain and suggest alternatives

Respond like a knowledgeable local friend, not a robotic assistant."""

RESPONSE_GENERATOR_PROMPT = get_response_generator_prompt()