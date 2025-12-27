import tkinter as tk
from tkinter import messagebox, scrolledtext, font, ttk, filedialog
import threading
import sys
import os
import re

# Ensure we can import from parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.planner import generate_quick_suggestion
from agent.graph import run_agent

class SmartNotepad:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Trip Notepad & Assistant")
        self.root.geometry("1400x800")
        
        # Style Configuration
        self.default_font = ("Segoe UI", 11)
        self.header_font = ("Segoe UI", 13, "bold")
        self.ai_color = "#1a5276" # Dark Blue for AI in Notepad
        self.chat_user_color = "#2c3e50"
        self.chat_ai_color = "#27ae60" # Green for Chatbot
        self.bg_color = "#ffffff"
        self.root.configure(bg="#f0f0f0")

        self.create_layout()
        self.configure_tags_notepad()
        self.configure_tags_chat()

    def create_layout(self):
        # 1. Main Paned Window (Split Logic)
        self.paned_window = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=5, bg="#dcdcdc")
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # 2. Left Pane: Notepad
        self.left_frame = tk.Frame(self.paned_window, bg=self.bg_color)
        self.paned_window.add(self.left_frame, minsize=400)
        self.setup_notepad(self.left_frame)

        # 3. Right Pane: Chatbot
        self.right_frame = tk.Frame(self.paned_window, bg="#f9f9f9")
        self.paned_window.add(self.right_frame, minsize=300)
        self.setup_chatbot(self.right_frame)

    # --- NOTEPAD SECTION ---
    # --- NOTEPAD SECTION (TREEVIEW PLANNER) ---
    def setup_notepad(self, parent):
        # Toolbar
        self.toolbar = tk.Frame(parent, bg="#dcdcdc", height=40)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Buttons
        btn_fill = tk.Button(self.toolbar, text="🤖 Fill Plan", command=self.trigger_planner_ai, bg="#27ae60", fg="white", relief=tk.FLAT)
        btn_fill.pack(side=tk.LEFT, padx=5, pady=5)

        btn_modify = tk.Button(self.toolbar, text="✨ Modify", command=self.modify_plan, bg="#d35400", fg="white", relief=tk.FLAT)
        btn_modify.pack(side=tk.LEFT, padx=5, pady=5)

        btn_add_col = tk.Button(self.toolbar, text="➕ Col", command=self.add_column, bg="#2980b9", fg="white", relief=tk.FLAT)
        btn_add_col.pack(side=tk.LEFT, padx=5, pady=5)
        
        btn_add_row = tk.Button(self.toolbar, text="➕ Row", command=self.add_row, bg="#2980b9", fg="white", relief=tk.FLAT)
        btn_add_row.pack(side=tk.LEFT, padx=5, pady=5)

        btn_save = tk.Button(self.toolbar, text="💾 Save", command=self.save_file, bg="#7f8c8d", fg="white", relief=tk.FLAT)
        btn_save.pack(side=tk.LEFT, padx=5, pady=5)

        # Toggle Button
        self.btn_toggle = tk.Button(self.toolbar, text="📝 Text View", command=self.toggle_view, bg="#8e44ad", fg="white", relief=tk.FLAT)
        self.btn_toggle.pack(side=tk.LEFT, padx=5, pady=5)

        # Container for Views
        self.view_container = tk.Frame(parent, bg=self.bg_color)
        self.view_container.pack(fill=tk.BOTH, expand=True)

        self.current_view_mode = "grid" # or "text"

        # Initialize both views
        self.setup_grid_view(self.view_container)
        self.setup_text_view(self.view_container)
        
        # Show default
        self.tree_frame.pack(fill=tk.BOTH, expand=True)
        self.text_frame.pack_forget()

    def setup_grid_view(self, parent):
        self.tree_frame = tk.Frame(parent)
        
        # Treeview (The Grid)
        style = ttk.Style()
        style.configure("Treeview", font=self.default_font, rowheight=30)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        self.columns = ["Day/Time", "Activity", "Notes"]
        self.tree = ttk.Treeview(self.tree_frame, columns=self.columns, show="headings", selectmode="browse")
        
        self.tree.heading("Day/Time", text="Day/Time")
        self.tree.column("Day/Time", width=120)
        self.tree.heading("Activity", text="Activity")
        self.tree.column("Activity", width=200)
        self.tree.heading("Notes", text="Notes")
        self.tree.column("Notes", width=300)

        # Scrollbar
        vsb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # Bindings for Editing
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-3>", self.show_context_menu)
        
        # Initial Dummy Row
        self.tree.insert("", "end", values=("Day 1 - 09:00 AM", "Breakfast", "Try local cafe"))

    def setup_text_view(self, parent):
        self.text_frame = tk.Frame(parent)
        self.text_area = scrolledtext.ScrolledText(self.text_frame, wrap=tk.WORD, font=self.default_font, bg=self.bg_color, undo=True)
        self.text_area.pack(fill=tk.BOTH, expand=True)
        
        # Basic Instructions
        self.text_area.insert("1.0", "📝 Free-form Notepad Mode\nType your plan here or click 'Fill Plan' for AI help.\n\n")
        
        # Smart Triggers binding
        self.text_area.bind("<KeyRelease>", self.check_notepad_triggers)

    def check_notepad_triggers(self, event):
        if event.keysym in ("Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R"): return

        # Get current line
        insert_pos = self.text_area.index(tk.INSERT)
        line_num = insert_pos.split('.')[0]
        line_text = self.text_area.get(f"{line_num}.0", f"{line_num}.end")

        # Trigger 1: Generation ">>"
        if line_text.strip().endswith(">>"):
            # Remove the >>
            clean_line = line_text.replace(">>", "").strip()
            # Update text area: remove >>
            # We need to be careful with cursor position
            start_idx = f"{line_num}.0"
            end_idx = f"{line_num}.end"
            self.text_area.delete(start_idx, end_idx)
            self.text_area.insert(start_idx, clean_line)
            
            # Trigger AI with this context
            # We use the previous lines + this line as context
            context = self.text_area.get("1.0", f"{line_num}.end")
            threading.Thread(target=self.get_text_suggestion, args=(context,)).start()
            return

        # Trigger 2: Refinement "[instruction]" at end of line
        # Regex to capture content inside last [...]
        match = re.search(r'\[(.*?)\]$', line_text)
        if match and event.keysym == 'bracketright': # optimize: check only if ] typed
            instruction = match.group(1)
            # The Text to refine is the part BEFORE the [
            content_to_refine = line_text[:match.start()].strip()
            
            if len(instruction) > 2 and len(content_to_refine) > 2:
                # Trigger Refinement
                threading.Thread(target=self.process_text_refinement, args=(line_num, content_to_refine, instruction)).start()

    def process_text_refinement(self, line_num, content, instruction):
        try:
            from agent.recommender import refine_text_llm
            response = refine_text_llm(content, instruction)
            self.root.after(0, lambda: self.apply_text_refinement(line_num, response))
        except Exception as e:
            print(f"Refine Text Error: {e}")

    def apply_text_refinement(self, line_num, new_text):
        start_idx = f"{line_num}.0"
        end_idx = f"{line_num}.end"
        self.text_area.delete(start_idx, end_idx)
        self.text_area.insert(start_idx, new_text)

    def toggle_view(self):
        if self.current_view_mode == "grid":
            self.current_view_mode = "text"
            self.tree_frame.pack_forget()
            self.text_frame.pack(fill=tk.BOTH, expand=True)
            self.btn_toggle.config(text="📊 Grid View")
        else:
            self.current_view_mode = "grid"
            self.text_frame.pack_forget()
            self.tree_frame.pack(fill=tk.BOTH, expand=True)
            self.btn_toggle.config(text="📝 Text View")

    def add_row(self):
        # Add basic empty row
        self.tree.insert("", "end", values=["" for _ in self.columns])

    def add_column(self):
        from tkinter import simpledialog
        name = simpledialog.askstring("New Column", "Column Name (e.g. Cost):")
        if name:
            # Update columns list
            self.columns.append(name)
            
            # Recreate columns in Treeview (Treeview columns are static-ish, often easier to reconfig)
            current_data = []
            for item in self.tree.get_children():
                current_data.append(self.tree.item(item)['values'])
            
            self.tree["columns"] = self.columns
            for col in self.columns:
                self.tree.heading(col, text=col)
                self.tree.column(col, width=120)
            
            # Restore data with padded empty value for new col
            self.tree.delete(*self.tree.get_children())
            for row in current_data:
                new_row = list(row) + [""]
                self.tree.insert("", "end", values=new_row)

    def on_double_click(self, event):
        """ Handling In-Cell Editing """
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell": return
        
        column = self.tree.identify_column(event.x) # Returns '#1', '#2'
        item_id = self.tree.identify_row(event.y)
        
        if not column or not item_id: return
        
        # Get column index (1-based string -> 0-based int)
        col_idx = int(column[1:]) - 1
        
        # Get current value
        current_values = self.tree.item(item_id).get("values")
        current_text = current_values[col_idx] if current_values else ""

        # Create Entry widget
        x, y, w, h = self.tree.bbox(item_id, column)
        entry = tk.Entry(self.tree, font=self.default_font)
        entry.place(x=x, y=y, width=w, height=h)
        entry.insert(0, current_text)
        entry.focus()

        def save_edit(event=None):
            if getattr(entry, 'skip_save', False): return
            
            try:
                new_text = entry.get()
                # Check if item still exists
                if not self.tree.exists(item_id): return
                
                current_values = list(self.tree.item(item_id, "values"))
                # Ensure list is long enough
                while len(current_values) <= col_idx:
                    current_values.append("")
                
                current_values[col_idx] = new_text
                self.tree.item(item_id, values=current_values)
            except Exception as e:
                pass # Item likely deleted or view changed
            finally:
                if entry.winfo_exists():
                    entry.destroy()

        def check_grid_triggers(event):
             if entry.get().endswith(">>"):
                 # Trigger Row Refinement
                 instruction = entry.get().replace(">>", "").strip()
                 
                 # Prevent FocusOut from triggering save_edit
                 entry.skip_save = True
                 entry.destroy()
                 
                 # Check existence
                 if not self.tree.exists(item_id): return
                 
                 current_values = self.tree.item(item_id)['values']
                 row_dict = {col: val for col, val in zip(self.columns, current_values)}
                 
                 threading.Thread(target=self.process_refinement, args=(row_dict, instruction, self.columns, item_id)).start()

        entry.bind("<Return>", save_edit)
        entry.bind("<FocusOut>", lambda e: save_edit())
        entry.bind("<KeyRelease>", check_grid_triggers)

    def modify_plan(self):
        """ Global Plan Modifier """
        from tkinter import simpledialog
        instruction = simpledialog.askstring("Modify Plan", "What changes should I make? (e.g. 'Add lunch at 1pm', 'Remove the museum')")
        if not instruction: return
        
        # Gather execution context
        current_data = []
        for item in self.tree.get_children():
            # Convert values tuple to dict
            vals = self.tree.item(item)['values']
            row_dict = {col: val for col, val in zip(self.columns, vals)}
            current_data.append(row_dict)
            
        threading.Thread(target=self.process_restructure, args=(current_data, instruction, self.columns)).start()

    def process_restructure(self, current_data, instruction, columns):
        try:
            from agent.recommender import restructure_plan_llm
            response = restructure_plan_llm(current_data, instruction, columns)
            self.root.after(0, lambda: self.populate_plan(response))
        except Exception as e:
            print(f"Restructure Error: {e}")

    def trigger_planner_ai(self):
        if self.current_view_mode == "grid":
            # Context: Serialize current rows to text
            context = "Current Plan:\n"
            for item in self.tree.get_children():
                row = self.tree.item(item)['values']
                context += " | ".join(str(r) for r in row) + "\n"
            
            if len(self.tree.get_children()) <= 1:
                context += "\nPlease suggest a comprehensive plan."

            # Pass columns schema
            threading.Thread(target=self.get_planner_suggestion, args=(context, self.columns)).start()
        else:
            # TEXT MODE
            context = self.text_area.get("1.0", tk.END).strip()
            if len(context) < 10:
                context += "Suggest a travel itinerary."
            
            # Pass columns=None to trigger Markdown mode
            threading.Thread(target=self.get_text_suggestion, args=(context,)).start()

    def get_text_suggestion(self, context):
        try:
            # Import explicitly to be safe
            from agent.planner import generate_quick_suggestion
            response = generate_quick_suggestion(context, columns=None)
            self.root.after(0, lambda: self.populate_text_plan(response))
        except Exception as e:
            print(f"Text Planner Error: {e}")

    def populate_text_plan(self, text):
        self.text_area.insert(tk.END, "\n\n" + text + "\n")
        self.text_area.see(tk.END)

    def get_planner_suggestion(self, context, columns):
        try:
            # Call planner with columns schema
            response = generate_quick_suggestion(context, columns=columns)
            
            # Debug: Save raw response
            with open("debug_last_json.txt", "w", encoding="utf-8") as f:
                f.write(response)

            self.root.after(0, lambda: self.populate_plan(response))
        except Exception as e:
            print(f"Planner Error: {e}")

    def populate_plan(self, json_text):
        """
        Parses JSON response and inserts into Grid.
        Expects: JSON List of Dicts
        """
        import json
        import re
        
        # Cleaning: valid JSON might be wrapped in quotes or markdown code blocks
        clean_text = json_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()
        
        # Basic fixes for common LLM JSON errors
        clean_text = re.sub(r',\s*]', ']', clean_text) # Remove trailing comma
        clean_text = re.sub(r',\s*}', '}', clean_text) # Remove trailing comma in obj

        try:
            data = json.loads(clean_text)
            if not isinstance(data, list):
                print("Error: AI did not return a list.")
                return

            # Clear existing? Maybe ask user? For now, let's append.
            self.tree.delete(*self.tree.get_children())
            
            for row_obj in data:
                # Map keys to current columns order
                values = []
                for col in self.columns:
                    val = row_obj.get(col, "")
                    values.append(val)
                
                self.tree.insert("", "end", values=values)

        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {e}")
            print(f"Raw Text: {json_text}")
            # Optional: Show error in UI
            self.tree.insert("", "end", values=("Error", "Parsing Failed", "Check Console", ""))

    def show_context_menu(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id: return
        
        self.tree.selection_set(item_id)
        menu = tk.Menu(self.tree, tearoff=0)
        menu.add_command(label="✨ Refine this Row", command=lambda: self.refine_row(item_id))
        menu.add_command(label="❌ Delete Row", command=lambda: self.tree.delete(item_id))
        menu.post(event.x_root, event.y_root)

    def refine_row(self, item_id):
        from tkinter import simpledialog
        instruction = simpledialog.askstring("Refine Row", "How should this step change? (e.g. 'Make it later')")
        if not instruction: return

        # Get current row data
        current_values = self.tree.item(item_id)['values']
        row_dict = {col: val for col, val in zip(self.columns, current_values)}
        
        # Run in thread
        threading.Thread(target=self.process_refinement, args=(row_dict, instruction, self.columns, item_id)).start()

    def process_refinement(self, row_dict, instruction, columns, item_id):
        try:
            from agent.recommender import refine_data_llm
            response = refine_data_llm(row_dict, instruction, columns)
            
            # Update UI
            self.root.after(0, lambda: self.apply_refinement(item_id, response))
        except Exception as e:
            print(f"Refine Error: {e}")

    def apply_refinement(self, item_id, json_text):
        import json
        clean_text = json_text.strip()
        if clean_text.startswith("```json"): clean_text = clean_text[7:]
        if clean_text.endswith("```"): clean_text = clean_text[:-3]
        
        try:
            data = json.loads(clean_text)
            if isinstance(data, list) and len(data) > 0:
                row_obj = data[0] # Take first result
                values = [row_obj.get(col, "") for col in self.columns]
                self.tree.item(item_id, values=values)
        except:
            pass
            
    def configure_tags_notepad(self):
        pass # Not needed for Treeview styling, driven by ttk.Style

    # --- CHATBOT SECTION ---
    def setup_chatbot(self, parent):
        # Header
        header = tk.Frame(parent, bg="#dcdcdc", bd=1, relief=tk.RAISED, height=40)
        header.pack(side=tk.TOP, fill=tk.X)
        tk.Label(header, text="💬 Trip Assistant", font=self.header_font, bg="#dcdcdc").pack(pady=8)

        # Chat History (Read Only)
        self.chat_history = scrolledtext.ScrolledText(parent, wrap=tk.WORD, font=self.default_font, bg="#f9f9f9", state='disabled', padx=10, pady=10)
        self.chat_history.pack(expand=True, fill='both', padx=5, pady=5)

        # Input Area
        input_frame = tk.Frame(parent, bg="#f9f9f9")
        input_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=10)

        self.chat_input = tk.Entry(input_frame, font=self.default_font, bg="white", relief=tk.SOLID, bd=1)
        self.chat_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, ipady=5)
        self.chat_input.bind("<Return>", self.send_chat_message)

        btn_send = tk.Button(input_frame, text="Send", command=self.send_chat_message, bg="#8e44ad", fg="white", font=("Segoe UI", 9, "bold"), relief=tk.FLAT)
        btn_send.pack(side=tk.RIGHT, padx=5)

    def configure_tags_chat(self):
        self.chat_history.tag_config("user_msg", foreground=self.chat_user_color, font=("Segoe UI", 11, "bold"), justify='right', lmargin1=50)
        self.chat_history.tag_config("ai_msg", foreground=self.chat_ai_color, font=("Segoe UI", 11), justify='left', rmargin=50)
        self.chat_history.tag_config("bold", font=("Segoe UI", 11, "bold")) # Re-use styling logic

    def send_chat_message(self, event=None):
        msg = self.chat_input.get().strip()
        if not msg: return
        
        self.chat_input.delete(0, tk.END)
        self.append_chat(f"You: {msg}\n", "user_msg")
        
        threading.Thread(target=self.get_chat_response, args=(msg,)).start()

    def get_chat_response(self, msg):
        try:
            # Independent Query: Just runs the agent on the message
            response = run_agent(msg) 
            # We don't need double insertion. Just insert the markdown.
            self.root.after(0, lambda: self.insert_markdown_chat(response))
        except Exception as e:
            self.root.after(0, lambda: self.append_chat(f"Error: {str(e)}\n", "ai_msg"))

    def append_chat(self, text, tag):
        self.chat_history.config(state='normal')
        self.chat_history.insert(tk.END, text, tag)
        self.chat_history.insert(tk.END, "\n")
        self.chat_history.see(tk.END)
        self.chat_history.config(state='disabled')

    def insert_markdown_chat(self, text):
        """
        Inserts formatted markdown into the chat history.
        """
        self.chat_history.config(state='normal')
        self.chat_history.insert(tk.END, "\n", "ai_msg")
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                self.chat_history.insert(tk.END, "\n", "ai_msg")
                continue
                
            tags = ["ai_msg"]
            
            if line.startswith("# "):
                tags.append("h1")
                line = line[2:]
            elif line.startswith("## "):
                tags.append("h2")
                line = line[3:]
            elif line.startswith("- "):
                tags.append("bullet")
            
            # Simple Bold parsing
            parts = re.split(r'(\*\*.*?\*\*)', line)
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    clean_part = part[2:-2]
                    self.chat_history.insert(tk.END, clean_part, tuple(tags + ["bold"]))
                else:
                    self.chat_history.insert(tk.END, part, tuple(tags))
            
            self.chat_history.insert(tk.END, "\n", "ai_msg")
            
        self.chat_history.see(tk.END)
        self.chat_history.config(state='disabled')

    # --- SHARED HELPERS ---


    def save_file(self):
        filename = filedialog.asksaveasfilename(defaultextension=".csv" if self.current_view_mode == "grid" else ".txt",
                                              filetypes=[("All Files", "*.*")])
        if not filename:
            return

        if self.current_view_mode == "grid":
            # Save CSV
            try:
                import csv
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(self.columns)
                    for item in self.tree.get_children():
                        writer.writerow(self.tree.item(item)['values'])
                messagebox.showinfo("Saved", "Project saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save file: {e}")
        else:
            # Save Text
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(self.text_area.get("1.0", tk.END))
                messagebox.showinfo("Saved", "Notepad saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save file: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SmartNotepad(root)
    root.mainloop()
