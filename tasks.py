from crewai import Task

from agents import budget_planner, destination_advisor, itinerary_planner, safety_guide

# {placeholders} are filled in from the user's input when the crew starts.
# Agents are told not to write their own top-level title, because main.py adds
# the section headings when it builds travel_report.md.

destination_task = Task(
    description=(
        "Traveler details:\n"
        "- Starting location: {start_location}\n"
        "- Destination or preferred region: {destination}\n"
        "- Travel dates: {dates}\n"
        "- Number of days: {days}\n"
        "- Total budget: {budget}\n"
        "- Interests: {interests}\n\n"
        "If the traveler named a specific destination, confirm it is a good fit and "
        "summarize it, plus mention 1-2 alternatives. If they gave only a region or "
        "said they are open to suggestions, recommend 3 destinations within it. "
        "For every destination, explain why it matches their interests, budget and "
        "travel dates. End with a clearly labelled line 'TOP PICK: <destination>', "
        "because the next agents will plan the trip for that place."
    ),
    expected_output=(
        "A destination summary with reasons for each destination, ending with "
        "'TOP PICK: <destination>'."
    ),
    agent=destination_advisor,
)

itinerary_task = Task(
    description=(
        "Using the TOP PICK destination from the previous task, create a day-wise "
        "itinerary for {days} days, travelling from {start_location} on {dates}. "
        "Focus on these interests: {interests}. For each day include morning, "
        "afternoon and evening activities, recommended attractions, and group nearby "
        "places together so the route is practical. Mention approximate travel time "
        "between places. Use '### Day 1', '### Day 2', ... as headings."
    ),
    expected_output="A day-by-day itinerary (Day 1, Day 2, ...) with a logical route.",
    agent=itinerary_planner,
    context=[destination_task],
)

budget_task = Task(
    description=(
        "Using the destination and itinerary from the previous tasks, estimate the "
        "total trip cost against a budget of {budget}, travelling from {start_location}. "
        "Break it into: travel (to/from {start_location} plus local transport), "
        "accommodation, food, activities and miscellaneous. Present a markdown table "
        "with category, estimated cost and notes, then show the total and whether it "
        "fits the budget. Finish with practical tips to reduce expenses."
    ),
    expected_output=(
        "A markdown budget breakdown table with a total, and a list of money-saving tips."
    ),
    agent=budget_planner,
    context=[destination_task, itinerary_task],
)

safety_task = Task(
    description=(
        "For the TOP PICK destination, use the Weather Lookup tool to get the weather. "
        "Combine it with the typical climate for the travel dates: {dates}. "
        "Write your answer in EXACTLY these three markdown sections, using these headings:\n"
        "### Weather Information  (current weather, expected conditions for the dates)\n"
        "### Travel Tips  (safety tips plus local considerations: customs, etiquette, "
        "language, currency, local transport, scams to avoid, emergency basics)\n"
        "### Packing Checklist  (clothing and essentials as a markdown checklist using "
        "'- [ ] item', grouped under Clothing, Documents, Electronics, Health, Misc)"
    ),
    expected_output=(
        "Three sections: Weather Information, Travel Tips, and Packing Checklist."
    ),
    agent=safety_guide,
    context=[destination_task, itinerary_task],
)

# Order matters: the crew runs these one after another (Process.sequential).
all_tasks = [destination_task, itinerary_task, budget_task, safety_task]
all_agents = [destination_advisor, itinerary_planner, budget_planner, safety_guide]


def get_fresh_tasks_and_agents():
    """Returns fresh Task instances for multi-run environments like web UIs."""
    t1 = Task(
        description=destination_task.description,
        expected_output=destination_task.expected_output,
        agent=destination_advisor,
    )
    t2 = Task(
        description=itinerary_task.description,
        expected_output=itinerary_task.expected_output,
        agent=itinerary_planner,
        context=[t1],
    )
    t3 = Task(
        description=budget_task.description,
        expected_output=budget_task.expected_output,
        agent=budget_planner,
        context=[t1, t2],
    )
    t4 = Task(
        description=safety_task.description,
        expected_output=safety_task.expected_output,
        agent=safety_guide,
        context=[t1, t2],
    )
    return [t1, t2, t3, t4], [destination_advisor, itinerary_planner, budget_planner, safety_guide]

