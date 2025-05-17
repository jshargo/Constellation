import os
import json
from dotenv import load_dotenv
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime

import anthropic
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

# Initialize Anthropic client
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
if not anthropic_api_key:
    raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

client = anthropic.Anthropic(api_key=anthropic_api_key)


# --------------------------------------------------------------
# Step 1: Define the data models
# --------------------------------------------------------------

class SpeakerTurn(BaseModel):
    speaker: str
    text: str

class CallMetadata(BaseModel):
    caller_number: str
    clinic_id: str

class PayloadData(BaseModel):
    call_id: str
    timestamp: str
    speaker_turns: List[SpeakerTurn]
    metadata: CallMetadata

class AppointmentRequest(BaseModel):
    intent: Literal["Schedule Appointment", "Reschedule Appointment", "Cancel Appointment", "Information Request"]
    patient_name: Optional[str] = None
    requested_date: Optional[str] = None
    requested_time: Optional[str] = None
    reason_for_visit: Optional[str] = None
    urgency_level: Optional[Literal["Low", "Medium", "High"]] = None
    additional_notes: Optional[str] = None
    call_id: str
    caller_number: str
    clinic_id: str


# --------------------------------------------------------------
# Step 2: Function to process appointment requests
# --------------------------------------------------------------

def load_payload(file_path: str) -> PayloadData:
    """Load and parse the payload from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            return PayloadData(**data)
    except Exception as e:
        print(f"Error loading payload: {e}")
        raise

def extract_conversation_text(payload: PayloadData) -> str:
    """Extract the conversation text from the payload."""
    conversation = ""
    for turn in payload.speaker_turns:
        conversation += f"{turn.speaker}: {turn.text}\n"
    return conversation

def process_appointment_request(payload_path: str) -> AppointmentRequest:
    """Process an appointment request using Anthropic's Claude model with structured output."""
    
    # Load the payload data
    payload = load_payload(payload_path)
    
    # Extract conversation text
    conversation_text = extract_conversation_text(payload)
    
    # Define the system prompt for appointment processing
    system_prompt = """
    You are an AI assistant that helps process appointment requests for a medical clinic.
    Extract key information from patient messages and classify the intent of their request.
    
    For each request, identify:
    1. The primary intent (Schedule Appointment, Reschedule Appointment, Cancel Appointment, or Information Request)
    2. Patient name (if provided)
    3. Requested date and time (if provided)
    4. Reason for visit (if provided)
    5. Urgency level (Low, Medium, High) based on the content
    6. Any additional notes or special requirements
    """
    
    # Construct a prompt that explicitly asks for JSON format
    json_prompt = f"""
    Based on the following conversation, extract appointment information and return it in JSON format.
    Format your response as valid JSON only, with no additional text.
    
    Conversation:
    {conversation_text}
    
    Return a JSON object with these fields:
    - intent: one of ["Schedule Appointment", "Reschedule Appointment", "Cancel Appointment", "Information Request"]
    - patient_name: (if available)
    - requested_date: (if available)
    - requested_time: (if available)
    - reason_for_visit: (if available)
    - urgency_level: one of ["Low", "Medium", "High"] (if applicable)
    - additional_notes: (if applicable)
    """
    
    # Call Anthropic's Claude model with explicit instructions for JSON output
    completion = client.messages.create(
        model="claude-3-opus-20240229",
        system=system_prompt,
        messages=[
            {"role": "user", "content": json_prompt}
        ],
        max_tokens=1000,
        temperature=0
    )
    
    # Parse the response - Claude will return JSON-like content but we need to extract it
    response_content = completion.content[0].text
    
    # Print the raw response for debugging
    print("\nRaw model response:")
    print(response_content)
    
    # Try to parse the response as JSON directly first
    try:
        base_appointment_data = json.loads(response_content)
        json_str = response_content
    except json.JSONDecodeError:
        # If direct parsing fails, try to extract JSON from the response
        if '```json' in response_content:
            # Extract JSON from markdown code block
            json_start = response_content.find('```json') + 7
            json_end = response_content.find('```', json_start)
            json_str = response_content[json_start:json_end].strip()
        elif '```' in response_content:
            # Extract JSON from generic code block
            json_start = response_content.find('```') + 3
            json_end = response_content.find('```', json_start)
            json_str = response_content[json_start:json_end].strip()
        else:
            # Try to find JSON-like structure in the text
            json_start = response_content.find('{')
            json_end = response_content.rfind('}')
            if json_start != -1 and json_end != -1 and json_end > json_start:
                json_str = response_content[json_start:json_end+1].strip()
            else:
                # No JSON structure found
                json_str = ""
                
        print("\nExtracted JSON:")
        print(json_str)
    
    try:
        # Create base appointment data from model response
        base_appointment_data = json.loads(json_str)
        
        # Add metadata from the payload
        base_appointment_data.update({
            "call_id": payload.call_id,
            "caller_number": payload.metadata.caller_number,
            "clinic_id": payload.metadata.clinic_id
        })
        
        # Validate and return the complete appointment data
        appointment_data = AppointmentRequest(**base_appointment_data)
    except json.JSONDecodeError as e:
        print(f"Error parsing model response: {e}")
        print(f"Response content: {response_content}")
        # Fallback with default values
        appointment_data = AppointmentRequest(
            intent="Schedule Appointment",
            call_id=payload.call_id,
            caller_number=payload.metadata.caller_number,
            clinic_id=payload.metadata.clinic_id
        )
    
    return appointment_data


# --------------------------------------------------------------
# Step 3: Example usage
# --------------------------------------------------------------

# Define the path to the payload file
payload_path = "/Users/shargo/Curon/backend-test/payload.json"

# Process the request from the payload file
appointment = process_appointment_request(payload_path)

print("\nAppointment Request Details:")
print(f"Intent: {appointment.intent}")
if appointment.patient_name:
    print(f"Patient Name: {appointment.patient_name}")
if appointment.requested_date:
    print(f"Requested Date: {appointment.requested_date}")
if appointment.requested_time:
    print(f"Requested Time: {appointment.requested_time}")
if appointment.reason_for_visit:
    print(f"Reason for Visit: {appointment.reason_for_visit}")
if appointment.urgency_level:
    print(f"Urgency Level: {appointment.urgency_level}")
if appointment.additional_notes:
    print(f"Additional Notes: {appointment.additional_notes}")

print("\nMetadata:")
print(f"Call ID: {appointment.call_id}")
print(f"Caller Number: {appointment.caller_number}")
print(f"Clinic ID: {appointment.clinic_id}")