import asyncio
import os
import sys
from datetime import date
from pathlib import Path

# Safeguard against Windows permission issues with CrewAI credentials cache
if sys.platform == "win32":
    local_crew_dir = Path(__file__).resolve().parent / ".crewai_data"
    local_crew_dir.mkdir(parents=True, exist_ok=True)
    try:
        appdata = os.environ.get("LOCALAPPDATA")
        test_path = Path(appdata) / "crewai" / "credentials"
        test_path.mkdir(parents=True, exist_ok=True)
    except Exception:
        os.environ["LOCALAPPDATA"] = str(local_crew_dir)

import chainlit as cl
from crewai import Crew, Process
from dotenv import load_dotenv

from tasks import get_fresh_tasks_and_agents

load_dotenv(override=True)

REPORT_FILE = "travel_report.md"

PRESETS = {
    "preset_goa": {
        "title": "🌴 Goa Beach & Food Explorer",
        "inputs": {
            "start_location": "Mumbai",
            "destination": "Goa",
            "dates": "10 Dec - 15 Dec 2026",
            "days": "5",
            "budget": "50,000 INR",
            "interests": "beaches, coastal cuisine, historic forts, sunset cafes",
        },
    },
    "preset_rajasthan": {
        "title": "🏰 Royal Rajasthan Cultural Journey",
        "inputs": {
            "start_location": "New Delhi",
            "destination": "Jaipur & Udaipur",
            "dates": "15 Jan - 19 Jan 2027",
            "days": "4",
            "budget": "45,000 INR",
            "interests": "royal palaces, Rajasthani thali, folk music, heritage bazaars",
        },
    },
    "preset_manali": {
        "title": "🏔️ Himachal Mountain Escape",
        "inputs": {
            "start_location": "Chandigarh",
            "destination": "Manali & Solang Valley",
            "dates": "20 Feb - 25 Feb 2027",
            "days": "5",
            "budget": "35,000 INR",
            "interests": "snow views, mountain cafes, easy treks, river walks, local trout",
        },
    },
    "preset_japan": {
        "title": "🌸 Japan Golden Route (Tokyo & Kyoto)",
        "inputs": {
            "start_location": "Singapore",
            "destination": "Tokyo & Kyoto, Japan",
            "dates": "28 Mar - 03 Apr 2027",
            "days": "6",
            "budget": "$2,200 USD",
            "interests": "cherry blossoms, authentic ramen, historic shrines, modern tech",
        },
    },
}


# ==============================================================================
# Helper to render the initial welcome hero card
# ==============================================================================
async def show_welcome_screen():
    welcome_html = """
<div class="hero-container">
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px;">
        <div>
            <h1 style="font-size: 2.2rem; font-weight: 800; margin: 0; background: linear-gradient(135deg, #38bdf8, #818cf8, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                ✈️ WanderAI | Intelligent Travel Crew
            </h1>
            <p style="font-size: 1.05rem; color: #94a3b8; margin-top: 6px; margin-bottom: 0;">
                Autonomous multi-agent travel intelligence system powered by <strong>CrewAI</strong> & <strong>Google Gemini</strong>.
            </p>
        </div>
        <div style="background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.3); padding: 8px 16px; border-radius: 9999px; font-size: 0.85rem; color: #38bdf8; font-weight: 600;">
            4 Specialist Agents Active
        </div>
    </div>

    <div class="hero-grid">
        <div class="hero-card" style="border-top: 3px solid #34d399;">
            <div style="font-size: 1.3rem; margin-bottom: 6px;">🧭 <strong>Destination Advisor</strong></div>
            <div style="font-size: 0.88rem; color: #94a3b8; line-height: 1.5;">
                Analyzes budget, dates, and passions to recommend ideal destination matches with alternatives.
            </div>
        </div>

        <div class="hero-card" style="border-top: 3px solid #38bdf8;">
            <div style="font-size: 1.3rem; margin-bottom: 6px;">🗺️ <strong>Itinerary Planner</strong></div>
            <div style="font-size: 0.88rem; color: #94a3b8; line-height: 1.5;">
                Constructs a logical day-wise schedule with morning, afternoon & evening activities to minimize transit.
            </div>
        </div>

        <div class="hero-card" style="border-top: 3px solid #fbbf24;">
            <div style="font-size: 1.3rem; margin-bottom: 6px;">💰 <strong>Budget Planner</strong></div>
            <div style="font-size: 0.88rem; color: #94a3b8; line-height: 1.5;">
                Breaks down transport, lodging, food, and activities into itemized tables with smart money-saving hacks.
            </div>
        </div>

        <div class="hero-card" style="border-top: 3px solid #c084fc;">
            <div style="font-size: 1.3rem; margin-bottom: 6px;">🛡️ <strong>Safety & Guide Agent</strong></div>
            <div style="font-size: 0.88rem; color: #94a3b8; line-height: 1.5;">
                Queries live weather via <code>wttr.in</code>, offers local cultural tips, scams to avoid, and packing checklists.
            </div>
        </div>
    </div>
</div>
"""
    actions = [
        cl.Action(name="preset_goa", payload={"key": "preset_goa"}, label="🌴 Goa Beach (5 Days)"),
        cl.Action(name="preset_rajasthan", payload={"key": "preset_rajasthan"}, label="🏰 Rajasthan (4 Days)"),
        cl.Action(name="preset_manali", payload={"key": "preset_manali"}, label="🏔️ Manali (5 Days)"),
        cl.Action(name="preset_japan", payload={"key": "preset_japan"}, label="🌸 Japan (6 Days)"),
        cl.Action(name="custom_trip", payload={"key": "custom"}, label="✍️ Plan Custom Trip"),
    ]

    await cl.Message(
        content=welcome_html,
        actions=actions,
    ).send()


