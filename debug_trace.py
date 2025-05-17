import requests
import json
import os
import logging
import sys
from typing import Dict, Any, Optional, List
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
API_URL = os.environ.get("API_URL", "http://localhost:8000/api/v1")
DEMO_TOKEN = os.environ.get("DEMO_TOKEN", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkZW1vX3VzZXIiLCJyb2xlIjoiZ2FtZXIifQ.8qPWSSvIY7TfRjd0pc-oYKbpodM6wPVSbI_O_Y9jD20")

def send_query(text: str, conversation_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Send a query to the API and return the response"""
    headers = {
        "Authorization": f"Bearer {DEMO_TOKEN}",
        "Content-Type": "application/json"
    }
    url = f"{API_URL}/support/query"
    
    payload = {"text": text}
    if conversation_history:
        payload["conversation_history"] = conversation_history
        logger.info(f"Sending {len(conversation_history)} messages in history")
    
    logger.info(f"Sending query: {text}")
    response = requests.post(
        url,
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"API error: {response.status_code} - {response.text}")
        return {"error": response.text}

def test_trace_continuity():
    """Test trace continuity by sending sequential queries and tracking metadata"""
    logger.info("Starting trace continuity test...")
    
    # First query - no conversation history
    logger.info("Step 1: Sending initial query")
    response1 = send_query("What are legendary items?")
    
    if "error" in response1:
        logger.error("Initial query failed, aborting test")
        return
    
    query_id1 = response1.get("query_id", "")
    run_id1 = response1.get("metadata", {}).get("run_id", "")
    
    logger.info(f"First response: query_id={query_id1}, run_id={run_id1}")
    logger.info(f"Answer: {response1.get('answer', '')[:100]}...")
    
    # Build conversation history from first interaction
    conversation_history = [
        {
            "type": "user",
            "content": "What are legendary items?",
            "metadata": {}
        },
        {
            "type": "assistant",
            "content": response1.get("answer", ""),
            "metadata": {"run_id": run_id1, "query_id": query_id1}
        }
    ]
    
    # Second query - with conversation history
    logger.info("\nStep 2: Sending follow-up query with conversation history")
    response2 = send_query("Are they difficult to obtain?", conversation_history)
    
    if "error" in response2:
        logger.error("Follow-up query failed")
        return
    
    query_id2 = response2.get("query_id", "")
    run_id2 = response2.get("metadata", {}).get("run_id", "")
    parent_run_id2 = response2.get("metadata", {}).get("parent_run_id", "")
    
    logger.info(f"Second response: query_id={query_id2}, run_id={run_id2}, parent_run_id={parent_run_id2}")
    logger.info(f"Answer: {response2.get('answer', '')[:100]}...")
    
    # Check if trace continuity was maintained
    if parent_run_id2 and (parent_run_id2 == run_id1 or parent_run_id2 == query_id1):
        logger.info("✅ Trace continuity MAINTAINED between queries")
    else:
        logger.error("❌ Trace continuity BROKEN between queries")
        logger.error(f"  First run_id: {run_id1}")
        logger.error(f"  Second parent_run_id: {parent_run_id2}")
    
    # Add second interaction to conversation history
    conversation_history.append({
        "type": "user",
        "content": "Are they difficult to obtain?",
        "metadata": {}
    })
    
    conversation_history.append({
        "type": "assistant",
        "content": response2.get("answer", ""),
        "metadata": {"run_id": run_id2, "query_id": query_id2}
    })
    
    # Test escalation with conversation history
    logger.info("\nStep 3: Testing escalation with conversation history")
    response3 = send_query("I need to speak to a human about legendary items", conversation_history)
    
    if "error" in response3:
        logger.error("Escalation query failed")
        return
    
    query_id3 = response3.get("query_id", "")
    run_id3 = response3.get("metadata", {}).get("run_id", "")
    parent_run_id3 = response3.get("metadata", {}).get("parent_run_id", "")
    ticket_id = response3.get("ticket_id", "")
    
    logger.info(f"Escalation response: query_id={query_id3}, run_id={run_id3}, parent_run_id={parent_run_id3}")
    logger.info(f"Ticket ID: {ticket_id}")
    logger.info(f"Answer: {response3.get('answer', '')}")
    
    # Check if trace continuity was maintained for escalation
    if parent_run_id3 and (parent_run_id3 == run_id2 or parent_run_id3 == query_id2):
        logger.info("✅ Trace continuity MAINTAINED for escalation")
    else:
        logger.error("❌ Trace continuity BROKEN for escalation")
        logger.error(f"  Second run_id: {run_id2}")
        logger.error(f"  Escalation parent_run_id: {parent_run_id3}")
    
    # Summary
    logger.info("\n=== TRACE CONTINUITY TEST SUMMARY ===")
    logger.info(f"Initial Query: {query_id1} (run_id: {run_id1})")
    logger.info(f"Follow-up Query: {query_id2} (run_id: {run_id2}, parent: {parent_run_id2})")
    logger.info(f"Escalation Query: {query_id3} (run_id: {run_id3}, parent: {parent_run_id3})")
    logger.info(f"Ticket ID: {ticket_id}")
    
    if ticket_id:
        logger.info("A ticket was successfully created. Check Jira for conversation history.")
    else:
        logger.error("No ticket was created for the escalation request.")

def test_direct_escalation():
    """Test a direct escalation without prior conversation"""
    logger.info("\n=== TESTING DIRECT ESCALATION ===")
    response = send_query("I need to speak to a human")
    
    if "error" in response:
        logger.error("Direct escalation query failed")
        return
    
    query_id = response.get("query_id", "")
    run_id = response.get("metadata", {}).get("run_id", "")
    ticket_id = response.get("ticket_id", "")
    
    logger.info(f"Direct escalation: query_id={query_id}, run_id={run_id}")
    logger.info(f"Ticket ID: {ticket_id}")
    logger.info(f"Answer: {response.get('answer', '')}")
    
    if ticket_id:
        logger.info("✅ Direct escalation ticket created successfully")
    else:
        logger.error("❌ No ticket created for direct escalation")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "direct":
        test_direct_escalation()
    else:
        test_trace_continuity() 