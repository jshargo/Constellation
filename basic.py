import os
import uuid
import asyncio
from typing import Any
from dotenv import load_dotenv

from prompts import calendar_agent_prompt

from pydantic_ai import Agent
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

# Initialize Agent
calendar_agent = Agent(
    'openai:gpt-4o', 
    system_prompt=calendar_agent_prompt
    )


async def process_chat(user_input: str, current_history = Any | None) -> Any | None:
    global chat_history
    agent_output = await calendar_agent.run(user_input, message_history=current_history)
    insert_to_db(user_input, agent_output.output)
    chat_history = agent_output.all_messages()
    print(agent_output.output)
    return chat_history

if __name__ == '__main__':
    print(f"Starting new chat session. Session ID: {SESSION_CHAT_ID}")
    print("How can I help you with your scheduling?")
    
    while True:
        user_input = input("-> ")
        asyncio.run(process_chat(user_input, chat_history))