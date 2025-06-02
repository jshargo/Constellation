import os
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime, timezone 

from pydantic_core import to_jsonable_python
from pydantic_ai import Agent
from pydantic_ai.messages import (
    ModelRequest as PydanticModelRequest,
    ModelResponse as PydanticModelResponse
)
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") 
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE_URL and SUPABASE_SERVICE_KEY (or your designated Supabase key) must be set in the .env file.")
    exit(1)

if not OPENAI_API_KEY:
    print("Error: OPENAI_API_KEY must be set in the .env file for the Agent to work.")
    exit(1)

supabase_client: Client | None = None
try:
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Successfully initialized Supabase client.")
except Exception as e:
    print(f"Error initializing Supabase client: {e}")
    exit(1)

def store_chat_history_in_supabase(messages_list: list):
    """
    Stores a list of chat messages (ModelRequest or ModelResponse objects)
    into Supabase tables 'chats' and 'chat_turns'.
    """
    if not supabase_client:
        print("Supabase client not initialized. Cannot store history.")
        return None
        
    if not messages_list:
        print("No messages to store.")
        return None

    chat_id = None
    try:
        chat_insert_payload = {
            "metadata": {
                "source": "pydantic_ai_script", 
                "script_run_time": datetime.now(timezone.utc).isoformat()
            }
        }
        chat_insert_response = supabase_client.table("chats").insert(chat_insert_payload).execute()

        if chat_insert_response.data:
            chat_id = chat_insert_response.data[0]['chat_id']
            print(f"Created new chat session with ID: {chat_id}")
        else:
            error_detail = getattr(chat_insert_response, 'error', "Unknown error during chat insertion.")
            print(f"Error creating chat session: {error_detail}")
            return None
        
    except Exception as e:
        print(f"Exception creating chat session: {e}")
        return None

    turns_inserted_count = 0
    for index, message_obj in enumerate(messages_list):
        turn_data = {
            "chat_id": chat_id,
            "turn_sequence_number": index,
        }

        if hasattr(message_obj, 'parts'):
            turn_data["parts"] = to_jsonable_python(message_obj.parts)
        else:
            print(f"Warning: Message object at index {index} (type: {type(message_obj)}) has no 'parts' attribute. Storing empty parts.")
            turn_data["parts"] = []

        if isinstance(message_obj, PydanticModelRequest):
            turn_data["turn_type"] = "ModelRequest"
            if message_obj.parts and hasattr(message_obj.parts[0], 'timestamp') and isinstance(message_obj.parts[0].timestamp, datetime):
                turn_data["event_timestamp"] = message_obj.parts[0].timestamp.isoformat()
            else:
                print(f"Warning: ModelRequest (index {index}) missing valid part timestamp. Using current UTC time.")
                turn_data["event_timestamp"] = datetime.now(timezone.utc).isoformat()
            
            turn_data["model_name"] = None
            turn_data["usage_data"] = None
            turn_data["vendor_id"] = None

        elif isinstance(message_obj, PydanticModelResponse):
            turn_data["turn_type"] = "ModelResponse"
            if hasattr(message_obj, 'timestamp') and isinstance(message_obj.timestamp, datetime):
                turn_data["event_timestamp"] = message_obj.timestamp.isoformat()
            else:
                print(f"Warning: ModelResponse (index {index}) missing valid object timestamp. Using current UTC time.")
                turn_data["event_timestamp"] = datetime.now(timezone.utc).isoformat()

            turn_data["model_name"] = getattr(message_obj, 'model_name', None)
            turn_data["vendor_id"] = getattr(message_obj, 'vendor_id', None)
            
            if hasattr(message_obj, 'usage'):
                turn_data["usage_data"] = to_jsonable_python(message_obj.usage)
            else:
                turn_data["usage_data"] = None
        else:
            print(f"Unknown message type at index {index}: {type(message_obj)}. Skipping this turn.")
            continue 

        try:
            turn_insert_response = supabase_client.table("chat_turns").insert(turn_data).execute()
            if turn_insert_response.data:
                turns_inserted_count += 1
            else:
                error_detail = getattr(turn_insert_response, 'error', f"Unknown error inserting turn {index}.")
                print(f"Error inserting chat turn {index} for chat_id {chat_id}: {error_detail}")
        except Exception as e:
            print(f"Exception inserting chat turn {index} for chat_id {chat_id}: {e}")

    print(f"Successfully stored {turns_inserted_count} turns out of {len(messages_list)} for chat_id: {chat_id}")
    
    try:
        update_payload = {"updated_at": datetime.now(timezone.utc).isoformat()}
        update_response = supabase_client.table("chats").update(update_payload).eq("chat_id", chat_id).execute()
        if not update_response.data and hasattr(update_response, 'error') and update_response.error:
             print(f"Warning: Could not update 'updated_at' for chat {chat_id}: {update_response.error}")
    except Exception as e:
        print(f"Warning: Exception while updating 'updated_at' for chat {chat_id}: {e}")

    return chat_id

agent = Agent('openai:gpt-4o', system_prompt='Be a helpful assistant.')

print("Running agent (first call)...")
result1 = agent.run_sync('Tell me a joke.')
history_step_1 = result1.all_messages()

print("Running agent (second call with history)...")
result2 = agent.run_sync(
    'Tell me a different joke.', message_history=history_step_1
)

final_chat_messages_obj = result2.all_messages()

print("\n--- Full Chat History to be Processed ---")
list_of_messages_to_store = []
if hasattr(final_chat_messages_obj, 'root') and isinstance(final_chat_messages_obj.root, list):
    list_of_messages_to_store = final_chat_messages_obj.root
elif isinstance(final_chat_messages_obj, list): # Fallback if it's already a list
    list_of_messages_to_store = final_chat_messages_obj
else: # Fallback if it's just iterable
    try:
        list_of_messages_to_store = list(final_chat_messages_obj)
    except TypeError:
        print("Error: final_chat_messages_obj is not a list, does not have .root, and is not directly iterable.")

if list_of_messages_to_store:
    print(f"Extracted {len(list_of_messages_to_store)} messages for storage.")
else:
    print("No messages extracted from final_chat_messages_obj.")


if supabase_client and list_of_messages_to_store:
    print(f"\nAttempting to store chat history in Supabase...")
    new_chat_id_result = store_chat_history_in_supabase(list_of_messages_to_store)
    if new_chat_id_result:
        print(f"Chat history storage process completed. Chat ID: {new_chat_id_result}")
    else:
        print("Failed to complete chat history storage process.")
elif not supabase_client:
    # Message already printed by the check at the top
    pass
else: # No messages
    print("No chat messages to store in Supabase.")