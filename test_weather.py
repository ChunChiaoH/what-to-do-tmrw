"""
Direct test of weather API to debug the issue
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_weather_api():
    """Test weatherapi.com directly"""
    api_key = os.getenv("WEATHERAPI_KEY")
    if not api_key:
        print("No API key found")
        return
    
    url = "http://api.weatherapi.com/v1/forecast.json"
    params = {
        "key": api_key,
        "q": "Sydney",
        "days": 1,
        "aqi": "no",
        "alerts": "no"
    }
    
    try:
        response = requests.get(url, params=params)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Location: {data['location']['name']}")
            print(f"Current: {data['current']['condition']['text']}")
            return True
    except Exception as e:
        print(f"Error: {e}")
    
    return False

if __name__ == "__main__":
    test_weather_api()