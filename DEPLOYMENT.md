# Streamlit Cloud Deployment Guide

## Prerequisites
1. GitHub repository with this code
2. Streamlit Cloud account (free at [share.streamlit.io](https://share.streamlit.io))
3. API keys for:
   - OpenAI API (`OPENAI_API_KEY`)
   - WeatherAPI.com (`WEATHERAPI_KEY`) 
   - Foursquare Places API (`FOURSQUARE_API_KEY`)

## Deployment Steps

### 1. Push Code to GitHub
```bash
git push origin streamlit-deployment
```

### 2. Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Select your GitHub repository
4. Choose `streamlit-deployment` branch
5. Set main file path: `app.py`
6. Click "Deploy"

### 3. Configure Secrets
In your Streamlit Cloud app dashboard:
1. Go to "Settings" → "Secrets"
2. Add these secrets:

```toml
OPENAI_API_KEY = "sk-your-openai-key-here"
WEATHERAPI_KEY = "your-weatherapi-key-here"
FOURSQUARE_API_KEY = "your-foursquare-key-here"
ENVIRONMENT = "production"
```

### 4. Your App is Live! 🎉
Your chatbot will be available at: `https://your-app-name.streamlit.app`

## Key Differences from Local Version

### Logging
- **Local**: Logs to `logs/` directory with detailed file logging
- **Cloud**: Console logging only (WARNING level and above)

### API Keys
- **Local**: Uses `.env` file or environment variables
- **Cloud**: Uses Streamlit secrets management

### File System
- **Local**: Full read/write access
- **Cloud**: Read-only filesystem (no log files created)

## Troubleshooting

### Common Issues
1. **Import errors**: Make sure all dependencies are in `requirements.txt`
2. **API key issues**: Double-check secrets configuration
3. **File permission errors**: Our logging system automatically adapts for cloud

### Debug Tips
- Check app logs in Streamlit Cloud dashboard
- Use the "Rerun" button to restart the app
- Monitor resource usage in the dashboard

## Local Testing
To test the cloud-compatible version locally:
```bash
# Set environment variable to simulate cloud
export STREAMLIT_SERVER_HEADLESS=true
streamlit run app.py
```

## Branch Strategy
- `master`: Local development version
- `streamlit-deployment`: Cloud-ready version with deployment optimizations