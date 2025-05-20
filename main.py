# main.py
import asyncio
from dotenv import load_dotenv
from typing import List, Dict # For type hinting message history

from agents import Runner
from agent import calendar_agent

async def run_calendar_agent_cli_with_memory():
    load_dotenv()
    runner = Runner()

    print("Google Calendar Agent CLI (with memory)")
    print("Ask me to schedule an event (e.g., 'Schedule a meeting for tomorrow at 10 AM').")
    print("Type 'exit' or 'quit' to stop.")

    # Initialize chat history.
    # Each item is a dictionary like {"role": "user", "content": "..."} or {"role": "assistant", "content": "..."}
    # The system prompt (agent.instructions) is handled by the Agent configuration.
    chat_history: List[Dict[str, str]] = []

    while True:
        try:
            user_prompt_text = input("You: ")
            if user_prompt_text.lower() in ['exit', 'quit']:
                print("Exiting.")
                break
            if not user_prompt_text.strip():
                continue

            # Add current user's message to the history
            chat_history.append({"role": "user", "content": user_prompt_text})

            # We are now passing the entire chat_history (list of messages) as the second argument
            # to runner.run(). This assumes the `agents` library is designed to interpret
            # this as the conversational context, to be used alongside `calendar_agent.instructions`
            # (which acts as the system prompt).
            # If `runner.run()` strictly expects a single string prompt, this will error,
            # indicating the 'agents' library handles memory differently (e.g. stateful Agent objects
            # or through a Context object in a specific way not yet detailed).
            agent_response_text = await runner.run(calendar_agent, chat_history)

            if agent_response_text is not None:
                # Add assistant's response to history
                # Ensure it's a string, as LLM outputs can sometimes be other types if not handled.
                processed_response_text = str(agent_response_text)
                chat_history.append({"role": "assistant", "content": processed_response_text})
                print(f"Agent: {processed_response_text}")
            else:
                # Handle cases where the agent might not return a textual response (e.g., an error or empty)
                print("Agent: I didn't get a response. Please try again.")
                # Optionally, remove the last user message from history to prevent issues on retry
                if chat_history and chat_history[-1]["role"] == "user":
                    chat_history.pop()


        except KeyboardInterrupt:
            print("\nExiting due to user interrupt.")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            # If an error occurs, especially before the assistant responds,
            # you might want to pop the last user message to avoid polluting history.
            if chat_history and chat_history[-1]["role"] == "user":
                # For simplicity, we're not popping here, but in a robust app you might.
                pass


if __name__ == "__main__":
    try:
        asyncio.run(run_calendar_agent_cli_with_memory())
    except RuntimeError as e:
        if "cannot be called from a running event loop" in str(e):
             print("Detected running event loop. Please run this script from a context where a new loop can be started, or modify for synchronous execution if applicable.")
        else:
            # Fallback for synchronous execution if `await runner.run` was the issue or if library is sync
            print("Async execution failed or not applicable, trying a conceptual synchronous approach.")
            load_dotenv()
            runner = Runner() # Assuming Runner can be used synchronously
            print("Google Calendar Agent CLI (Sync Mode Attempt with memory)")
            print("Type 'exit' or 'quit' to stop.")
            
            chat_history_sync: List[Dict[str, str]] = []
            while True:
                user_prompt_text_sync = input("You: ")
                if user_prompt_text_sync.lower() in ['exit', 'quit']:
                    break
                if not user_prompt_text_sync.strip():
                    continue
                
                chat_history_sync.append({"role": "user", "content": user_prompt_text_sync})
                try:
                    # Assuming runner.run() is blocking if not async
                    agent_response_text_sync = runner.run(calendar_agent, chat_history_sync) 
                    
                    if agent_response_text_sync is not None:
                        processed_response_text_sync = str(agent_response_text_sync)
                        chat_history_sync.append({"role": "assistant", "content": processed_response_text_sync})
                        print(f"Agent: {processed_response_text_sync}")
                    else:
                        print("Agent: I didn't get a response (sync). Please try again.")
                        if chat_history_sync and chat_history_sync[-1]["role"] == "user":
                             chat_history_sync.pop()
                except Exception as e_sync:
                    print(f"Error in sync mode: {e_sync}")