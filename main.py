import os
import sys
from datetime import date
import warnings

from crewai import Crew, Process

from tasks import all_agents, all_tasks

# ------------------------------------------------------------ Terminal UI
CYAN, GREEN, YELLOW, RED, BOLD, RESET = (
    "\033[96m", "\033[92m", "\033[93m", "\033[91m", "\033[1m", "\033[0m",
)
LINE = "=" * 64
REPORT_FILE = "travel_report.md"

warnings.filterwarnings("ignore", category=UserWarning, module="crewai")  # suppress CrewAI warnings

def banner():
    print(f"\n{CYAN}{LINE}")
    print("        AI TRAVEL PLANNER CREW  (powered by Gemini)")
    print(f"{LINE}{RESET}")
    print("  1. Destination Advisor   3. Budget Planner")
    print("  2. Itinerary Planner     4. Safety & Guide Agent")
    print(f"{CYAN}{LINE}{RESET}\n")


def ask(question, default=None, number=False):
    """Ask one question; keep asking until we get a valid answer."""
    suffix = f" [{default}]" if default else ""
    while True:
        answer = input(f"{YELLOW}> {question}{suffix}: {RESET}").strip() or (default or "")
        if not answer:
            print(f"{RED}  Please enter a value.{RESET}")
        elif number and not (answer.isdigit() and int(answer) > 0):
            print(f"{RED}  Please enter a positive number.{RESET}")
        else:
            return answer


def section(title):
    print(f"\n{GREEN}{LINE}\n  {title}\n{LINE}{RESET}\n")


# -------------------------------------------------------------------- Main
def main():
    if not os.getenv("GEMINI_API_KEY"):
        # agents.py loads .env when imported, so this check runs after that
        print(f"{RED}GEMINI_API_KEY not found. Add it to your .env file.{RESET}")
        sys.exit(1)

    banner()
    inputs = {
        "start_location": ask("Starting location"),
        "destination": ask("Destination or preferred region (or 'open' for suggestions)", default="open"),
        "dates": ask("Travel dates (e.g. 10 Dec - 15 Dec 2026)"),
        "days": ask("Number of days", default="5", number=True),
        "budget": ask("Total budget (with currency, e.g. 50000 INR)"),
        "interests": ask("Interests (e.g. beaches, history, food, trekking)"),
    }

    print(f"\n{CYAN}Your agents are working... this can take a minute or two.{RESET}\n")

    crew = Crew(
        agents=all_agents,
        tasks=all_tasks,
        process=Process.sequential,  # tasks run one after another, in order
        verbose=False,
    )

    try:
        result = crew.kickoff(inputs=inputs)
    except Exception as error:
        print(f"\n{RED}Something went wrong: {error}{RESET}")
        sys.exit(1)

    # Report sections. The 4th agent's output already contains three sections:
    # Weather Information, Travel Tips and Packing Checklist.
    sections = [
        ("Destination Summary", result.tasks_output[0].raw),
        ("Day-wise Itinerary", result.tasks_output[1].raw),
        ("Estimated Budget Breakdown", result.tasks_output[2].raw),
        (None, result.tasks_output[3].raw),
    ]

    report = (
        "# Travel Report\n\n"
        f"- **From:** {inputs['start_location']}\n"
        f"- **Destination / region:** {inputs['destination']}\n"
        f"- **Dates:** {inputs['dates']} ({inputs['days']} days)\n"
        f"- **Budget:** {inputs['budget']}\n"
        f"- **Interests:** {inputs['interests']}\n"
        f"- **Generated on:** {date.today()}\n\n---\n\n"
    )

    for title, text in sections:
        if title:
            section(title.upper())
            report += f"## {title}\n\n{text}\n\n---\n\n"
        else:
            section("WEATHER, TRAVEL TIPS & PACKING CHECKLIST")
            report += f"{text}\n"
        print(text)

    with open(REPORT_FILE, "w", encoding="utf-8") as file:
        file.write(report)
    print(f"\n{GREEN}{BOLD}Done! Your report was saved to {REPORT_FILE}{RESET}\n")


if __name__ == "__main__":
    main()
