import json
from typing import List, Dict
from .llm_client import GroqClient
from .search_client import SearchClient

# Initialize clients
llm = GroqClient()
search_tool = SearchClient()

def extract_keywords(text: str) -> Dict[str, str]:
    return {}

def generate_search_query(context_text: str) -> str:
    """
    Generates a concise web search query from the user's context.
    """
    query_gen_prompt = f"Extract a concise web search query to find travel recommendations from this user text: '{context_text}'. Return ONLY the query."
    search_query = llm.generate(query_gen_prompt, system_message="You are a query extractor.")
    # Clean up quotes if any
    search_query = search_query.strip('"').strip("'")
    return search_query

def suggest_places_llm(context_text: str, columns: List[str] = None) -> str:
    """
    RAG-based suggestion, now customized for JSON Schema if columns are provided.
    """
    search_query = generate_search_query(context_text)
    print(f"DEBUG: Search Query: {search_query}")
    
    # 2. Web Search
    try:
        search_results = search_tool.search(search_query)
    except Exception as e:
        print(f"Search failed: {e}")
        search_results = "No external data. Use internal knowledge."

    # 3. RAG Prompt
    if columns:
        # JSON MODE
        system_msg = f"""You are a Data Generator.
        The user has a Trip Planner with specific columns: {columns}.
        
        CRITICAL INSTRUCTION:
        1. Return a VALID JSON LIST of objects.
        2. Each object MUST have keys exactly matching: {columns}.
        3. ENSURE all keys and string values are DOUBLE-QUOTED. Escape inner quotes.
        4. If {columns} has 'Day/Time', use format "Day X - Time" (e.g., "Day 1 - 09:00 AM").
        5. **COVER THE FULL DURATION** requested. If user asks for 2 days, generate Day 1 AND Day 2.
        6. No Markdown formatting (no ```json). Just the raw JSON string.
        7. If a value is unknown, use "-".
        """
        
        rag_prompt = f"""
        User Request/Context: '{context_text}'
        Search Data: {search_results}
        
        Task: Fill the table rows in JSON format.
        """
    else:
        # Standard Fallback (Text Mode)
        system_msg = """You are a helpful travel assistant.
        Provide a detailed itinerary in a clean list format.
        """
        rag_prompt = f"Request: {context_text}\nData: {search_results}"

    return llm.generate(rag_prompt, system_msg)

def refine_data_llm(row_data: dict, instruction: str, columns: list, plan_context: str = "") -> str:
    """
    Surgically updates a single row of data based on user instruction.
    """
    # Lightweight search if instruction is complex
    from agent.recommender import generate_search_query, search_tool # Local import to avoid circular dep if any
    
    search_results = "N/A"
    if len(instruction) > 10:
         try:
             # simple heuristic query
             q = f"{row_data.get('Activity', '')} {instruction}" 
             search_results = search_tool.search(q, max_results=1)
         except:
             pass

    system_msg = f"""You are a Precise Data Editor.
    The user has a JSON object representing a trip step.
    Columns: {columns}
    
    CRITICAL INSTRUCTION:
    1. Update the JSON object based ONLY on the User Instruction.
    2. Input is one object, Output must be a LIST containing that SINGLE updated object.
    3. Return strictly VALID JSON. Keys/Strings must be double-quoted.
    4. Maintain existing values for columns that are not changing.
    5. Use the provided 'Context Plan' to understand dependencies (e.g. time continuity), but ONLY return the modified row.
    """
    
    rag_prompt = f"""
    Context Plan (Full Itinerary):
    {plan_context}
    
    Original Row to Edit: {row_data}
    User Instruction: "{instruction}"
    Search Context: {search_results}
    
    Task: Return JSON List with the updated row.
    """
    
    return llm.generate(rag_prompt, system_msg)

def refine_text_llm(line_text: str, instruction: str) -> str:
    """
    Refines a single line of text based on user instruction.
    Used for Notepad Mode [instruction] syntax.
    """
    system_msg = """You are a Text Editor.
    The user has a line of text and an instruction.
    Rewrite the line to satisfy the instruction.
    Return ONLY the rewritten line. No quotes, no markdown.
    """
    
    prompt = f"""
    Original Line: "{line_text}"
    Instruction: "{instruction}"
    
    Task: Rewrite the line.
    """
    
    return llm.generate(prompt, system_msg).strip()

