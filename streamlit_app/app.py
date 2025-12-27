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
st.set_page_config(page_title="Smart Trip Planner", page_icon="✈️", layout="wide")

# Custom CSS for Premium + High Contrast UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700&family=Inter&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3 {
        font-family: 'Outfit', sans-serif;
        color: #1e293b;
    }
    
    /* SIDEBAR STYLING - High Contrast */
    section[data-testid="stSidebar"] {
        background-color: #0f172a; /* Slate 900 */
    }
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] p {
        color: #f8fafc !important; /* White text */
    }
    section[data-testid="stSidebar"] .stRadio label {
        color: #e2e8f0 !important;
    }
    
    /* BUTTONS */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        border: none;
        transition: transform 0.1s;
    }
    
    /* Primary Gradient Button */
    div[data-testid="stHorizontalBlock"] button[kind="secondary"] {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
    }
    div[data-testid="stHorizontalBlock"] button[kind="secondary"]:hover {
        opacity: 0.9;
        transform: scale(1.02);
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if "plan_data" not in st.session_state:
    st.session_state.plan_data = pd.DataFrame([{"Day/Time": "Day 1 - 09:00", "Activity": "Breakfast", "Notes": "Try local cafe"}])

if "notepad_content" not in st.session_state:
    st.session_state.notepad_content = "Suggestion: Trip to Paris\n\n- Visit Eiffel Tower"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/201/201623.png", width=64)
    st.title("Trip Copilot")
    st.caption("AI-Powered • Web Enabled")
    
    st.divider()
    
    view_mode = st.radio("WORKFLOW", ["Data Grid", "Smart Notepad"])
    
    st.divider()
    
    # ADD COLUMN FEATURE
    new_col = st.text_input("New Column Name", placeholder="e.g. Cost, Location")
    if st.button("➕ Add Column"):
        if new_col and new_col not in st.session_state.plan_data.columns:
            st.session_state.plan_data[new_col] = ""
            st.rerun()
            
    st.divider()
    
    if st.button("🗑️ Clear Workspace"):
        st.session_state.plan_data = pd.DataFrame([{"Day/Time": "", "Activity": "", "Notes": ""}])
        st.session_state.notepad_content = ""
        st.session_state.chat_history = []
        st.rerun()

# --- LOGIC HANDLERS ---
def handle_grid_changes(edited_df):
    """ Detects Smart Triggers (>>) in Grid """
    # Compare with previous state is hard, so we just scan for '>>'
    
    triggers_found = False
    
    for idx, row in edited_df.iterrows():
        for col in edited_df.columns:
            val = str(row[col])
            if val.endswith(">>"):
                triggers_found = True
                instruction = val.replace(">>", "").strip()
                
                # Clean the triggers visual immediately
                edited_df.at[idx, col] = instruction # Placeholder or clean?
                
                with st.spinner(f"✨ Refining Row {idx+1}..."):
                    # Prepare Row Context
                    row_dict = row.to_dict()
                    row_dict[col] = instruction # Update with command
                    columns = list(edited_df.columns)
                    
                    try:
                        # Call Refine Agent
                        from agent.recommender import refine_data_llm
                        # Pass full context for awareness
                        full_context = edited_df.to_string()
                        response = refine_data_llm(row_dict, instruction, columns, plan_context=full_context)
                        
                        # Parse List Response
                        clean_text = response.strip()
                        if clean_text.startswith("```json"): clean_text = clean_text[7:]
                        if clean_text.endswith("```"): clean_text = clean_text[:-3]
                        new_row_list = json.loads(clean_text)
                        
                        if new_row_list and isinstance(new_row_list, list):
                            new_row_obj = new_row_list[0]
                            # Update DataFrame
                            for k, v in new_row_obj.items():
                                if k in edited_df.columns:
                                    edited_df.at[idx, k] = v
                                    
                        st.toast("Row Updated Successfully!")
                    except Exception as e:
                        st.error(f"Refine Error: {e}")

    return edited_df

def handle_fill_plan():
    with st.spinner("🤖 Generating Plan..."):
        context = st.session_state.plan_data.to_string()
        cols = list(st.session_state.plan_data.columns)
        resp = generate_quick_suggestion(context, columns=cols)
        try:
             clean_text = resp.strip().replace("```json", "").replace("```", "")
             data = json.loads(clean_text)
             st.session_state.plan_data = pd.DataFrame(data)
        except: st.error("AI Generation Failed")

def handle_modify_plan(instr):
    with st.spinner("✨ Restructuring..."):
        data = st.session_state.plan_data.to_dict(orient="records")
        resp = restructure_plan_llm(data, instr, list(st.session_state.plan_data.columns))
        try:
             clean_text = resp.strip().replace("```json", "").replace("```", "")
             st.session_state.plan_data = pd.DataFrame(json.loads(clean_text))
             st.success("Plan Modified!")
        except: st.error("Modification Failed")

# --- UI LAYOUT ---
col1, col2 = st.columns([2.5, 1], gap="medium")

with col1:
    if view_mode == "Data Grid":
        st.subheader("🗺️ Structured Plan")
        
        # Tools
        c1, c2, c3 = st.columns([1, 2, 1])
        if c1.button("✨ Auto-Fill All"): handle_fill_plan()
        mod_txt = c2.text_input("Modify", placeholder="e.g. 'Add Lunch at 1pm'", label_visibility="collapsed")
        if c3.button("🚀 Modify"): 
            if mod_txt: handle_modify_plan(mod_txt)
            
        # Grid with Callback
        edited_df = st.data_editor(
            st.session_state.plan_data,
            num_rows="dynamic",
            use_container_width=True,
            key="grid",
            height=600
        )
        
        # Check for Triggers
        # We check if the edited_df matches session state. If different, we scan.
        if not edited_df.equals(st.session_state.plan_data):
            # Scan for >>
            final_df = handle_grid_changes(edited_df)
            st.session_state.plan_data = final_df
            st.rerun()

    else:
        st.subheader("📝 Smart Notepad")
        txt = st.text_area("Content", st.session_state.notepad_content, height=600)
        
        # Smart Text Triggers
        if txt != st.session_state.notepad_content:
            # Check for >> 
            lines = txt.split('\n')
            last_line = lines[-1].strip() if lines else ""
            
            if ">>" in txt: # Naive check, improved below
                # Find line with >>
                for i, line in enumerate(lines):
                    if line.strip().endswith(">>"):
                        prompt = line.replace(">>", "").strip()
                        # call AI
                        with st.spinner("Writing..."):
                            resp = generate_quick_suggestion(st.session_state.notepad_content + "\n" + prompt)
                            # Replace line with Prompt + Response
                            lines[i] = prompt + "\n" + resp
                            st.session_state.notepad_content = "\n".join(lines)
                            st.rerun()
            
            # Check for [...]
            elif "]" in txt:
                # Find line ending with [instruction]
                import re
                for i, line in enumerate(lines):
                    match = re.search(r'(.*)\[(.*?)\]$', line)
                    if match:
                        content = match.group(1).strip()
                        instr = match.group(2).strip()
                        # We only trigger if user hits enter (new line added)? 
                        # Streamlit is tricky with keystrokes. We'll use a button for reliability or assume specific syntax.
                        # For now, let's leave [...] as a "Click to Apply" or rely on a helper button.
                        pass

            st.session_state.notepad_content = txt

with col2:
    st.subheader("💬 Assistant")
    
    # Custom Chat Container using st.container
    with st.container(height=700, border=True):
        for msg in st.session_state.chat_history:
             with st.chat_message(msg["role"]): st.markdown(msg["content"])
             
        if prompt := st.chat_input("Ask Copilot..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                     resp = run_agent(prompt)
                     st.markdown(resp)
            st.session_state.chat_history.append({"role": "assistant", "content": resp})
