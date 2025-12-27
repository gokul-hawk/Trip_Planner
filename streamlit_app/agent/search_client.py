import warnings

# Suppress the specific rename warning if it occurs
warnings.filterwarnings("ignore", message=".*renamed to `ddgs`.*")

try:
    # Try the new package name first
    from ddgs import DDGS
except ImportError:
    # Fallback to old package
    from duckduckgo_search import DDGS


class SearchClient:
    def __init__(self):
        pass

    def search(self, query: str, max_results: int = 3) -> str:
        """
        Performs a web search and returns formatted snippets.
        """
        try:
            results = []
            with DDGS() as ddgs:
                # Use 'text' method for standard search
                for r in ddgs.text(query, max_results=max_results):
                    results.append(f"Title: {r['title']}\nSnippet: {r['body']}\nLink: {r['href']}")
            
            if not results:
                return "No search results found."
                
            return "\n\n".join(results)
        except Exception as e:
            return f"Error performing search: {str(e)}"
