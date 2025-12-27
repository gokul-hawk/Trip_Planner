# ✈️ AI Smart Travel Planner

An intelligent, dual-mode travel assistant that helps you plan perfect trips using AI and real-time web search. It combines a structured **Excel-like Grid** for logistics and a free-form **Creative Notepad** for brainstorming.

## ✨ Key Features

### 1. 🌗 Dual View Modes
Switch instantly between two powerful interfaces:
*   **📊 Grid View**: A structured table (Day/Time, Activity, Notes). perfect for detailed itineraries.
*   **📝 Text View**: A flexible markdown editor for drafting ideas, lists, and rough plans.

### 2. 🧠 Smart Triggers (AI Magic)
The AI is embedded directly into your workflow:
*   **Auto-Complete (`>>`)**:
    *   *Grid*: Type `Lunch at 1pm >>` in a cell, and the AI intelligently fills the Time, Activity, and Notes columns for that row.
    *   *Notepad*: Type `Suggest 3 museums >>` and the AI inserts recommendations right there.
*   **Refine Line (`[...]`)**:
    *   *Notepad*: Type `Visit the Louvre [Make it cheaper]` to act on a specific line.

### 3. pro Plan Restructuring
*   **"✨ Modify" Button**: surgically update your plan without breaking it.
    *   *Example*: "Add a coffee break at 4pm" or "Remove the boat tour".
    *   The AI inserts or removes items while preserving the rest of your schedule perfectly.

### 4. 💬 Integrated Chat Assistant
*   A dedicated Chatbot panel on the right side.
*   Ask questions, get weather info, or check prices using real-time web search (DuckDuckGo).

---

## 🚀 Installation

1.  **Prerequisites**: Python 3.10+
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *(Requires `groq`, `duckduckgo-search` aka `ddgs`, `langchain`, `tk`)*

3.  **API Key**:
    *   Set your Groq API Key in your environment variables:
    ```bash
    set GROQ_API_KEY=your_api_key_here
    ```

## 🎮 Usage

Run the application:
```bash
python gui/smart_notepad.py
```

### Grid View Workflow
1.  **Fill Plan**: Click "🤖 Fill Plan" to generate a full itinerary from scratch based on the current rows.
2.  **Add/Edit**: Double-click any cell to edit. Right-click a row to **"✨ Refine"**.
3.  **Smart Entry**: Double-click a cell, type `Dinner at 8pm >>`, and watch the row auto-fill.
4.  **Modify**: Click "✨ Modify" (Orange Button) to bulk-update the plan (e.g., "Swap Day 1 and Day 2").

### Notepad Workflow
1.  **Toggle**: Click "📝 Text View" (Purple Button).
2.  **Brainstorm**: Type "Trip to Japan".
3.  **Generate**: Type `>>` at the end of a line to expand it.
4.  **Edit**: Use `[instruction]` to rewrite lines.

## 💾 Saving
*   **Grid Mode**: Saves as structured `.csv` files.
*   **Text Mode**: Saves as readable `.txt` files.