# ==============================================================================
# Chat Lifecycle Handlers
# ==============================================================================
@cl.on_chat_start
async def on_chat_start():
    await show_welcome_screen()


@cl.action_callback("preset_goa")
async def on_preset_goa(action: cl.Action):
    await action.remove()
    await start_planning(PRESETS["preset_goa"]["inputs"], title=PRESETS["preset_goa"]["title"])


@cl.action_callback("preset_rajasthan")
async def on_preset_rajasthan(action: cl.Action):
    await action.remove()
    await start_planning(PRESETS["preset_rajasthan"]["inputs"], title=PRESETS["preset_rajasthan"]["title"])


@cl.action_callback("preset_manali")
async def on_preset_manali(action: cl.Action):
    await action.remove()
    await start_planning(PRESETS["preset_manali"]["inputs"], title=PRESETS["preset_manali"]["title"])


@cl.action_callback("preset_japan")
async def on_preset_japan(action: cl.Action):
    await action.remove()
    await start_planning(PRESETS["preset_japan"]["inputs"], title=PRESETS["preset_japan"]["title"])


@cl.action_callback("custom_trip")
async def on_custom_trip(action: cl.Action):
    await action.remove()
    await prompt_custom_trip()


@cl.action_callback("plan_another")
async def on_plan_another(action: cl.Action):
    await action.remove()
    await show_welcome_screen()


async def prompt_custom_trip():
    guide_msg = """
### ✍️ Plan Your Custom Trip
Please share your trip details by replying to this message. You can paste them in one message or formatted like this:

- **Starting Location:** Mumbai
- **Destination:** Kerala (or "open" for suggestions)
- **Dates:** 15 Jan - 20 Jan 2027
- **Days:** 5
- **Budget:** 40,000 INR
- **Interests:** backwaters, beaches, authentic cuisine, nature

*(Or simply write: "Plan a 4-day trip from Bangalore to Ooty with a 25000 INR budget focused on tea gardens and quiet scenery")*
"""
    await cl.Message(content=guide_msg).send()


# ==============================================================================
# Freeform Input Parser
# ==============================================================================
@cl.on_message
async def on_message(message: cl.Message):
    text = message.content.strip()

    # Parse simple key-value patterns if available
    lines = text.splitlines()
    data = {}
    for line in lines:
        if ":" in line:
            key, val = line.split(":", 1)
            k = key.strip().lower().replace("-", "").replace("*", "")
            v = val.strip().replace("*", "")
            if "start" in k or "from" in k:
                data["start_location"] = v
            elif "dest" in k or "to" in k:
                data["destination"] = v
            elif "date" in k:
                data["dates"] = v
            elif "day" in k:
                # extract digits
                digits = "".join([c for c in v if c.isdigit()])
                data["days"] = digits or "5"
            elif "budget" in k:
                data["budget"] = v
            elif "interest" in k or "prefer" in k:
                data["interests"] = v

    # Fallback to sensible defaults or interactive prompts if incomplete
    inputs = {
        "start_location": data.get("start_location") or "New Delhi",
        "destination": data.get("destination") or "open",
        "dates": data.get("dates") or "Next Month",
        "days": data.get("days") or "5",
        "budget": data.get("budget") or "50,000 INR",
        "interests": data.get("interests") or text,
    }

    # If the user literally just typed a destination or natural sentence:
    if len(data) < 2:
        inputs["interests"] = text
        inputs["destination"] = text

    await start_planning(inputs, title=f"🗺️ Custom Journey: {inputs['destination']}")


