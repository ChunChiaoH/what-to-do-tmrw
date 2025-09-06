# What To Do Tomorrow? 🤖

An intelligent activity recommendation agent that helps you discover what to do in any city based on real weather forecasts and local venues. Simply ask "What can I do tomorrow in [city]?" and get personalized recommendations!

## Features

- **Real Weather Data**: Gets current weather forecasts from WeatherAPI.com
- **Activity Discovery**: Finds activities and venues using Foursquare Places API
- **Smart Recommendations**: Suggests indoor/outdoor activities based on weather conditions
- **Flexible Date Parsing**: Understands "tomorrow", "this weekend", "next Monday", etc.
- **Global Coverage**: Works with any location worldwide
- **Web Interface**: User-friendly Streamlit web app
- **CLI Support**: Command-line interface for terminal usage

## Quick Start

### Web Interface (Streamlit)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd what-to-do-tmrw
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up API keys**
   Create a `.env` file with:
   ```env
   OPENAI_API_KEY=your-openai-api-key
   WEATHERAPI_KEY=your-weatherapi-key
   FOURSQUARE_API_KEY=your-foursquare-api-key
   ```

4. **Run the web app**
   ```bash
   streamlit run app.py
   ```

### Command Line Interface

```bash
python agent.py
```

## API Keys Required

- **OpenAI API**: For natural language processing and decision making
- **WeatherAPI.com**: For weather forecasts (free tier available)
- **Foursquare Places API**: For activity and venue discovery

## Example Queries

- "What can I do tomorrow in Sydney?"
- "What activities are available this weekend in Melbourne?"
- "What can I do next Monday in Brisbane?"
- "What indoor activities are there in Perth?"

## Architecture

The project uses an **Agent Loop** pattern with:

- **Query Analyzer**: Extracts location and date information from user queries
- **Decision Engine**: Determines what data to fetch (weather, activities, or both)
- **MCP Tools**: Modular tools for weather and activity APIs
- **Response Generator**: Creates natural, contextual responses

### Key Components

- `agent.py` - Main agent with LLM-driven decision making
- `app.py` - Streamlit web interface
- `mcp_server.py` - MCP server with weather and activity tools
- `mcp_client.py` - MCP client for tool communication
- `tools/` - Individual tool implementations
- `utils/` - Helper functions and context builders
- `config/` - Configuration and logging setup

## Deployment

### Streamlit Cloud

The app is ready for deployment on Streamlit Cloud. See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

### Local Development

Two branches are maintained:
- `master` - Local development with full logging
- `streamlit-deployment` - Cloud-optimized version

## How It Works

1. **User Input**: Ask about activities in any location
2. **Query Analysis**: LLM extracts location and time preferences
3. **Weather Check**: Fetches real weather forecast data
4. **Activity Search**: Finds relevant venues and activities
5. **Smart Filtering**: Recommends indoor/outdoor options based on weather
6. **Natural Response**: Generates conversational recommendations

## Technology Stack

- **Python 3.8+**
- **OpenAI GPT Models** for natural language processing
- **Streamlit** for web interface
- **MCP (Model Context Protocol)** for tool communication
- **WeatherAPI.com** for weather data
- **Foursquare Places API** for venue data

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source and available under the MIT License.