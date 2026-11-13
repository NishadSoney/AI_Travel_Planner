import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

# Safeguard against Windows permission issues with CrewAI credentials cache
if sys.platform == "win32":
    local_crew_dir = Path(__file__).resolve().parent / ".crewai_data"
    local_crew_dir.mkdir(parents=True, exist_ok=True)
    try:
        appdata = os.environ.get("LOCALAPPDATA")
        if not appdata or not os.access(appdata, os.W_OK):
            os.environ["LOCALAPPDATA"] = str(local_crew_dir)
        else:
            test_path = Path(appdata) / "crewai" / "credentials"
            test_path.mkdir(parents=True, exist_ok=True)
    except (PermissionError, OSError):
        os.environ["LOCALAPPDATA"] = str(local_crew_dir)

from crewai import Agent, LLM
from crewai.tools import tool
from dotenv import load_dotenv

load_dotenv(override=True)

# ---------------------------------------------------------------- Gemini LLM
raw_model = os.getenv("GEMINI_MODEL", "gemini/gemini-3.5-flash-lite").strip()

# Discontinued models that Google rejects with 404
DEPRECATED_MODELS = {
    "gemini/gemini-1.5-flash": "gemini/gemini-3.5-flash-lite",
    "gemini/gemini-1.5-pro": "gemini/gemini-3.8-flash",
    "gemini/gemini-2.5-flash": "gemini/gemini-3.5-flash-lite",
    "gemini/gemini-2.5-flash-lite": "gemini/gemini-3.5-flash-lite",
    "gemini/gemini-2.5-pro": "gemini/gemini-3.8-flash",
    "gemini-2.5-flash": "gemini/gemini-3.5-flash-lite",
    "gemini-1.5-flash": "gemini/gemini-3.5-flash-lite",
}
resolved_model = DEPRECATED_MODELS.get(raw_model, raw_model)
if not resolved_model.startswith("gemini/"):
    resolved_model = f"gemini/{resolved_model}"

llm = LLM(
    model=resolved_model,
    api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.7,
)


# ------------------------------------------------------------- Weather tool
@tool("Weather Lookup")
def weather_tool(city: str) -> str:
    """Get the current weather and a 3-day forecast for a city (e.g. 'Goa, India')."""
    try:
        url = "https://wttr.in/" + urllib.parse.quote(city) + "?format=j1"
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode())

        now = data["current_condition"][0]
        lines = [
            f"Current weather in {city}: {now['weatherDesc'][0]['value']}, "
            f"{now['temp_C']}°C (feels like {now['FeelsLikeC']}°C), "
            f"humidity {now['humidity']}%, wind {now['windspeedKmph']} km/h."
        ]
        for day in data["weather"]:
            lines.append(
                f"{day['date']}: min {day['mintempC']}°C, max {day['maxtempC']}°C, "
                f"{day['hourly'][4]['weatherDesc'][0]['value']}"
            )
        return "\n".join(lines)
    except Exception as error:
        return f"Weather data unavailable ({error}). Use typical seasonal climate knowledge instead."


# ------------------------------------------------------------------- Agents
destination_advisor = Agent(
    role="Destination Advisor",
    goal="Analyze the traveler's preferences and recommend the most suitable destinations, "
         "explaining clearly why each one matches their interests.",
    backstory="You are a well-travelled consultant with 15 years of experience matching "
              "travelers to places they love. You listen carefully to interests, budget and "
              "season, and you always justify your recommendations.",
    llm=llm,
    verbose=True,
    allow_delegation=False,
)

itinerary_planner = Agent(
    role="Itinerary Planner",
    goal="Create a practical day-wise itinerary with attractions and activities, "
         "organized into an efficient route that avoids wasted travel time.",
    backstory="You are a professional trip designer who plans smooth, realistic schedules. "
              "You group nearby places together, balance busy and relaxed days, and keep "
              "opening hours and travel time in mind.",
    llm=llm,
    verbose=True,
    allow_delegation=False,
)

budget_planner = Agent(
    role="Budget Planner",
    goal="Estimate travel, accommodation, food and activity costs, split the budget into "
         "categories, and suggest smart ways to save money.",
    backstory="You are a travel finance expert who builds realistic budgets and knows "
              "plenty of money-saving tricks without ruining the experience.",
    llm=llm,
    verbose=True,
    allow_delegation=False,
)

safety_guide = Agent(
    role="Travel Safety and Guide Agent",
    goal="Retrieve weather information, suggest clothing and packing items, give safety "
         "tips, and highlight important local travel considerations.",
    backstory="You are an experienced travel guide and safety consultant. You help "
              "travelers prepare for weather, local customs, scams, health and emergencies.",
    llm=llm,
    tools=[weather_tool],
    verbose=True,
    allow_delegation=False,
)