# ==============================================================================
# Crew Execution with Live Chainlit Steps & Thought Tracking
# ==============================================================================
async def start_planning(inputs: dict, title: str = "Custom Trip"):
    # Display the trip parameter card
    param_summary = f"""
<div class="agent-card">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
        <h3 style="margin: 0; font-size: 1.4rem; color: #f8fafc;">{title}</h3>
        <span class="agent-badge badge-destination">🚀 Initializing AI Crew</span>
    </div>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; font-size: 0.95rem;">
        <div>📍 <strong>From:</strong> <span style="color: #cbd5e1;">{inputs.get('start_location', 'N/A')}</span></div>
        <div>🎯 <strong>Destination:</strong> <span style="color: #cbd5e1;">{inputs.get('destination', 'open')}</span></div>
        <div>📅 <strong>Dates:</strong> <span style="color: #cbd5e1;">{inputs.get('dates', 'N/A')} ({inputs.get('days', '5')} days)</span></div>
        <div>💵 <strong>Budget:</strong> <span style="color: #cbd5e1;">{inputs.get('budget', 'N/A')}</span></div>
    </div>
    <div style="margin-top: 12px; font-size: 0.95rem;">
        🎨 <strong>Interests:</strong> <span style="color: #cbd5e1;">{inputs.get('interests', 'N/A')}</span>
    </div>
</div>
"""
    await cl.Message(content=param_summary).send()

    # Communication queue between synchronous CrewAI thread and asynchronous Chainlit event loop
    event_queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    # Step callback triggered on agent cognitive actions and tool calls
    def crew_step_callback(step_output):
        try:
            thought = getattr(step_output, "thought", "")
            tool = getattr(step_output, "tool", None)
            tool_input = getattr(step_output, "tool_input", None)
            result = getattr(step_output, "result", None)
            text = getattr(step_output, "text", "")

            event = {
                "type": "step",
                "thought": thought,
                "tool": tool,
                "tool_input": tool_input,
                "result": result,
                "text": text,
            }
            loop.call_soon_threadsafe(event_queue.put_nowait, event)
        except Exception as e:
            print("Step callback error:", e)

    # Task callback triggered when an agent finalizes its assignment
    def crew_task_callback(task_output):
        try:
            event = {
                "type": "task_done",
                "agent": getattr(task_output, "agent", "Agent"),
                "raw": getattr(task_output, "raw", ""),
                "description": getattr(task_output, "description", ""),
            }
            loop.call_soon_threadsafe(event_queue.put_nowait, event)
        except Exception as e:
            print("Task callback error:", e)

    # Instantiate fresh tasks and agents for this run
    tasks, agents = get_fresh_tasks_and_agents()

    crew = Crew(
        agents=agents,
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
        step_callback=crew_step_callback,
        task_callback=crew_task_callback,
    )

    # Agent UI tracking state
    agent_metadata = {
        "Destination Advisor": {
            "icon": "🧭",
            "name": "Destination Advisor",
            "badge_class": "badge-destination",
            "desc": "Analyzing destination matches, seasonal suitability & alternatives",
        },
        "Itinerary Planner": {
            "icon": "🗺️",
            "name": "Itinerary Planner",
            "badge_class": "badge-itinerary",
            "desc": "Formulating day-by-day balanced route & activity timetable",
        },
        "Budget Planner": {
            "icon": "💰",
            "name": "Budget Planner",
            "badge_class": "badge-budget",
            "desc": "Calculating cost breakdowns & practical money-saving strategies",
        },
        "Travel Safety and Guide Agent": {
            "icon": "🛡️",
            "name": "Safety & Guide Agent",
            "badge_class": "badge-safety",
            "desc": "Checking real-time weather, safety protocols & packing items",
        },
    }

    # Queue consumer task that updates Chainlit steps and displays thinking processes live
    async def consumer():
        active_step = None
        current_agent_name = "Destination Advisor"

        # Initialize first agent step
        active_step = cl.Step(name=f"🧭 Destination Advisor: Researching Options", type="run")
        await active_step.send()

        while True:
            event = await event_queue.get()
            if event is None:
                # Sentinel to terminate consumer
                if active_step:
                    await active_step.update()
                break

            etype = event.get("type")

            if etype == "step":
                thought = event.get("thought")
                tool = event.get("tool")
                tool_input = event.get("tool_input")
                result = event.get("result")

                # If the agent engaged in an internal reasoning/thought step:
                if thought and active_step:
                    thought_step = cl.Step(
                        name="🧠 Thought Process",
                        type="tool",
                        parent_id=active_step.id,
                    )
                    thought_step.output = f"```text\n{thought.strip()}\n```"
                    await thought_step.send()

                # If the agent invoked a tool (e.g. Weather Lookup):
                if tool and active_step:
                    tool_step = cl.Step(
                        name=f"🛠️ Tool: {tool}",
                        type="tool",
                        parent_id=active_step.id,
                    )
                    tool_step.input = str(tool_input)
                    tool_step.output = str(result) if result else "Fetching data..."
                    await tool_step.send()

            elif etype == "task_done":
                agent_raw = event.get("agent", "")
                raw_text = event.get("raw", "")

                # Match agent metadata
                meta = agent_metadata.get(agent_raw)
                if not meta:
                    for k, v in agent_metadata.items():
                        if k.lower() in agent_raw.lower() or agent_raw.lower() in k.lower():
                            meta = v
                            break
                if not meta:
                    meta = {
                        "icon": "🤖",
                        "name": agent_raw,
                        "badge_class": "badge-itinerary",
                        "desc": "Agent Task Finished",
                    }

                # Finalize the current active step
                if active_step:
                    active_step.output = f"✅ Completed assignment successfully."
                    await active_step.update()

                # Post a beautifully formatted card in the main feed
                card_html = f"""
<div class="agent-card">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
        <div style="font-size: 1.25rem; font-weight: 700; color: #f8fafc;">
            {meta['icon']} {meta['name']}
        </div>
        <span class="agent-badge {meta['badge_class']}">Completed</span>
    </div>
    <div style="font-size: 0.9rem; color: #94a3b8; margin-bottom: 16px;">
        {meta['desc']}
    </div>
    <div style="background: rgba(15, 23, 42, 0.5); border-radius: 10px; padding: 18px; border: 1px solid rgba(255, 255, 255, 0.06); font-size: 0.95rem; line-height: 1.6;">
        {raw_text}
    </div>
</div>
"""
                await cl.Message(content=card_html).send()

                # Determine and start the next agent step if not finished
                if "Destination Advisor" in meta["name"]:
                    current_agent_name = "Itinerary Planner"
                    active_step = cl.Step(name=f"🗺️ Itinerary Planner: Designing Schedule", type="run")
                    await active_step.send()
                elif "Itinerary Planner" in meta["name"]:
                    current_agent_name = "Budget Planner"
                    active_step = cl.Step(name=f"💰 Budget Planner: Calculating Expenses", type="run")
                    await active_step.send()
                elif "Budget Planner" in meta["name"]:
                    current_agent_name = "Safety & Guide Agent"
                    active_step = cl.Step(name=f"🛡️ Safety & Guide Agent: Checking Weather & Tips", type="run")
                    await active_step.send()
                else:
                    active_step = None

    # Run consumer in the background
    consumer_task = asyncio.create_task(consumer())

    # Kickoff the Crew in a worker thread to keep the Chainlit UI completely responsive
    try:
        result = await asyncio.to_thread(crew.kickoff, inputs=inputs)
    except Exception as err:
        await event_queue.put(None)
        await consumer_task
        await cl.Message(
            content=f"❌ **Something went wrong while running the agents:**\n```\n{err}\n```"
        ).send()
        return

    # Notify consumer of completion and await its cleanup
    await event_queue.put(None)
    await consumer_task

    # Build the final comprehensive travel report
    report_content = (
        "# ✈️ Complete Travel Itinerary & Safety Report\n\n"
        f"- **Starting Point:** {inputs.get('start_location', 'N/A')}\n"
        f"- **Destination:** {inputs.get('destination', 'N/A')}\n"
        f"- **Travel Dates:** {inputs.get('dates', 'N/A')} ({inputs.get('days', '5')} days)\n"
        f"- **Budget:** {inputs.get('budget', 'N/A')}\n"
        f"- **Interests:** {inputs.get('interests', 'N/A')}\n"
        f"- **Generated On:** {date.today()}\n\n---\n\n"
    )

    section_titles = [
        "Destination Recommendations",
        "Day-wise Detailed Itinerary",
        "Estimated Budget Breakdown",
        "Weather, Travel Tips & Packing Checklist",
    ]

    for i, title in enumerate(section_titles):
        if i < len(result.tasks_output):
            out_raw = result.tasks_output[i].raw
            report_content += f"## {title}\n\n{out_raw}\n\n---\n\n"

    # Save to disk
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report_content)

    # Attach file for user download
    download_element = cl.File(
        name="travel_report.md",
        path=REPORT_FILE,
        display="inline",
    )

    final_msg = f"""
<div class="agent-card" style="border: 2px solid rgba(56, 189, 248, 0.4); background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.9));">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <h2 style="margin: 0; color: #38bdf8;">🎉 Trip Planning Complete!</h2>
        <span class="agent-badge badge-destination">Report Ready</span>
    </div>
    <p style="color: #94a3b8; font-size: 1rem; margin-top: 8px;">
        All 4 agents have successfully collaborated and finalized your custom travel package. You can review the details above or download the markdown report below.
    </p>
</div>
"""
    await cl.Message(
        content=final_msg,
        elements=[download_element],
        actions=[
            cl.Action(name="plan_another", payload={"key": "another"}, label="🔄 Plan Another Trip")
        ],
    ).send()
