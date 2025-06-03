import os
import uuid
import asyncio
from typing import Any, List, Dict
from dotenv import load_dotenv

from prompts import calendar_agent_prompt
from tools import schedule_event, reschedule_event, cancel_event, list_event

from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel
from pydantic_ai.tools import Tool, ToolDefinition
from supabase import create_client, Client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") 

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Generate a single chat_id for the entire session
SESSION_CHAT_ID = str(uuid.uuid4())
chat_history: Any | None = None 
    
def insert_to_db(user_input: str, agent_output: str):
    try:
        supabase.table("chat").insert({
            "chat_id": SESSION_CHAT_ID, 
            "message": user_input, 
            "response": agent_output
        }).execute()
    except Exception as e:
        print(f"Error inserting to Supabase: {e}")

# Initialize the test model for logging tool calls
test_model = TestModel()

# Initialize Agent with the test model
calendar_agent = Agent(
    test_model,
    system_prompt=calendar_agent_prompt,
    tools=[schedule_event, reschedule_event, cancel_event, list_event]
    )

async def process_chat(user_input: str, current_history = Any | None) -> Any | None:
    global chat_history
    agent_output = await calendar_agent.run(user_input, message_history=current_history)
    insert_to_db(user_input, agent_output.output)
    chat_history = agent_output.all_messages()
    
    # Print the agent's response
    print(agent_output.output)
    
    # Print the tool calls that were made
    print("\nTool calls made:")
    print(test_model.last_model_request_parameters.function_tools)
    
    return chat_history

if __name__ == '__main__':
    print(f"Starting new chat session. Session ID: {SESSION_CHAT_ID}")
    print("How can I help you with your scheduling?")
    
    while True:
        user_input = input("-> ")
        asyncio.run(process_chat(user_input, chat_history))
        # I want to schedule an appointment tomorrow for 1pm with Dr. Kohan for tooth pain.