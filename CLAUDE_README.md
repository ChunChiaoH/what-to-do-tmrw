# What To Do Tomorrow Agent - Project Notes

## Project Goals

### Primary Objective
Build a chatbot agent that can answer questions like "what can I do tomorrow in [location]" using an Agent Loop pattern with MCP tools.

### Key Requirements
1. **LLM-Powered Understanding**
   - Use LLM to understand user prompts
   - Extract location, preferences, activity types from natural language

2. **Agent Loop Decision Making**
   - Agent makes first decision (what tool to call)
   - Gets result from MCP tool
   - Decides whether it needs more information
   - Can make multiple tool calls iteratively
   - Stops when sufficient information is gathered

3. **MCP Architecture**
   - Follow Model Context Protocol standards
   - Single MCP server with two tools:
     - `weather_api` - calls weatherapi.com
     - `activity_api` - provides activity recommendations
   - Agent acts as MCP client

4. **Weather-Based Recommendations**
   - Check weather conditions first
   - Recommend indoor activities if bad weather
   - Recommend outdoor activities if good weather
   - Provide weather-informed advice

### Technical Architecture

```
User Query → Agent (MCP Client) → Decision Loop:
    ├── LLM analyzes query
    ├── Decides which MCP tool to call
    ├── Calls weather_api and/or activity_api
    ├── Evaluates if more info needed  
    ├── Makes additional tool calls if needed
    └── Generates final response
```

### MCP Tools Specification

1. **weather_api**
   - Uses weatherapi.com API
   - Input: location, forecast_days, include_hourly
   - Output: current weather + forecast data

2. **activity_api** 
   - Input: location, weather_condition, activity_type, category
   - Output: curated list of activities based on conditions
   - Supports indoor/outdoor/both activity types

### Success Criteria

- [x] Virtual environment setup
- [x] MCP dependencies installed  
- [x] MCP server with weather and activity tools
- [ ] Agent with LLM-driven decision loop
- [ ] Integration testing with real API calls
- [ ] Support for varied user queries and locations

### API Keys Required
- WEATHERAPI_KEY (weatherapi.com)
- OPENAI_API_KEY (for LLM decision making)
- Note: activity_api uses local data (no external API key needed)

## Current Status
Building the agent loop implementation with iterative decision making capabilities.