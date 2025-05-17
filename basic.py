
import os
from dotenv import load_dotenv
load_dotenv()

import anthropic
anthropic.api_key = os.getenv("ANTHROPIC_API_KEY")

client = anthropic.Anthropic()

message = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=1000,
    temperature=1,
    system="You are a helpful receptionist. Answer only with short sentences in a professional manner.",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Can you schedule an appointment for me?"
                }
            ]
        }
    ]
)

print(message.content)