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
- [x] Agent with LLM-driven decision loop
- [x] Integration testing with real API calls
- [x] Support for varied user queries and locations

### Current Status ✅

**COMPLETED FEATURES:**
- ✅ LLM query analysis (extracts location, preferences, time context)
- ✅ Agent Loop with iterative decision making (3-step process)
- ✅ MCP server with proper protocol initialization
- ✅ WeatherAPI.com integration (real weather data)
- ✅ Activity recommendations based on weather conditions
- ✅ Weather-informed advice generation

**WORKING EXAMPLE:**
```
Query: "What can I do tomorrow in Sydney?"

Agent Loop:
1. LLM extracts: location="Sydney", time="tomorrow"  
2. Calls weather_api → gets cloudy, 13-17°C, 0% rain
3. Calls activity_api → returns mixed indoor/outdoor activities
4. Generates response with weather tip

Result: 6 activity recommendations with weather advice
```

### Latest Updates ✅
- ✅ **Foursquare Integration**: Real activity data from Foursquare Places API
- ✅ **Enhanced Variety**: Intelligent geographic and category diversification
- ✅ **Date-Aware Intelligence**: LLM understands current date and time context
- ✅ **Natural Responses**: LLM-powered conversational response generation
- ✅ **Target Date Accuracy**: Weather API correctly handles "today", "tomorrow", "weekend", etc.

## Code Refactoring Plan 🔧

### Current Architecture Issues
- **mcp_server.py**: 485 lines (too large)
- **agent.py**: 408 lines (manageable but growing)
- **Large functions**: `get_foursquare_places()` ~140 lines
- **Mixed concerns**: API clients, business logic, configuration all mixed

### Target Structure (Following MCP Best Practices)
```
mcp_server/
├── server.py              # Main MCP server entry point
├── tools/                 # Tool implementations
│   ├── weather_tool.py     # Weather API tool
│   └── activity_tool.py    # Activity API tool
├── api_clients/           # External API clients
│   ├── weather_client.py   # WeatherAPI.com client
│   └── foursquare_client.py # Foursquare API client
├── utils/                 # Utility functions
│   ├── date_utils.py       # Date parsing logic
│   └── location_utils.py   # Geographic utilities
├── config/               # Configuration
│   └── categories.py      # Foursquare categories
└── prompts.py            # Centralized prompts
```

### Refactoring Phases

**Phase 1: Split Large Functions** ✅ *COMPLETED*
- ✅ Break down `get_foursquare_places()` into 4 smaller functions
- ✅ Extract coordinate mapping logic
- ✅ Extract result processing and variety algorithms
- ✅ Maintain same interface for backward compatibility

**Phase 2: Extract Configuration & Utilities** ✅ *COMPLETED*
- ✅ Move `FOURSQUARE_CATEGORIES` to `config/categories.py`
- ✅ Extract `parse_target_date()` to `utils/date_utils.py`
- ✅ Create reusable utility functions

**Phase 3: Full Module Restructure** ✅ *COMPLETED*
- ✅ Split tools into separate files
- ✅ Extract API clients from tools
- ✅ Implement central server pattern
- ✅ Remove old monolithic mcp_server.py

### Benefits of Refactoring
- ✅ **Testability**: Each module can be unit tested
- ✅ **Maintainability**: Smaller, focused files (< 200 lines each)
- ✅ **Reusability**: API clients usable across multiple tools
- ✅ **Scalability**: Easy to add new tools and features
- ✅ **Standards Compliance**: Follows 2025 MCP best practices

### API Keys Required
- WEATHERAPI_KEY (weatherapi.com)
- OPENAI_API_KEY (for LLM decision making)
- FOURSQUARE_API_KEY (for real activity data)

## Current Status
**Production-ready agent** with clean modular architecture! ✅ All refactoring phases completed following 2025 MCP best practices.

## Future Improvements

### OpenAI Function Calling Migration
**Priority:** High | **Effort:** Medium | **Status:** Planned

Currently using prompt engineering for LLM decision making (returning JSON strings). Consider migrating to OpenAI's structured function calling for better reliability:

**Benefits:**
- More reliable than JSON parsing (no parse errors)
- Built-in parameter validation 
- Cleaner system prompts (focus on reasoning vs output format)
- Type safety and constraints
- Support for parallel function calls

**Implementation:**
- Create function schemas for `call_weather_api`, `call_activity_api`, `respond_to_user`
- Replace decision engine prompt with function definitions
- Update `decide_next_action()` to use `tools` parameter
- Add proof of concept to validate approach

**Impact:** Improved reliability and maintainability of agent decision making.