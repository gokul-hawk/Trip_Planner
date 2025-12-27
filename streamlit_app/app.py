import streamlit as st
import pandas as pd
import json
import threading
import os
import sys

# Ensure agent can be imported
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from agent.planner import generate_quick_suggestion
from agent.recommender import refine_data_llm, restructure_plan_llm, refine_text_llm
from agent.graph import run_agent

# --- CONFIGURATION ---
# --- CONFIGURATION ---
st.set_page_config(page_title="Smart Trip Planner", page_icon="✈️", layout="wide")

# Custom CSS for that "Premium" feel
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main Header Styling */
    h1 {
        color: #2c3e50;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    /* Button Styling */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        font-weight: 600;
        transition: all 0.2s ease;
        border: none;
    }
    
    /* Primary Action Buttons */
    div[data-testid="stHorizontalBlock"] button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    div[data-testid="stHorizontalBlock"] button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08);
    }

    /* Secondary/Modify Buttons */
    button[kind="secondary"] {
        background-color: #f7f9fc;
        color: #2c3e50;
        border: 1px solid #e2e8f0;
    }

    /* Container Cards */
    .css-1r6slb0 {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
    }
    
    /* Sidebar Polish */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #e9ecef;
    }
    
    .stTextArea textarea {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if "plan_data" not in st.session_state:
    # Initial DataFrame for Grid
    st.session_state.plan_data = pd.DataFrame([
        {"Day/Time": "Day 1 - 09:00 AM", "Activity": "Breakfast", "Notes": "Try local cafe"}
    ])

if "notepad_content" not in st.session_state:
    st.session_state.notepad_content = "Suggestion: Trip to Paris\n\n- Visit Eiffel Tower\n- Eat Croissants"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/201/201623.png", width=64)
    st.title("Trip Copilot")
    st.caption("AI-Powered Travel Agent")
    
    st.markdown("---")
    
    view_mode = st.radio(
        "Workflow", 
        ["📊 Grid Planner", "📝 Creative Notepad"],
        captions=["Structured Itinerary", "Free-form Brainstorming"]
    )
    
    st.markdown("---")
    
    with st.expander("⚙️ Settings"):
        api_key = st.text_input("Groq API Key", type="password", value=os.environ.get("GROQ_API_KEY", ""))
        if api_key:
            os.environ["GROQ_API_KEY"] = api_key
            
        if st.button("🗑️ Reset All Data", type="primary"):
            st.session_state.plan_data = pd.DataFrame([{"Day/Time": "", "Activity": "", "Notes": ""}])
            st.session_state.notepad_content = ""
            st.session_state.chat_history = []
            st.rerun()
            
    st.info("💡 **Tip**: Use the Chatbot on the right for quick searches!")

# --- MAIN AGENT FUNCTIONS ---
def handle_fill_plan_grid():
    with st.spinner("✨ Drafting your perfect itinerary..."):
        # Context from current grid
        context = "Current Plan:\n"
        for index, row in st.session_state.plan_data.iterrows():
            context += f"{row['Day/Time']} | {row['Activity']} | {row['Notes']}\n"
        
        columns = list(st.session_state.plan_data.columns)
        response = generate_quick_suggestion(context, columns=columns)
        
        try:
            # Clean JSON
            clean_text = response.strip()
            if clean_text.startswith("```json"): clean_text = clean_text[7:]
            if clean_text.endswith("```"): clean_text = clean_text[:-3]
            
            data = json.loads(clean_text)
            st.session_state.plan_data = pd.DataFrame(data)
            st.success("Plan generated!")
        except Exception as e:
            st.error(f"AI Error: {e}")

def handle_modify_plan_grid(instruction):
    with st.spinner("🔧 Restructuring plan..."):
        current_data = st.session_state.plan_data.to_dict(orient="records")
        columns = list(st.session_state.plan_data.columns)
        
        response = restructure_plan_llm(current_data, instruction, columns)
        try:
            clean_text = response.strip()
            if clean_text.startswith("```json"): clean_text = clean_text[7:]
            if clean_text.endswith("```"): clean_text = clean_text[:-3]
            
            data = json.loads(clean_text)
            st.session_state.plan_data = pd.DataFrame(data)
            st.success("Changes applied!")
        except Exception as e:
            st.error(f"Modification Error: {e}")

def handle_fill_notepad():
    with st.spinner("✍️ Writing suggestions..."):
        response = generate_quick_suggestion(st.session_state.notepad_content, columns=None)
        st.session_state.notepad_content += f"\n\n{response}"

# --- UI LOGIC ---

col_main, col_chat = st.columns([7, 3], gap="large")

with col_main:
    if view_mode == "📊 Grid Planner":
        st.header("🗺️ Itinerary Planner")
        st.caption("Double-click cells to edit. Use the 'Modify' tool for bulk changes.")
        
        # Toolbar Container
        with st.container():
            c1, c2, c3 = st.columns([1, 2, 1])
            with c1:
                if st.button("✨ Auto-Fill Plan", help="Generate a full plan based on current rows"):
                    handle_fill_plan_grid()
                    st.rerun()
                
            with c2:
                mod_instr = st.text_input("Modify Instruction", placeholder="e.g. 'Add lunch at 13:00' or 'Remove Day 2'", label_visibility="collapsed")
            
            with c3:
                if st.button("🚀 Apply Change"):
                    if mod_instr:
                        handle_modify_plan_grid(mod_instr)
                        st.rerun()
                    else:
                        st.warning("Please enter an instruction.")
        
        st.divider()
        
        # The Grid
        edited_df = st.data_editor(
            st.session_state.plan_data,
            num_rows="dynamic",
            use_container_width=True,
            key="grid_editor",
            height=600
        )
        st.session_state.plan_data = edited_df

    else:
        st.header("📝 Creative Space")
        st.caption("Draft ideas, lists, and rough notes here.")
        
        st.session_state.notepad_content = st.text_area(
            "Draft your ideas here:", 
            value=st.session_state.notepad_content, 
            height=600,
            label_visibility="collapsed"
        )
        
        c1, c2 = st.columns([1, 4])
        with c1:
            if st.button("✨ Inspire Me"):
                handle_fill_notepad()
                st.rerun()

# --- CHATBOT SECTION ---
with col_chat:
    st.subheader("💬 Assistant")
    
    # Custom Container for Chat
    chat_container = st.container(height=700)
    
    with chat_container:
        # Display History
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
                st.markdown(msg["content"])
                
        # Input
        if prompt := st.chat_input("Ask about weather, costs..."):
            # User Msg
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar="👤"):
                st.markdown(prompt)
                
            # AI Reply
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Thinking..."):
                    try:
                        response = run_agent(prompt)
                        st.markdown(response)
                        st.session_state.chat_history.append({"role": "assistant", "content": response})
                    except Exception as e:
                        st.error(f"Error: {e}")
