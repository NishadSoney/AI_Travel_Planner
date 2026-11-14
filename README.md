# AI Travel Planner (CrewAI + Gemini)

An automated AI Travel Planning Crew built with [CrewAI](https://github.com/crewAIInc/crewAI) and Google Gemini.

The system uses a sequential team of 4 autonomous AI agents to build a complete, customized travel plan:
1. **Destination Advisor**: Recommends top destinations matching traveler preferences, season, budget, and interests.
2. **Itinerary Planner**: Designs an optimized day-wise schedule with morning, afternoon, and evening activities.
3. **Budget Planner**: Formulates an itemized cost estimate table (transport, stay, food, activities) with money-saving tips.
4. **Safety & Guide Agent**: Fetches real-time weather forecasts via `wttr.in`, local safety tips, etiquette, scams to avoid, and an organized packing checklist.

Final output is saved to `travel_report.md`.

---

## Getting Started

### 1. Prerequisites
- Python 3.10+
- Google Gemini API Key ([Get one from Google AI Studio](https://aistudio.google.com/apikey))

### 2. Installation
Clone the repository and install dependencies:
```bash
git clone https://github.com/NishadSoney/AI_Travel_Planner.git
cd AI_Travel_Planner
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and add your Gemini API key:
```bash
cp .env.example .env
```
Inside `.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini/gemini-3.5-flash-lite
```

### 4. Run the Planner

#### Option A: Interactive Web UI (Chainlit)
Launch the modern, full-width UI with live agent tracking and thought visualization:
```bash
chainlit run app.py -w
```
Open your browser at `http://localhost:8000`.

#### Option B: Terminal CLI
Run directly in your command line:
```bash
python main.py
```
Follow the interactive prompts in your terminal. Once completed, your plan is saved to `travel_report.md`.
