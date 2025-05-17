import streamlit as st
import requests
import json
from typing import Optional
import uuid
import os
from streamlit_app import main
import logging

logging.basicConfig(level=logging.INFO)

# Constants for production
API_URL = os.environ.get("API_URL", "https://support-assistant.onrender.com/api/v1")
DEMO_TOKEN = os.environ.get("DEMO_TOKEN", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkZW1vX3VzZXIiLCJyb2xlIjoiZ2FtZXIifQ.8qPWSSvIY7TfRjd0pc-oYKbpodM6wPVSbI_O_Y9jD20")

# Configure page
st.set_page_config(
    page_title="KGen AI Support Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

def get_support_response(query: str, conversation_history=None) -> dict:
    """Send query to support API and return response"""
    headers = {
        "Authorization": f"Bearer {DEMO_TOKEN}",
        "Content-Type": "application/json"
    }
    url = f"{API_URL}/support/query"
    
    # Prepare the request payload
    payload = {"text": query}
    
    # Add conversation history if provided and it's an escalation request
    if conversation_history and query.lower().startswith("escalate:"):
        payload["conversation_history"] = conversation_history
        
    logging.info(f"Requesting: {url} with headers={headers} and data={payload}")
    
    response = requests.post(
        url,
        headers=headers,
        json=payload
    )
    logging.info(f"Response status: {response.status_code}, text: {response.text}")
    try:
        return response.json()
    except Exception as e:
        st.error(f"API error: {e}\nRaw response: {response.text}")
        logging.error(f"API error: {e}\nRaw response: {response.text}")
        return {}

def submit_feedback(query_id: str, feedback_type: str, comment: Optional[str] = None) -> dict:
    """Submit feedback for a query response"""
    headers = {
        "Authorization": f"Bearer {DEMO_TOKEN}",
        "Content-Type": "application/json"
    }
    url = f"{API_URL}/feedback"
    logging.info(f"Submitting feedback: {url} with headers={headers} and data={{'query_id': query_id, 'feedback_type': feedback_type, 'comment': comment}}")
    response = requests.post(
        url,
        headers=headers,
        json={"query_id": query_id, "feedback_type": feedback_type, "comment": comment}
    )
    logging.info(f"Feedback response status: {response.status_code}, text: {response.text}")
    try:
        return response.json()
    except Exception as e:
        st.error(f"API error: {e}\nRaw response: {response.text}")
        logging.error(f"API error: {e}\nRaw response: {response.text}")
        return {}

# Custom styles
st.markdown("""
<style>
    .reportview-container {
        background-color: #f0f2f6;
    }
    .sidebar .sidebar-content {
        background-color: #262730;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    main() 