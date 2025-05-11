import streamlit as st
import requests
import json
from typing import Optional
import uuid
import os

# Constants for production
API_URL = os.environ.get("API_URL", "https://support-assistant.onrender.com")
DEMO_TOKEN = os.environ.get("DEMO_TOKEN", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkZW1vX3VzZXIiLCJyb2xlIjoiZ2FtZXIifQ.8qPWSSvIY7TfRjd0pc-oYKbpodM6wPVSbI_O_Y9jD20")

# Configure page
st.set_page_config(
    page_title="KGen AI Support Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

def get_support_response(query: str) -> dict:
    """Send query to support API and return response"""
    headers = {
        "Authorization": f"Bearer {DEMO_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.post(
        f"{API_URL}/support/query",
        headers=headers,
        json={"text": query}
    )
    return response.json()

def submit_feedback(query_id: str, feedback_type: str, comment: Optional[str] = None) -> dict:
    """Submit feedback for a query response"""
    headers = {
        "Authorization": f"Bearer {DEMO_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.post(
        f"{API_URL}/feedback",
        headers=headers,
        json={"query_id": query_id, "feedback_type": feedback_type, "comment": comment}
    )
    return response.json()

# Use same main function as the local app
from streamlit_app import main

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

def main():
    st.write("Streamlit version:", st.__version__)
    # ... existing code ...

if __name__ == "__main__":
    main() 