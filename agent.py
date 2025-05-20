from agents import Agent, ModelSettings
from dotenv import load_dotenv

from prompts import calendar_agent_prompt 
from calendar_tools import create_google_calendar_event, cancel_calendar_event, update_calendar_event, list_calendar_events

load_dotenv()

calendar_agent_instructions_text = calendar_agent_prompt

calendar_agent = Agent(
    name="Google Calendar Agent",
    instructions=calendar_agent_instructions_text,
    model="gpt-4o-mini", 
    tools=[create_google_calendar_event, cancel_calendar_event, list_calendar_events, update_calendar_event],
    model_settings=ModelSettings(
        tool_choice="auto",
        temperature=0.2, 
    )
)

if __name__ == '__main__':
    print("Google Calendar Agent definition loaded.")
    print(f"Agent Name: {calendar_agent.name}")
    print(f"Instructions: {calendar_agent.instructions[:100]}...") # Print first 100 chars of instructions
    if calendar_agent.tools:
        print(f"Tools configured: {[tool.name for tool in calendar_agent.tools]}")
    else:
        print("No tools configured for this agent.")