"""
Date parsing and handling utilities
"""
from datetime import datetime, timedelta
from typing import Dict, Any


def parse_target_date(target_date: str) -> Dict[str, Any]:
    """Parse target date string and return date info"""
    today = datetime.now().date()
    result = {"date": None, "description": target_date or "tomorrow"}
    
    if not target_date or target_date.lower() in ["tomorrow", "tmrw"]:
        result["date"] = today + timedelta(days=1)
    elif target_date.lower() == "today":
        result["date"] = today
    elif target_date.lower() in ["this weekend", "weekend"]:
        # Find next Saturday
        days_until_saturday = (5 - today.weekday()) % 7
        if days_until_saturday == 0 and today.weekday() == 5:  # It's Saturday
            result["date"] = today
        else:
            result["date"] = today + timedelta(days=days_until_saturday if days_until_saturday > 0 else 6)
    elif target_date.lower() in ["next week", "next monday"]:
        days_until_monday = (7 - today.weekday()) % 7
        result["date"] = today + timedelta(days=days_until_monday if days_until_monday > 0 else 7)
    else:
        # Try to parse as date string (YYYY-MM-DD format)
        try:
            result["date"] = datetime.strptime(target_date, "%Y-%m-%d").date()
        except ValueError:
            # Default to tomorrow if parsing fails
            result["date"] = today + timedelta(days=1)
            result["description"] = "tomorrow (default)"
    
    return result