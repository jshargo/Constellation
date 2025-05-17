import anthropic
from dotenv import load_dotenv
load_dotenv()

anthropic.api_key = "ANTHROPIC_API_KEY"
client = anthropic.Anthropic()


response = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=1024,
    system="You are a helpful receptionist. Answer only with short sentences in a professional manner.",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Can you schedule an appointment for me? I have knee pain. It would be great if it was on Tuesday at 10 A.M."
                }
            ]
        }
    ],
    tools=[appointment_tool, outbound_tool]
)

print(response)


