"""
Foursquare API category mappings for activity types
"""

# Foursquare category mappings
FOURSQUARE_CATEGORIES = {
    "indoor": {
        "culture": ["10000", "10027", "10028", "10029"],
        "shopping": ["17000", "17001", "17069"],
        "entertainment": ["10000", "10032", "10041"],
        "fitness": ["18000", "18021", "18001"],
        "learning": ["12000", "12062"],
        "relaxation": ["18058", "12000"]
    },
    "outdoor": {
        "nature": ["16000", "16032", "16014"],
        "water": ["16048", "16025"],
        "adventure": ["16000", "16034"],
        "sightseeing": ["15000", "15014"],
        "fitness": ["18000", "18042"]
    }
}

# City coordinates for geographic searches
CITY_COORDINATES = {
    "sydney": (-33.8688, 151.2093),
    "melbourne": (-37.8136, 144.9631), 
    "brisbane": (-27.4698, 153.0251),
    "perth": (-31.9505, 115.8605),
    "adelaide": (-34.9285, 138.6007)
}

# Search variety options
RADIUS_OPTIONS = [2000, 5000, 10000, 20000]  # 2km, 5km, 10km, 20km