def restructure_plan_llm(current_plan: list, instruction: str, columns: list) -> str:
    """
    Restructures the entire plan (Add/Remove/Reorder items) based on instruction.
    CRITICAL: Preserves Unchanged Items.
    """
    system_msg = f"""You are a Trip Planner Editor.
    The user provides a Current Plan (JSON) and an Instruction.
    You must return a NEW JSON List representing the updated plan.
    
    CRITICAL RULES:
    1. KEEP all existing rows UNCHANGED unless the instruction specifically conflicts with them.
    2. INSERT new rows where they logically fit (by time/day).
    3. REMOVE rows only if instructed.
    4. Return ONLY the valid VALID JSON List. Double-quote keys/values.
    5. Columns: {columns}
    """
    
    rag_prompt = f"""
    Current Plan:
    {current_plan}
    
    User Instruction: "{instruction}"
    
    Task: Return the modified JSON List.
    """
    
    return llm.generate(rag_prompt, system_msg)

def recommend_single_place(context_text: str) -> str:
    """
    Suggests a SINGLE best-fit place considering climate, time, and crowd factors.
    """
    # 1. Extract context for specific parameters
    query_gen_prompt = f"""
    Analyze this user request: '{context_text}'
    Extract the Destination, Intended Date/Time, and Interests.
    Then, create a specific web search query to find:
    1. The best place matching the interest.
    2. The weather/climate for that specific date/time.
    3. Opening hours or best time to visit.
    
    Return ONLY the search query.
    """
    search_query = llm.generate(query_gen_prompt, system_message="You are a query extractor.")
    search_query = search_query.strip('"').strip("'")
    
    # 2. Search
    search_results = search_tool.search(search_query, max_results=4)
    
    # 3. RAG Prompt
    system_msg = """You are a highly specific travel assistant.
    Recommend ONLY ONE place that best fits the user's request.
    
    CRITICAL:
    - **Format**: Use clear bullet points. **NO TABLES**.
    - You MUST evaluate if the place is suitable for the specific DATE, TIME, and CLIMATE mentioned.
    - If the weather is bad or the place is closed, warn the user and suggest an alternative.
    - Mention the 'Why': explain specific vibes, crowd levels, or unique features.
    """
    
    rag_prompt = f"""
    User Request: '{context_text}'
    Search Data:
    {search_results}
    
    Task:
    Recommend the single best place. Include:
    - Name & Type
    - Weather/Timing Check (Is it good to go now?)
    - Estimated Cost/Price (if available in search)
    - Why it's the perfect choice.
    """
    return llm.generate(rag_prompt, system_msg)

def check_price(context_text: str) -> str:
    """
    Checks price/entry fee for a specific place.
    """
    query_gen_prompt = f"Extract the place name from '{context_text}' and create a search query to find its entry fee, ticket price, or cost. Return ONLY the query."
    search_query = llm.generate(query_gen_prompt, system_message="Query Extractor")
    search_results = search_tool.search(search_query, max_results=3)
    
    system_msg = "You are a price checker. Extract the cost information strictly from the search results."
    return llm.generate(f"Data: {search_results}\n\nQ: Current price/entry fee for the place in '{context_text}'?", system_msg)

def critique_plan(context_text: str) -> str:
    """
    Critiques a proposed plan for feasibility.
    """
    # Search for logistics (distances, opening times)
    query_gen_prompt = f"Extract the main locations and route from '{context_text}' and create a search query to check distances and opening hours. Return ONLY the query."
    search_query = llm.generate(query_gen_prompt, system_message="Query Extractor")
    search_results = search_tool.search(search_query, max_results=3)
    
    system_msg = "You are a travel logic critic. Critique the plan for: 1. Realistic timing? 2. logically ordered? 3. Weather constraints?"
    return llm.generate(f"Plan: {context_text}\n\nLogistics Data: {search_results}\n\nCritique this.", system_msg)

def suggest_places(location: str, interests: List[str] = None) -> List[Dict]:
    pass
