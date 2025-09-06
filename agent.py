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
from prompts import get_query_analyzer_prompt, get_decision_engine_prompt, get_response_generator_prompt

load_dotenv()

# Agent configuration
AGENT_CONFIG = {
    "model": "gpt-3.5-turbo",
    "query_temperature": 0.1,
    "decision_temperature": 0.2,
    "max_loops": 5
}

class WhatToDoAgent:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.mcp_server_process = None
        
    async def start_mcp_server(self):
        """Start the MCP server as a subprocess and initialize connection"""
        try:
            self.mcp_server_process = subprocess.Popen(
                [sys.executable, "server.py"],
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
        try:
            response = self.openai_client.chat.completions.create(
                model=AGENT_CONFIG["model"],
                messages=[
                    {"role": "system", "content": get_query_analyzer_prompt()},
                    {"role": "user", "content": query}
                ],
                temperature=AGENT_CONFIG["query_temperature"]
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
                    "current_condition": weather["current"]["condition"],
                    "tomorrow_forecast": weather["forecast"][0]["day_summary"]["condition"] if weather["forecast"] else "no_forecast"
                }
            else:
                context_summary["data_collected"]["weather"] = {"error": weather.get("error")}
        
        if "activity_data" in context:
            activity = context["activity_data"]
            if activity.get("success"):
                context_summary["data_collected"]["activities"] = {
                    "count": activity["total_results"],
                    "type": activity["query_parameters"]["resolved_activity_type"],
                    "data_source": activity.get("data_source", "unknown"),
                    "activities": activity.get("activities", [])  # Include actual activity list
                }
            else:
                context_summary["data_collected"]["activities"] = {"error": activity.get("error")}
        
        try:
            response = self.openai_client.chat.completions.create(
                model=AGENT_CONFIG["model"],
                messages=[
                    {"role": "system", "content": get_decision_engine_prompt()},
                    {"role": "user", "content": f"Current context: {json.dumps(context_summary, indent=2)}"}
                ],
                temperature=AGENT_CONFIG["decision_temperature"]
            )
            #print('***************')
            #print(get_decision_engine_prompt())
            #print('***************')
            #print(context_summary)
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
            "max_loops": AGENT_CONFIG["max_loops"]
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
                # Use LLM-provided parameters, but add fallback logic
                weather_params = decision.get("params", {})
                if "target_date" not in weather_params and "time_context" in query_analysis:
                    weather_params["target_date"] = query_analysis["time_context"]
                elif "target_date" not in weather_params:
                    weather_params["target_date"] = "tomorrow"  # Only as last resort
                
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
        """Generate natural, contextual response using LLM"""
        try:
            # Prepare context summary for LLM response generation
            response_context = {
                "original_query": context.get("query"),
                "user_preferences": context.get("query_analysis", {}),
                "weather_data": None,
                "activities": [],
                "errors": []
            }
            
            # Add weather data if available
            if "weather_data" in context and context["weather_data"].get("success"):
                weather = context["weather_data"]
                forecast = weather.get("forecast", [])
                target_date_info = weather.get("target_date", {})
                
                if forecast:
                    # Find the correct forecast day based on target date
                    target_day_forecast = forecast[0]  # Default to first day
                    target_date_str = target_date_info.get("resolved")
                    
                    if target_date_str:
                        # Look for matching date in forecast
                        for day_forecast in forecast:
                            if day_forecast["date"] == target_date_str:
                                target_day_forecast = day_forecast
                                break
                    
                    response_context["weather_data"] = {
                        "location": weather["location"]["name"],
                        "target_date": target_date_info.get("requested", "unknown"),
                        "condition": target_day_forecast["day_summary"]["condition"],
                        "temp_range": f"{target_day_forecast['day_summary']['min_temp_c']}°C - {target_day_forecast['day_summary']['max_temp_c']}°C",
                        "rain_chance": target_day_forecast["day_summary"]["chance_of_rain"],
                        "date_found": target_day_forecast["date"] == target_date_str if target_date_str else True
                    }
            
            # Collect all unique activities
            if "activity_data_list" in context:
                all_activities = []
                for activity_data in context["activity_data_list"]:
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
                
                response_context["activities"] = unique_activities[:8]
            
            # Collect errors
            if "weather_data" in context and not context["weather_data"].get("success"):
                response_context["errors"].append(f"Weather data unavailable: {context['weather_data'].get('error')}")
            if "activity_data" in context and not context["activity_data"].get("success"):
                response_context["errors"].append(f"Activity data unavailable: {context['activity_data'].get('error')}")
            
            # Generate natural response using LLM
            response = self.openai_client.chat.completions.create(
                model=AGENT_CONFIG["model"],
                messages=[
                    {"role": "system", "content": get_response_generator_prompt()},
                    {"role": "user", "content": f"Context: {json.dumps(response_context, indent=2)}"}
                ],
                temperature=0.5  # Slightly more creative for natural responses
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Response generation failed: {e}")
            # Fallback to simple response
            return f"I encountered an error while preparing your response. Please try asking again."


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