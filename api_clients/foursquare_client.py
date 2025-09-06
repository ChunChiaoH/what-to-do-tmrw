"""
Foursquare Places API client
"""
import os
import requests
import random
from typing import Dict, List, Any
from config.categories import FOURSQUARE_CATEGORIES, CITY_COORDINATES, RADIUS_OPTIONS


class FoursquareClient:
    """Client for Foursquare Places API"""
    
    def __init__(self):
        self.api_key = os.getenv("FOURSQUARE_API_KEY")
        self.base_url = "https://places-api.foursquare.com"
    
    def _get_search_categories(self, activity_type: str, category: str = None, variety: bool = True) -> List[str]:
        """Get Foursquare category IDs for search based on activity type and preferences"""
        type_categories = FOURSQUARE_CATEGORIES.get(activity_type, {})
        if category and category in type_categories:
            return type_categories[category]
        
        # If no specific category, pick random category types for variety
        if variety and len(type_categories) > 2:
            selected_category_types = random.sample(list(type_categories.keys()), min(3, len(type_categories)))
            categories = []
            for cat_type in selected_category_types:
                categories.extend(type_categories[cat_type])
            return categories
        else:
            return [cat for cat_list in type_categories.values() for cat in cat_list]

    def _build_search_params(self, location: str, categories: List[str], variety: bool = True) -> Dict[str, Any]:
        """Build Foursquare API search parameters with optional variety"""
        base_params = {
            "categories": ",".join(categories[:5]),
            "limit": 15,
        }
        
        if not variety:
            base_params["near"] = location
            return base_params
        
        # Add variety with coordinate-based or location-based search
        use_radius = random.choice([True, False])
        location_lower = location.lower()
        
        if use_radius and location_lower in CITY_COORDINATES:
            lat, lng = CITY_COORDINATES[location_lower]
            base_params.update({
                "ll": f"{lat},{lng}",
                "radius": random.choice(RADIUS_OPTIONS)
            })
        else:
            base_params["near"] = location
        
        return base_params

    def _diversify_results(self, results: List[Dict], variety: bool = True) -> List[Dict]:
        """Select and diversify Foursquare search results"""
        if not variety or len(results) <= 8:
            return results[:8]
        
        # Mix top results with random selections
        top_results = results[:5]
        remaining_results = results[5:]
        
        if remaining_results:
            random_results = random.sample(remaining_results, min(3, len(remaining_results)))
            selected_results = top_results + random_results
        else:
            selected_results = top_results
        
        # Shuffle for variety in presentation
        random.shuffle(selected_results)
        return selected_results

    def _format_result(self, result: Dict, category: str = None) -> Dict[str, Any]:
        """Format a single Foursquare result into our standard format"""
        # Determine category from Foursquare categories
        result_category = category or "general"
        if result.get("categories"):
            fs_category = result["categories"][0].get("name", "").lower()
            if "museum" in fs_category or "gallery" in fs_category or "theater" in fs_category:
                result_category = "culture"
            elif "shop" in fs_category or "mall" in fs_category or "market" in fs_category:
                result_category = "shopping"
            elif "restaurant" in fs_category or "bar" in fs_category or "cafe" in fs_category:
                result_category = "dining"
            elif "gym" in fs_category or "sport" in fs_category:
                result_category = "fitness"
            elif "park" in fs_category or "garden" in fs_category:
                result_category = "nature"
        
        return {
            "name": result["name"],
            "category": result_category,
            "description": result.get("location", {}).get("formatted_address", ""),
            "rating": result.get("rating", 0) / 10.0 if result.get("rating") else None,
            "source": "foursquare"
        }

    async def search_places(self, location: str, activity_type: str, category: str = None, variety: bool = True) -> List[Dict]:
        """Get places from Foursquare API with variety options"""
        if not self.api_key:
            return []
        
        try:
            # Get categories for search
            categories = self._get_search_categories(activity_type, category, variety)
            if not categories:
                return []
            
            # Build search parameters
            params = self._build_search_params(location, categories, variety)
            
            # Debug output
            print(f"Foursquare search: {location}, categories: {params['categories'][:50]}..., radius: {params.get('radius', 'default')}")
            
            # Call Foursquare API
            response = requests.get(
                f"{self.base_url}/places/search",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "accept": "application/json",
                    "X-Places-Api-Version": "2025-06-17"
                },
                params=params
            )
            if response.status_code != 200:
                print(f"Foursquare API error {response.status_code}: {response.text}")
            response.raise_for_status()
            data = response.json()
            
            # Process and format results
            results = data.get("results", [])
            selected_results = self._diversify_results(results, variety)
            
            places = []
            for result in selected_results:
                places.append(self._format_result(result, category))
            
            return places[:8]  # Limit to 8 results
            
        except Exception as e:
            print(f"Foursquare API error: {e}")
            return []