"""
What To Do Tomorrow Agent
Implements Agent Loop pattern with LLM-driven decision making and MCP tools
"""

import asyncio
import json
import os
import logging
from typing import Dict, List, Optional, Any
from openai import OpenAI
from dotenv import load_dotenv
from prompts import get_query_analyzer_prompt, get_decision_engine_prompt, get_response_generator_prompt
from config.logging_config import setup_logging
from mcp_client import MCPClient
from utils import (
    AgentContextBuilder,
    LLMContextBuilder,
    WeatherParamsBuilder,
    ValidationContextBuilder
)

load_dotenv()

# Localhost version - no Streamlit dependencies

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
        self.mcp_client = MCPClient()
        self.logger, _ = setup_logging()
        self.logger = logging.getLogger('agent')
        
    async def start_mcp_server(self):
        """Start the MCP server and initialize connection"""
        success = await self.mcp_client.start_server()
        if not success:
            self.logger.error("Failed to start MCP server")
        return success

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
            self.logger.error(f"Query analysis failed: {e}")
            return {"error": f"Failed to analyze query: {str(e)}"}

    def decide_next_action(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """LLM decides what action to take next based on current context"""
        try:
            context_str = LLMContextBuilder.build_decision_context(context)
            
            response = self.openai_client.chat.completions.create(
                model=AGENT_CONFIG["model"],
                messages=[
                    {"role": "system", "content": get_decision_engine_prompt()},
                    {"role": "user", "content": f"Current context: {context_str}"}
                ],
                temperature=AGENT_CONFIG["decision_temperature"]
            )
            
            content = response.choices[0].message.content.strip()
            return json.loads(content)
            
        except Exception as e:
            self.logger.error(f"Decision making failed: {e}")
            return {"action": "respond_to_user", "error": f"Decision failed: {str(e)}"}

    async def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call MCP tool via the client"""
        return await self.mcp_client.call_tool(tool_name, arguments)

    async def agent_loop(self, query: str) -> str:
        """Main Agent Loop - iterative decision making with LLM"""
        self.logger.info(f"Starting agent loop for: {query}")
        
        # Context will be built after query analysis
        
        # Step 1: Analyze the initial query
        query_analysis = self.analyze_initial_query(query)
        if "error" in query_analysis:
            return f"ERROR: {query_analysis['error']}"
        
        # Validate query analysis
        validation = ValidationContextBuilder.validate_query_analysis(query_analysis)
        if not validation["valid"]:
            return f"ERROR: {validation['error']}"
        
        # Build initial context
        context = AgentContextBuilder.build_initial_context(query, query_analysis, AGENT_CONFIG["max_loops"])
        self.logger.info(f"Query analysis: {query_analysis}")
        
        # Step 2: Agent Loop
        while ValidationContextBuilder.should_continue_loop(context):
            AgentContextBuilder.increment_loop_count(context)
            self.logger.info(f"Agent loop iteration {context['loop_count']}")
            
            # LLM decides next action
            decision = self.decide_next_action(context)
            self.logger.info(f"Decision: {decision.get('reasoning', 'No reasoning provided')}")
            
            if decision["action"] == "call_weather_api":
                self.logger.info("Calling weather API...")
                weather_params = WeatherParamsBuilder.build_weather_params(decision, query_analysis)
                result = await self.call_mcp_tool("weather_api", weather_params)
                AgentContextBuilder.add_weather_data(context, result)
                
                if result.get("success"):
                    self.logger.info("SUCCESS: Weather data retrieved")
                else:
                    self.logger.warning(f"Weather API failed: {result.get('error')}")
            
            elif decision["action"] == "call_activity_api":
                self.logger.info("Calling activity API...")
                result = await self.call_mcp_tool("activity_api", decision["params"])
                AgentContextBuilder.add_activity_data(context, result)
                
                if result.get("success"):
                    self.logger.info(f"SUCCESS: Activity data retrieved ({result['total_results']} activities)")
                else:
                    self.logger.warning(f"Activity API failed: {result.get('error')}")
            
            elif decision["action"] == "respond_to_user":
                self.logger.info("Generating final response...")
                break
            
            else:
                self.logger.warning(f"Unknown action: {decision['action']}")
                break
        
        # Step 3: Generate final response
        return self.generate_final_response(context)

    def generate_final_response(self, context: Dict[str, Any]) -> str:
        """Generate natural, contextual response using LLM"""
        try:
            context_str = LLMContextBuilder.build_response_context(context)
            
            # Generate natural response using LLM
            response = self.openai_client.chat.completions.create(
                model=AGENT_CONFIG["model"],
                messages=[
                    {"role": "system", "content": get_response_generator_prompt()},
                    {"role": "user", "content": f"Context: {context_str}"}
                ],
                temperature=0.5  # Slightly more creative for natural responses
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"Response generation failed: {e}")
            # Fallback to simple response
            return f"I encountered an error while preparing your response. Please try asking again."


    async def chat_ui(self, user_input: str) -> str:
        """Simple chat interface for UI integration (clean, no debug output)"""
        try:
            await self.start_mcp_server()
            response = await self.agent_loop(user_input)
            return response
        except Exception as e:
            self.logger.error(f"Chat UI error: {e}")
            return f"Sorry, I encountered an error: {str(e)}"
        finally:
            self.mcp_client.shutdown()

    async def chat_cli(self):
        """Interactive CLI chat interface"""
        print("What To Do Tomorrow Agent")
        print("Ask me: 'What can I do tomorrow in [city]?'")
        print("Type 'quit' to exit\n")
        
        await self.start_mcp_server()
        
        try:
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
        finally:
            self.mcp_client.shutdown()

    def __del__(self):
        """Clean up MCP client"""
        self.mcp_client.shutdown()


async def main():
    agent = WhatToDoAgent()
    await agent.chat_cli()


if __name__ == "__main__":
    asyncio.run(main())