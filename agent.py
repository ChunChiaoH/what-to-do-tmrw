"""
What To Do Tomorrow Agent
Implements Agent Loop pattern with LLM-driven decision making and MCP tools
"""

import asyncio
import json
import os
from typing import Dict, List, Optional, Any
from openai import OpenAI
from dotenv import load_dotenv
import subprocess
import sys

load_dotenv()

class WhatToDoAgent:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.mcp_server_process = None
        
    async def start_mcp_server(self):
        """Start the MCP server as a subprocess and initialize connection"""
        try:
            self.mcp_server_process = subprocess.Popen(
                [sys.executable, "mcp_server.py"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            print("MCP server started")
            
            # Initialize MCP connection
            await self.initialize_mcp_connection()
            
        except Exception as e:
            print(f"Failed to start MCP server: {e}")

    async def initialize_mcp_connection(self):
        """Initialize MCP protocol connection"""
        try:
            # Step 1: Send initialize request
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "what-to-do-agent",
                        "version": "1.0.0"
                    }
                }
            }
            
            self.mcp_server_process.stdin.write(json.dumps(init_request) + "\n")
            self.mcp_server_process.stdin.flush()
            
            # Read initialize response
            response_line = self.mcp_server_process.stdout.readline()
            response = json.loads(response_line)
            
            if "result" in response:
                # Step 2: Send initialized notification
                initialized_notification = {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized",
                    "params": {}
                }
                
                self.mcp_server_process.stdin.write(json.dumps(initialized_notification) + "\n")
                self.mcp_server_process.stdin.flush()
                
                print("MCP connection initialized successfully")
                return True
            else:
                print(f"MCP initialization failed: {response}")
                return False
                
        except Exception as e:
            print(f"Failed to initialize MCP connection: {e}")
            return False

    def analyze_initial_query(self, query: str) -> Dict[str, Any]:
        """LLM analyzes the user query and extracts key information"""
        system_prompt = """You are a query analyzer for a "What to do tomorrow" agent.

Extract information from the user's query:
1. location - the city/location they're asking about  
2. activity_preferences - any specific activity types or categories mentioned
3. time_context - when they want to do activities (tomorrow, today, etc.)

Respond ONLY in valid JSON format:
{"location": "city_name_or_null", "activity_preferences": "description_or_null", "time_context": "when"}

Examples:
"What can I do tomorrow in Sydney?" → {"location": "Sydney", "activity_preferences": null, "time_context": "tomorrow"}
"Indoor activities in Melbourne today" → {"location": "Melbourne", "activity_preferences": "indoor activities", "time_context": "today"}
"Cultural things to do in Brisbane tomorrow" → {"location": "Brisbane", "activity_preferences": "cultural activities", "time_context": "tomorrow"}"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            return json.loads(content)
            
        except Exception as e:
            print(f"Query analysis failed: {e}")
            return {"error": f"Failed to analyze query: {str(e)}"}

    def decide_next_action(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """LLM decides what action to take next based on current context"""
        
        # Build context summary for LLM
        context_summary = {
            "original_query": context["query"],
            "extracted_info": context.get("query_analysis", {}),
            "tools_used": context.get("tools_called", []),
            "data_collected": {}
        }
        
        # Add summaries of data we have
        if "weather_data" in context:
            weather = context["weather_data"]
            if weather.get("success"):
                context_summary["data_collected"]["weather"] = {
                    "location": weather["location"]["name"],
                    "current_condition": weather["current_weather"]["condition"],
                    "tomorrow_forecast": weather["forecast"][0]["day_summary"]["condition"] if weather["forecast"] else "no_forecast"
                }
            else:
                context_summary["data_collected"]["weather"] = {"error": weather.get("error")}
        
        if "activity_data" in context:
            activity = context["activity_data"]
            if activity.get("success"):
                context_summary["data_collected"]["activities"] = {
                    "count": activity["total_results"],
                    "type": activity["query_parameters"]["resolved_activity_type"]
                }
            else:
                context_summary["data_collected"]["activities"] = {"error": activity.get("error")}
        
        system_prompt = """You are the decision engine for a "What to do tomorrow" agent.

Based on the current context, decide what to do next.

Available actions:
1. "call_weather_api" - Get weather information for a location
2. "call_activity_api" - Get activity recommendations  
3. "respond_to_user" - Generate final response (when you have sufficient information)

