from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from agent.recommender import suggest_places_llm, recommend_single_place, check_price, critique_plan
from agent.summarizer import summarize_reviews
import os

# Define State
class AgentState(TypedDict):
    input_text: str
    intent: str
    response: str

# Initialize Model
api_key = os.environ.get("GROQ_API_KEY")
llm = ChatGroq(model="openai/gpt-oss-120b", api_key=api_key)

# Node: Classifier
def classify_input(state: AgentState):
    print("--- Classifying Intent ---")
    text = state['input_text']
    
    system_msg = """
    Classify the text into: ITINERARY, SINGLE_REC, CHECK_PRICE, CRITIQUE, REVIEW, CHAT.
    Return ONLY the category name.
    """
    # Using simple LLM call here (or you can use a structured output chain)
    response = llm.invoke([("system", system_msg), ("user", text)])
    intent = response.content.strip()
    return {"intent": intent}

# Node: Itinerary Handler
def handle_itinerary(state: AgentState):
    print("--- Handling Itinerary ---")
    res = suggest_places_llm(state['input_text'])
    return {"response": res}

# Node: Single Rec Handler
def handle_single_rec(state: AgentState):
    print("--- Handling Single Rec ---")
    res = recommend_single_place(state['input_text'])
    return {"response": res}

# Node: Price Handler
def handle_price(state: AgentState):
    print("--- Handling Price ---")
    res = check_price(state['input_text'])
    return {"response": res}

# Node: Critique Handler
def handle_critique(state: AgentState):
    print("--- Handling Critique ---")
    res = critique_plan(state['input_text'])
    return {"response": res}

# Node: Review Handler
def handle_review(state: AgentState):
    print("--- Handling Review ---")
    res = summarize_reviews(state['input_text'])
    return {"response": res}

# Node: Chat Fallback
def handle_chat(state: AgentState):
    return {"response": "Hi! I can help you plan trips, find places, check prices, or critique your itinerary. What do you need?"}

# Router Logic
def route_intent(state: AgentState):
    intent = state['intent']
    if "ITINERARY" in intent: return "itinerary"
    if "SINGLE_REC" in intent: return "single"
    if "CHECK_PRICE" in intent: return "price"
    if "CRITIQUE" in intent: return "critique"
    if "REVIEW" in intent: return "review"
    return "chat"

# Build Graph
builder = StateGraph(AgentState)

builder.add_node("classifier", classify_input)
builder.add_node("itinerary", handle_itinerary)
builder.add_node("single", handle_single_rec)
builder.add_node("price", handle_price)
builder.add_node("critique", handle_critique)
builder.add_node("review", handle_review)
builder.add_node("chat", handle_chat)

builder.set_entry_point("classifier")

builder.add_conditional_edges(
    "classifier",
    route_intent,
    {
        "itinerary": "itinerary",
        "single": "single",
        "price": "price",
        "critique": "critique",
        "review": "review",
        "chat": "chat"
    }
)

builder.add_edge("itinerary", END)
builder.add_edge("single", END)
builder.add_edge("price", END)
builder.add_edge("critique", END)
builder.add_edge("review", END)
builder.add_edge("chat", END)

graph = builder.compile()

def run_agent(text: str) -> str:
    """
    Entry point for the graph.
    """
    try:
        result = graph.invoke({"input_text": text})
        intent = result.get("intent", "UNKNOWN")
        response = result.get("response", "Error generating response.")
        
        return f"\n[AI Assistant ({intent})]:\n{response}\n"
    except Exception as e:
        return f"Agent Error: {str(e)}"
