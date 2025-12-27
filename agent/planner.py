from .graph import run_agent
from typing import Dict

def generate_quick_suggestion(context: str, columns: list = None) -> str:
    """
    Generates a suggestion for the Smart Notepad.
    If columns are provided, it enforces JSON schema.
    """
    from agent.recommender import suggest_places_llm
    return suggest_places_llm(context, columns)

def create_itinerary(preferences: Dict) -> str:
    """
    Generates a trip itinerary based on preferences.
    Deprecated logic for batch processing, but keeping for compatibility if needed.
    """
    # For now, we focus on the smart notepad integration
    return "Please use the Smart Notepad for interactive planning."
