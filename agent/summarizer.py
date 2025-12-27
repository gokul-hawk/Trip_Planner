from .llm_client import GroqClient
from .search_client import SearchClient

llm = GroqClient()
search_tool = SearchClient()

def summarize_reviews(place_name: str) -> str:
    """
    Summarizes reviews for a place using RAG.
    """
    # Search for reviews
    search_query = f"reviews for {place_name} travel"
    search_results = search_tool.search(search_query, max_results=3)
    
    system_msg = "You are a travel review synthesizer. Read the search snippets and provide a summary of what people say."
    prompt = f"Search Snippets:\n{search_results}\n\nSummarize the vibe and reviews for: {place_name}"
    
    return llm.generate(prompt, system_msg)