Available MCP tools:
- weather_api: needs {"location": "city_name", "forecast_days": 1, "include_hourly": true}
- activity_api: needs {"location": "city_name", "weather_condition": "optional", "activity_type": "indoor/outdoor/both", "category": "optional"}

Decision logic:
- If no location identified: respond with error
- If no weather data yet: call weather_api first
- If have weather but no activities: call activity_api with weather-informed parameters
- If weather suggests different activity type than what we have: call activity_api again
- If have weather + appropriate activities: respond_to_user

Respond ONLY in valid JSON:
{"action": "call_weather_api|call_activity_api|respond_to_user", "tool": "weather_api|activity_api|null", "params": {...}, "reasoning": "brief_explanation"}"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Current context: {json.dumps(context_summary, indent=2)}"}
                ],
                temperature=0.2
            )
            
            content = response.choices[0].message.content.strip()
            return json.loads(content)
            
        except Exception as e:
            print(f"Decision making failed: {e}")
            return {"action": "respond_to_user", "error": f"Decision failed: {str(e)}"}

    async def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call MCP tool via the server subprocess"""
        if not self.mcp_server_process:
            return {"error": "MCP server not started"}
        
        try:
            # Create MCP request
            mcp_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            # Send request to MCP server
            request_json = json.dumps(mcp_request) + "\n"
            self.mcp_server_process.stdin.write(request_json)
            self.mcp_server_process.stdin.flush()
            
            # Read response
            response_line = self.mcp_server_process.stdout.readline()
            response_data = json.loads(response_line)
            
            # Extract the tool result
            if "result" in response_data:
                content = response_data["result"]["content"][0]["text"]
                return json.loads(content)
            else:
                return {"error": "Invalid MCP response"}
                
        except Exception as e:
            return {"error": f"MCP tool call failed: {str(e)}"}

    async def agent_loop(self, query: str) -> str:
        """Main Agent Loop - iterative decision making with LLM"""
        print(f"Starting agent loop for: {query}")
        
        # Initialize context
        context = {
            "query": query,
            "tools_called": [],
            "loop_count": 0,
            "max_loops": 5  # Prevent infinite loops
        }
        
        # Step 1: Analyze the initial query
        query_analysis = self.analyze_initial_query(query)
        if "error" in query_analysis:
            return f"ERROR: {query_analysis['error']}"
        
        context["query_analysis"] = query_analysis
        print(f"Query analysis: {query_analysis}")
        
        # Check if location is available
        if not query_analysis.get("location"):
            return "ERROR: I couldn't determine which location you're asking about. Please specify a city."
        
        # Step 2: Agent Loop
        while context["loop_count"] < context["max_loops"]:
            context["loop_count"] += 1
            print(f"\nAgent loop iteration {context['loop_count']}")
            
            # LLM decides next action
            decision = self.decide_next_action(context)
            print(f"Decision: {decision.get('reasoning', 'No reasoning provided')}")
            
            if decision["action"] == "call_weather_api":
                print("Calling weather API...")
                # Add target date from query analysis if not in params
                weather_params = decision.get("params", {})
                if "target_date" not in weather_params:
                    weather_params["target_date"] = query_analysis.get("time_context", "tomorrow")
                
                result = await self.call_mcp_tool("weather_api", weather_params)
                context["weather_data"] = result
                context["tools_called"].append("weather_api")
                
                if result.get("success"):
                    print("SUCCESS: Weather data retrieved")
                else:
                    print(f"WARNING: Weather API failed: {result.get('error')}")
            
            elif decision["action"] == "call_activity_api":
                print("Calling activity API...")
                result = await self.call_mcp_tool("activity_api", decision["params"])
                
                # Store activity data (can have multiple calls)
                if "activity_data_list" not in context:
                    context["activity_data_list"] = []
                context["activity_data_list"].append(result)
                context["activity_data"] = result  # Keep latest for decision making
                context["tools_called"].append("activity_api")
                
                if result.get("success"):
                    print(f"SUCCESS: Activity data retrieved ({result['total_results']} activities)")
                else:
                    print(f"WARNING: Activity API failed: {result.get('error')}")
            
            elif decision["action"] == "respond_to_user":
                print("Generating final response...")
                break
            
            else:
                print(f"WARNING: Unknown action: {decision['action']}")
                break
        
        # Step 3: Generate final response
        return self.generate_final_response(context)

    def generate_final_response(self, context: Dict[str, Any]) -> str:
        """Generate human-readable response from collected data"""
        query_analysis = context.get("query_analysis", {})
        location = query_analysis.get("location", "the location")
        
        response_parts = []
        response_parts.append(f"Here's what you can do tomorrow in {location}!")
        
        # Add weather information
        if "weather_data" in context and context["weather_data"].get("success"):
            weather = context["weather_data"]
            tomorrow_forecast = weather["forecast"][0] if weather["forecast"] else None
            
            if tomorrow_forecast:
                day_summary = tomorrow_forecast["day_summary"]
                response_parts.append(
                    f"\n**Tomorrow's Weather:**\n"
                    f"   - {day_summary['condition']} with temperatures {day_summary['min_temp_c']}°C - {day_summary['max_temp_c']}°C\n"
                    f"   - Chance of rain: {day_summary['chance_of_rain']}%"
                )
        
        # Add activity recommendations
        if "activity_data_list" in context:
            all_activities = []
            for activity_data in context["activity_data_list"]:
                if activity_data.get("success"):
                    all_activities.extend(activity_data["activities"])
            
            if all_activities:
                # Deduplicate activities by name
                unique_activities = []
                seen_names = set()
                for activity in all_activities:
                    if activity["name"] not in seen_names:
                        unique_activities.append(activity)
                        seen_names.add(activity["name"])
                
                response_parts.append("\n**Recommended Activities:**")
                for i, activity in enumerate(unique_activities[:8], 1):  # Limit to 8
                    response_parts.append(
                        f"   {i}. **{activity['name']}** ({activity['category']})\n"
                        f"      {activity['description']}"
                    )
        
        # Add weather advice
        if "weather_data" in context and context["weather_data"].get("success"):
            weather = context["weather_data"]
            tomorrow_forecast = weather["forecast"][0] if weather["forecast"] else None
            if tomorrow_forecast:
                advice = self.get_weather_advice(tomorrow_forecast["day_summary"])
                response_parts.append(f"\n**Weather Tip:** {advice}")
        
        # Handle errors
        errors = []
        if "weather_data" in context and not context["weather_data"].get("success"):
            errors.append(f"Weather: {context['weather_data'].get('error')}")
        if "activity_data" in context and not context["activity_data"].get("success"):
            errors.append(f"Activities: {context['activity_data'].get('error')}")
        
        if errors:
            response_parts.append(f"\n**Note:** {'; '.join(errors)}")
        
        return "\n".join(response_parts)

    def get_weather_advice(self, day_summary: Dict[str, Any]) -> str:
        """Generate weather-specific advice"""
        condition = day_summary["condition"].lower()
        temp_max = day_summary["max_temp_c"]
        chance_of_rain = day_summary["chance_of_rain"]
        
        if chance_of_rain > 70:
            return f"High chance of rain ({chance_of_rain}%). Great day for indoor activities or bring an umbrella!"
        elif "sunny" in condition or "clear" in condition:
            return f"Perfect sunny weather! Ideal for outdoor activities. Don't forget sunscreen."
        elif temp_max > 30:
            return f"Hot day ahead ({temp_max}°C). Consider early morning or late afternoon outdoor activities."
        elif temp_max < 10:
            return f"Chilly day ({temp_max}°C). Layer up and consider warm indoor venues."
        else:
            return f"Pleasant weather ({temp_max}°C). Great for any type of activity!"

    async def chat(self):
        """Interactive chat interface"""
        print("What To Do Tomorrow Agent")
        print("Ask me: 'What can I do tomorrow in [city]?'")
        print("Type 'quit' to exit\n")
        
        await self.start_mcp_server()
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                # Run the agent loop
                response = await self.agent_loop(user_input)
                print(f"\nAgent: {response}\n")
                print("-" * 50)
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}\n")

    def __del__(self):
        """Clean up MCP server process"""
        if self.mcp_server_process:
            self.mcp_server_process.terminate()


async def main():
    agent = WhatToDoAgent()
    await agent.chat()


if __name__ == "__main__":
    asyncio.run(main())