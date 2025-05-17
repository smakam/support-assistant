import streamlit as st
import requests
import json
from typing import Optional, Dict, Any
import uuid
import os
import logging
import pandas as pd
import sqlite3
import io
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np

# Constants
API_URL = os.environ.get("API_URL", "http://localhost:8000/api/v1")
DEMO_TOKEN = os.environ.get("DEMO_TOKEN", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkZW1vX3VzZXIiLCJyb2xlIjoiZ2FtZXIifQ.8qPWSSvIY7TfRjd0pc-oYKbpodM6wPVSbI_O_Y9jD20")
KNOWLEDGE_BASE_PATH = os.environ.get("KNOWLEDGE_BASE_PATH", "advanced_knowledge_base.txt")
DB_PATH = os.environ.get("DB_PATH", "kgen_gaming_support_advanced.db")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

# Set page config for main page
st.set_page_config(
    page_title="KGen AI Support Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Function to find file in current or parent directory
def find_file(filename):
    """Find a file in the current directory or parent directory"""
    # Try current directory
    if os.path.exists(filename):
        return os.path.abspath(filename)
    
    # Try relative to script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, filename)
    if os.path.exists(file_path):
        return file_path
    
    # Try one level up
    parent_dir = os.path.dirname(script_dir)
    file_path = os.path.join(parent_dir, filename)
    if os.path.exists(file_path):
        return file_path
    
    # Try two levels up
    grandparent_dir = os.path.dirname(parent_dir)
    file_path = os.path.join(grandparent_dir, filename)
    if os.path.exists(file_path):
        return file_path
    
    return None

# Function to read knowledge base content
def read_knowledge_base():
    try:
        # Find the knowledge base file
        kb_path = find_file(KNOWLEDGE_BASE_PATH)
        if kb_path:
            logger.info(f"Found knowledge base at: {kb_path}")
            with open(kb_path, 'r') as f:
                return f.read()
        else:
            logger.error(f"Knowledge base file not found: {KNOWLEDGE_BASE_PATH}")
            return f"Knowledge base file not found: {KNOWLEDGE_BASE_PATH}"
    except Exception as e:
        logger.error(f"Error reading knowledge base: {str(e)}")
        return f"Error reading knowledge base: {str(e)}"

# Function to get SQL database structure
def get_db_schema():
    try:
        # Check for production environment indicator
        is_production = os.environ.get("ENVIRONMENT", "").lower() == "production"
        
        if is_production:
            # Use PostgreSQL in production
            import psycopg2
            from psycopg2 import sql
            
            db_url = os.environ.get("DATABASE_URL")
            if not db_url:
                logger.error("DATABASE_URL environment variable not set in production")
                return "DATABASE_URL environment variable not set in production"
                
            # Connect to PostgreSQL
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            
            # Get list of tables in PostgreSQL
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = cursor.fetchall()
            
            schema = {}
            for table in tables:
                table_name = table[0]
                # Get column info from PostgreSQL
                cursor.execute(sql.SQL("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = %s
                """), [table_name])
                columns = cursor.fetchall()
                schema[table_name] = [{"name": col[0], "type": col[1]} for col in columns]
            
            conn.close()
            return schema
        else:
            # Use SQLite for local development
            db_path = find_file(DB_PATH)
            if not db_path:
                logger.error(f"Database file not found: {DB_PATH}")
                return f"Database file not found: {DB_PATH}"
            
            logger.info(f"Found database at: {db_path}")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get list of tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            schema = {}
            for table in tables:
                table_name = table[0]
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                schema[table_name] = [{"name": col[1], "type": col[2]} for col in columns]
            
            conn.close()
            return schema
    except Exception as e:
        logger.error(f"Error reading database schema: {str(e)}")
        return f"Error reading database schema: {str(e)}"

# Function to get sample data from tables
def get_sample_data(table_name, limit=5):
    try:
        # Check for production environment indicator
        is_production = os.environ.get("ENVIRONMENT", "").lower() == "production"
        
        if is_production:
            # Use PostgreSQL in production
            import psycopg2
            import psycopg2.extras
            
            db_url = os.environ.get("DATABASE_URL")
            if not db_url:
                logger.error("DATABASE_URL environment variable not set in production")
                return pd.DataFrame({"Error": ["DATABASE_URL environment variable not set in production"]})
                
            # Connect to PostgreSQL
            conn = psycopg2.connect(db_url)
            
            # Create a safe query using parameters
            query = f"SELECT * FROM {table_name} LIMIT %s"
            df = pd.read_sql_query(query, conn, params=(limit,))
            conn.close()
            return df
        else:
            # Use SQLite for local development
            db_path = find_file(DB_PATH)
            if not db_path:
                logger.error(f"Database file not found: {DB_PATH}")
                return pd.DataFrame({"Error": [f"Database file not found: {DB_PATH}"]})
            
            conn = sqlite3.connect(db_path)
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
    except Exception as e:
        logger.error(f"Error fetching sample data: {str(e)}")
        return pd.DataFrame({"Error": [str(e)]})

# Function to create system architecture diagram
def create_system_diagram():
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Hide axes
    ax.axis('off')
    
    # Define component positions
    components = {
        "User Interface": (0.5, 0.9),
        "Router": (0.5, 0.7),
        "StaticKnowledgeAgent": (0.2, 0.5),
        "DynamicDataAgent": (0.5, 0.5),
        "HybridAgent": (0.8, 0.5),
        "Knowledge Base": (0.2, 0.3),
        "SQL Database": (0.5, 0.3),
        "JIRA": (0.8, 0.3),
        "LangSmith": (0.5, 0.1)
    }
    
    # Draw boxes
    for component, (x, y) in components.items():
        color = "skyblue"
        if "Agent" in component:
            color = "lightgreen"
        elif "Base" in component or "Database" in component:
            color = "wheat"
        elif component in ["JIRA", "LangSmith"]:
            color = "lightcoral"
            
        ax.add_patch(plt.Rectangle((x-0.1, y-0.04), 0.2, 0.08, fill=True, 
                                  alpha=0.7, color=color, transform=ax.transAxes))
        ax.text(x, y, component, ha='center', va='center', fontsize=10, transform=ax.transAxes)
    
    # Draw arrows
    ax.arrow(0.5, 0.86, 0, -0.1, head_width=0.01, head_length=0.02, fc='black', ec='black', transform=ax.transAxes)
    
    # Router to agents
    ax.arrow(0.5, 0.66, -0.25, -0.1, head_width=0.01, head_length=0.02, fc='black', ec='black', transform=ax.transAxes)
    ax.arrow(0.5, 0.66, 0, -0.1, head_width=0.01, head_length=0.02, fc='black', ec='black', transform=ax.transAxes)
    ax.arrow(0.5, 0.66, 0.25, -0.1, head_width=0.01, head_length=0.02, fc='black', ec='black', transform=ax.transAxes)
    
    # Agents to data sources
    ax.arrow(0.2, 0.46, 0, -0.09, head_width=0.01, head_length=0.02, fc='black', ec='black', transform=ax.transAxes)
    ax.arrow(0.5, 0.46, 0, -0.09, head_width=0.01, head_length=0.02, fc='black', ec='black', transform=ax.transAxes)
    
    # HybridAgent to both knowledge base and SQL
    ax.arrow(0.8, 0.46, -0.5, -0.09, head_width=0.01, head_length=0.02, fc='black', ec='black', transform=ax.transAxes, linestyle='dotted')
    ax.arrow(0.8, 0.46, -0.25, -0.09, head_width=0.01, head_length=0.02, fc='black', ec='black', transform=ax.transAxes, linestyle='dotted')
    
    # Router to JIRA for escalation cases 
    ax.arrow(0.5, 0.66, 0.3, -0.3, head_width=0.01, head_length=0.02, fc='black', ec='black', transform=ax.transAxes, linestyle='dashed', color='red')
    
    # Tracing to LangSmith
    ax.arrow(0.3, 0.5, 0.15, -0.35, head_width=0.01, head_length=0.02, fc='black', ec='black', transform=ax.transAxes, linestyle='dashed')
    ax.arrow(0.5, 0.5, 0, -0.35, head_width=0.01, head_length=0.02, fc='black', ec='black', transform=ax.transAxes, linestyle='dashed')
    ax.arrow(0.7, 0.5, -0.15, -0.35, head_width=0.01, head_length=0.02, fc='black', ec='black', transform=ax.transAxes, linestyle='dashed')
    
    # Titles and legend
    plt.title("KGen AI Support Assistant - System Architecture", fontsize=14)
    
    legend_elements = [
        plt.Rectangle((0, 0), 1, 1, color="skyblue", alpha=0.7, label="Interface Components"),
        plt.Rectangle((0, 0), 1, 1, color="lightgreen", alpha=0.7, label="Agent Components"),
        plt.Rectangle((0, 0), 1, 1, color="wheat", alpha=0.7, label="Data Sources"),
        plt.Rectangle((0, 0), 1, 1, color="lightcoral", alpha=0.7, label="External Services"),
        plt.Line2D([0], [0], color='red', lw=2, linestyle='dashed', label='Escalation Flow'),
        plt.Line2D([0], [0], color='black', lw=2, linestyle='dotted', label='Hybrid Queries'),
    ]
    ax.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 0), ncol=2)
    
    plt.tight_layout()
    
    # Convert plot to image
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    img = Image.open(buf)
    return img

def get_support_response(query: str, conversation_history=None) -> dict:
    """Send query to support API and return response"""
    headers = {
        "Authorization": f"Bearer {DEMO_TOKEN}",
        "Content-Type": "application/json"
    }
    url = f"{API_URL}/support/query"
    
    # Prepare the request payload
    payload = {"text": query}
    
    # Check for all escalation phrases, matching the backend logic
    escalation_phrases = [
        "speak to a human", "talk to a human", "need a human", "contact support", 
        "escalate", "support ticket", "create a ticket", "speak to an agent",
        "talk to support", "need help from a person", "human support"
    ]
    is_escalation = query.lower().startswith("escalate:") or any(phrase in query.lower() for phrase in escalation_phrases)
    
    # Add conversation history if provided (for all requests, not just escalations)
    if conversation_history:
        # Format conversation history according to the expected schema
        formatted_history = []
        for msg in conversation_history:
            if isinstance(msg, dict) and 'type' in msg and 'content' in msg:
                # Include metadata if available for trace continuity
                msg_data = {
                    "type": msg["type"],
                    "content": msg["content"]
                }
                # Preserve metadata for trace continuity
                if 'metadata' in msg and msg['metadata']:
                    msg_data["metadata"] = msg['metadata']
                formatted_history.append(msg_data)
        
        payload["conversation_history"] = formatted_history
        logger.info(f"Sending {len(formatted_history)} conversation messages in API request")
        logger.info(f"Conversation history includes trace metadata: {any('metadata' in msg for msg in formatted_history)}")
    
    logger.info(f"Requesting: {url} with headers={headers} and data={payload}")
    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload
        )
        logger.info(f"Response status: {response.status_code}, text: {response.text}")
        return response.json()
    except Exception as e:
        logger.error(f"API error: {e}")
        return {}

def submit_feedback(query_id: str, feedback_type: str, comment: Optional[str] = None) -> dict:
    """Submit feedback for a query response"""
    headers = {
        "Authorization": f"Bearer {DEMO_TOKEN}",
        "Content-Type": "application/json"
    }
    url = f"{API_URL}/feedback"
    logger.info(f"Submitting feedback: {url} with headers={headers} and data={{'query_id': query_id, 'feedback_type': feedback_type, 'comment': comment}}")
    try:
        response = requests.post(
            url,
            headers=headers,
            json={"query_id": query_id, "feedback_type": feedback_type, "comment": comment}
        )
        logger.info(f"Feedback response status: {response.status_code}, text: {response.text}")
        return response.json()
    except Exception as e:
        logger.error(f"API error: {e}")
        return {}

def process_sample_question():
    """Process sample question selected from sidebar"""
    if st.session_state.get('sample_question'):
        # Get the selected question
        question = st.session_state['sample_question']
        logger.info(f"Processing sample question: {question}")
        
        # Add the question to the message history as a user message
        st.session_state['messages'].append({
            'type': 'user',
            'content': question
        })
        
        # Use the utility function for trace continuity
        conversation_history = ensure_trace_continuity(
            st.session_state['messages'][:-1],  # Exclude the sample question we just added
            current_message=question
        )
        
        if conversation_history:
            logger.info(f"Including {len(conversation_history)} messages for sample question trace continuity")
        
        # Get API response with conversation history
        response = get_support_response(question, conversation_history=conversation_history)
        
        # Extract metadata from response for trace continuity
        metadata = response.get('metadata', {})
        
        # Check if follow-up is needed
        if response.get('follow_up_question'):
            # Store info for follow-up handling
            st.session_state['pending_followup'] = True
            st.session_state['followup_question'] = response.get('follow_up_question')
            st.session_state['original_question'] = question
            
            # Try to detect what information is being asked for in the follow-up
            follow_up_lower = response.get('follow_up_question', '').lower()
            if 'clan name' in follow_up_lower:
                st.session_state['followup_context'] = 'clan name'
            elif 'player name' in follow_up_lower:
                st.session_state['followup_context'] = 'player name'
            elif 'region' in follow_up_lower:
                st.session_state['followup_context'] = 'region'
            
            # Add the follow-up question as a system message
            st.session_state['messages'].append({
                'type': 'followup',
                'content': response.get('follow_up_question'),
                'metadata': metadata  # Store metadata for trace continuity
            })
        else:
            # Add the response as an assistant message
            st.session_state['messages'].append({
                'type': 'assistant',
                'content': response.get('answer', 'I encountered an error processing your request.'),
                'source_type': response.get('source_type', 'STATIC'),
                'follow_up_question': response.get('follow_up_question'),
                'query_id': response.get('query_id', str(uuid.uuid4())),
                'ticket_id': response.get('ticket_id'),
                'metadata': metadata  # Store metadata for trace continuity
            })
            
            # Debug log to check metadata
            if 'run_id' in metadata:
                logger.info(f"Stored response with run_id: {metadata['run_id']} for trace continuity")
            else:
                logger.warning("Response has no run_id in metadata!")
        
        # Reset sample question
        st.session_state['sample_question'] = None

def ensure_trace_continuity(messages, current_message):
    """
    Utility function to prepare conversation history with proper trace metadata
    for maintaining continuity in LangSmith traces.
    
    Args:
        messages: List of message objects from session state
        current_message: Current message being processed (to exclude from history)
        
    Returns:
        List of properly formatted conversation messages with metadata
    """
    conversation_history = []
    for msg in messages:
        # Skip the current message if it matches
        if current_message and msg.get('content') == current_message:
            continue
            
        # Skip messages with invalid types
        msg_type = msg.get('type')
        if msg_type not in ["assistant", "user", "followup", "system"]:
            continue
        
        # Create message with content and proper type
        msg_data = {
            "type": msg_type,
            "content": msg.get('content', '')
        }
        
        # Build comprehensive metadata
        metadata = {}
        
        # Include existing metadata
        if 'metadata' in msg and msg['metadata']:
            metadata.update(msg['metadata'])
        
        # Include query_id for trace linking
        if 'query_id' in msg:
            metadata['query_id'] = msg['query_id']
            
        # Include any other relevant fields for tracing
        if 'source_type' in msg:
            metadata['source_type'] = msg['source_type']
            
        # Only add metadata if we have any
        if metadata:
            msg_data["metadata"] = metadata
            
        conversation_history.append(msg_data)
        
    return conversation_history

def main():
    logger.info("Streamlit app started")
    
    # Regular chat UI
    st.title("KGen AI Support Assistant")
    st.write("Ask any question about game mechanics, player stats, or clan information!")

    # Initialize session state for message history
    if 'messages' not in st.session_state:
        st.session_state['messages'] = []
    
    if 'pending_followup' not in st.session_state:
        st.session_state['pending_followup'] = False

    # Track original question that triggered follow-up
    if 'original_question' not in st.session_state:
        st.session_state['original_question'] = ""
        
    # Track follow-up type for intelligent combination
    if 'followup_context' not in st.session_state:
        st.session_state['followup_context'] = ""

    # Add a state variable for sample questions
    if 'sample_question' not in st.session_state:
        st.session_state['sample_question'] = None

    # Track feedback state
    if 'feedback_given' not in st.session_state:
        st.session_state['feedback_given'] = {}
        
    # Track negative feedback comments
    if 'negative_feedback' not in st.session_state:
        st.session_state['negative_feedback'] = {}
    
    # Process sample questions if one was selected
    if st.session_state.get('sample_question'):
        process_sample_question()
        st.experimental_rerun()

    # Display message history
    for message in st.session_state['messages']:
        if message['type'] == 'user':
            st.chat_message("user", avatar="👤").write(message['content'])
        elif message['type'] == 'assistant':
            with st.chat_message("assistant", avatar="🤖"):
                st.write(message['content'])
                if message.get('source_type'):
                    st.caption(f"Source: {message['source_type']}")
                if message.get('ticket_id'):
                    st.error(f"Ticket created: {message['ticket_id']}")
                # Escalation interactive flow
                if message.get('source_type') == 'ESCALATION' and not message.get('ticket_id'):
                    if 'escalation_confirmed' not in st.session_state:
                        st.session_state['escalation_confirmed'] = False
                    if not st.session_state['escalation_confirmed']:
                        st.warning("Would you like to create a support ticket for this issue?")
                        col1, col2 = st.columns(2)
                        if col1.button("Yes, create ticket", key=f"escalate_yes_{message.get('query_id','')}"):
                            st.session_state['escalation_confirmed'] = True
                        if col2.button("No", key=f"escalate_no_{message.get('query_id','')}"):
                            st.session_state['escalation_confirmed'] = False
                            st.info("No ticket will be created.")
                    if st.session_state['escalation_confirmed']:
                        extra_details = st.text_area("Please provide any additional details for support (optional):", key=f"escalate_details_{message.get('query_id','')}")
                        if st.button("Submit Ticket", key=f"submit_escalate_{message.get('query_id','')}"):
                            # Use the utility function for consistent conversation history formatting
                            conversation_history = ensure_trace_continuity(
                                st.session_state['messages'],
                                current_message=None  # Include all messages for escalation
                            )
                            
                            # Log detailed info about the conversation history
                            logger.info(f"Sending COMPLETE conversation history with {len(conversation_history)} messages for escalation")
                            has_trace_metadata = any('run_id' in msg.get('metadata', {}) for msg in conversation_history)
                            logger.info(f"Conversation includes trace metadata: {has_trace_metadata}")
                            
                            # Create escalation query with prefix and details
                            escalation_query = f"ESCALATE: {message['content']}\nAdditional details: {extra_details}"
                            
                            # Send the request with conversation history
                            response = get_support_response(
                                escalation_query, 
                                conversation_history=conversation_history
                            )
                            
                            # Extract metadata from response for trace continuity
                            metadata = response.get('metadata', {})
                            
                            # Add the ticket creation response to history
                            st.session_state['messages'].append({
                                'type': 'assistant',
                                'content': response.get('answer', 'Ticket created.'),
                                'source_type': response.get('source_type', 'ESCALATION'),
                                'ticket_id': response.get('ticket_id'),
                                'query_id': response.get('query_id', str(uuid.uuid4())),
                                'metadata': metadata
                            })
                            st.session_state['escalation_confirmed'] = False
                            st.experimental_rerun()
                # Add feedback buttons to history messages too
                if message.get('query_id'):
                    query_id = message['query_id']
                    col1, col2, col3 = st.columns([1, 1, 5])
                    
                    # Check if feedback already given for this query
                    if query_id not in st.session_state['feedback_given']:
                        if col1.button("👍", key=f"hist_thumbs_up_{query_id}"):
                            try:
                                submit_feedback(query_id, "positive")
                                st.session_state['feedback_given'][query_id] = "positive"
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Error submitting feedback: {str(e)}")
                        
                        if col2.button("👎", key=f"hist_thumbs_down_{query_id}"):
                            st.session_state['negative_feedback'][query_id] = ""
                            st.experimental_rerun()
                    
                    # Already gave feedback - show it
                    elif st.session_state['feedback_given'].get(query_id) == "positive":
                        col1.markdown("👍")
                    elif st.session_state['feedback_given'].get(query_id) == "negative":
                        col2.markdown("👎")
                    
                    # Display textarea for negative feedback
                    if query_id in st.session_state['negative_feedback'] and query_id not in st.session_state['feedback_given']:
                        comment = st.text_area("What was wrong with this response?", key=f"neg_comment_{query_id}")
                        
                        if st.button("Submit Feedback", key=f"submit_neg_{query_id}"):
                            try:
                                submit_feedback(query_id, "negative", comment)
                                st.session_state['feedback_given'][query_id] = "negative"
                                del st.session_state['negative_feedback'][query_id]
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Error submitting feedback: {str(e)}")
        elif message['type'] == 'followup':
            st.info(message['content'])

    # Handle follow-up if needed
    if st.session_state.get('pending_followup') and st.session_state.get('followup_question'):
        followup_response = st.text_input(st.session_state['followup_question'], key="followup_input")
        
        # Add buttons to confirm or cancel
        col1, col2 = st.columns(2)
        submit_followup = col1.button("Submit Information")
        cancel_followup = col2.button("Cancel")
        
        if submit_followup and followup_response:
            # Add the follow-up response as a user message
            st.session_state['messages'].append({
                'type': 'user',
                'content': followup_response
            })
            
            # Build the combined query intelligently based on context
            if st.session_state.get('original_question') and st.session_state.get('followup_context'):
                # Replace the placeholder in the original question
                combined_query = st.session_state['original_question'].replace(
                    st.session_state['followup_context'], 
                    followup_response
                )
                # If no replacement happened, append the information
                if combined_query == st.session_state['original_question']:
                    combined_query = f"{st.session_state['original_question']} {st.session_state['followup_context']} {followup_response}"
            else:
                # Simple fallback approach
                combined_query = f"{st.session_state.get('original_question', '')} {followup_response}"
             
            # Use the utility function for trace continuity   
            conversation_history = ensure_trace_continuity(
                st.session_state['messages'][:-1],  # Exclude the followup response we just added
                current_message=followup_response
            )
            
            if conversation_history:
                logger.info(f"Including {len(conversation_history)} messages for follow-up trace continuity")
            
            # Get response to combined query with conversation history
            response = get_support_response(combined_query, conversation_history=conversation_history)
            
            # Extract metadata from response for trace continuity
            metadata = response.get('metadata', {})
            
            # Add the response as an assistant message
            st.session_state['messages'].append({
                'type': 'assistant',
                'content': response.get('answer', 'I encountered an error processing your request.'),
                'source_type': response.get('source_type', 'STATIC'),
                'follow_up_question': response.get('follow_up_question'),
                'query_id': response.get('query_id', str(uuid.uuid4())),
                'ticket_id': response.get('ticket_id'),
                'metadata': metadata  # Store metadata for trace continuity
            })
            # Reset follow-up state
            st.session_state['pending_followup'] = False
            st.session_state['original_question'] = ""
            st.session_state['followup_question'] = ""
            st.session_state['followup_context'] = ""
            st.experimental_rerun()
            
        elif cancel_followup:
            # Reset follow-up state without sending a query
            st.session_state['pending_followup'] = False
            st.session_state['original_question'] = ""
            st.session_state['followup_question'] = ""
            st.session_state['followup_context'] = ""
            st.experimental_rerun()

    # Chat input
    if not st.session_state.get('pending_followup'):
        # Allow user to enter a new query if not waiting for follow-up
        if prompt := st.chat_input():
            # Check if this is a direct escalation request
            escalation_phrases = [
                "speak to a human", "talk to a human", "need a human", "contact support", 
                "escalate", "support ticket", "create a ticket", "speak to an agent",
                "talk to support", "need help from a person", "human support"
            ]
            is_direct_escalation = any(phrase in prompt.lower() for phrase in escalation_phrases)
            
            # Add the user's message to history
            st.session_state['messages'].append({
                'type': 'user',
                'content': prompt
            })
            
            # Use the utility function to ensure trace continuity
            conversation_history = ensure_trace_continuity(
                st.session_state['messages'][:-1],  # Exclude the latest message we just added
                current_message=prompt
            )
            
            if conversation_history:
                logger.info(f"Including {len(conversation_history)} messages for trace continuity")
                if any('run_id' in msg.get('metadata', {}) for msg in conversation_history):
                    logger.info("✅ Found run_id in conversation history for trace continuity")
            
            # Get response from support API with conversation history
            response = get_support_response(prompt, conversation_history=conversation_history)
            
            # Extract metadata from response for trace continuity
            metadata = response.get('metadata', {})
            
            # Check if follow-up is needed
            if response.get('follow_up_question'):
                # Store info for follow-up handling
                st.session_state['pending_followup'] = True
                st.session_state['followup_question'] = response.get('follow_up_question')
                st.session_state['original_question'] = prompt
                
                # Try to detect what information is being asked for in the follow-up
                # This is used for smarter recombination later
                follow_up_lower = response.get('follow_up_question', '').lower()
                if 'clan name' in follow_up_lower:
                    st.session_state['followup_context'] = 'clan name'
                elif 'player name' in follow_up_lower:
                    st.session_state['followup_context'] = 'player name'
                elif 'region' in follow_up_lower:
                    st.session_state['followup_context'] = 'region'
                
                # Add the follow-up question as a system message
                st.session_state['messages'].append({
                    'type': 'followup',
                    'content': response.get('follow_up_question'),
                    'metadata': metadata  # Store metadata for trace continuity
                })
            else:
                # Add the response as an assistant message
                st.session_state['messages'].append({
                    'type': 'assistant',
                    'content': response.get('answer', 'I encountered an error processing your request.'),
                    'source_type': response.get('source_type', 'STATIC'),
                    'follow_up_question': response.get('follow_up_question'),
                    'query_id': response.get('query_id', str(uuid.uuid4())),
                    'ticket_id': response.get('ticket_id'),
                    'metadata': metadata  # Store metadata for trace continuity
                })
                
                # Debug log to check metadata
                if 'run_id' in metadata:
                    logger.info(f"Stored response with run_id: {metadata['run_id']} for trace continuity")
                else:
                    logger.warning("Response has no run_id in metadata!")
            
            st.experimental_rerun()

    # Show ticket ID if present
    if response := st.session_state.get('response', {}):
        if response.get("ticket_id"):
            st.error(f"Ticket created: {response['ticket_id']}")

    # Add sidebar with sample questions
    with st.sidebar:
        st.title("Sample Questions")
        
        # Create categories for better organization
        st.sidebar.markdown("#### Static Knowledge Questions")
        static_questions = [
            "What are XP boosters and how do they work?",
            "How are clans ranked in the game?",
            "What are legendary items?",
            "How do achievements work?",
            "Can I get a refund for purchases?",
        ]
        
        for q in static_questions:
            if st.sidebar.button(q, key=f"static_{q}"):
                st.session_state['sample_question'] = q
                st.experimental_rerun()
                
        st.sidebar.markdown("#### Dynamic Data Questions")
        dynamic_questions = [
            "What is IceWarden's current rank?",
            "Show DragonSlayer99's achievements",
            "Is FireMages a magic clan?",
            "How many members are in ShadowNinja's clan?",
        ]
        
        for q in dynamic_questions:
            if st.sidebar.button(q, key=f"dynamic_{q}"):
                st.session_state['sample_question'] = q
                st.experimental_rerun()
                
        st.sidebar.markdown("#### Hybrid Questions")
        hybrid_questions = [
            "Tell me about legendary items owned by DragonSlayer99",
            "What kind of clan is FireMages and what are they good for?",
            "Is FireMages a magic clan and what are the benefits?",
        ]
        
        for q in hybrid_questions:
            if st.sidebar.button(q, key=f"hybrid_{q}"):
                st.session_state['sample_question'] = q
                st.experimental_rerun()
                
        st.sidebar.markdown("#### Follow-up Needed")
        followup_questions = [
            "What items have I purchased?",
            "Is my clan a magic clan?",
            "How many members are in my clan?",
        ]
        
        for q in followup_questions:
            if st.sidebar.button(q, key=f"followup_{q}"):
                st.session_state['sample_question'] = q
                st.experimental_rerun()
                
        st.sidebar.markdown("#### Escalation Questions")
        
        escalation_questions = [
            "I need to speak to a human",
            "My payment failed, please help",
            "I need to escalate this issue",
        ]
        
        for q in escalation_questions:
            if st.sidebar.button(q, key=f"escalation_{q}"):
                st.session_state['sample_question'] = q
                st.experimental_rerun()
        
        # Clear chat
        if st.sidebar.button("Clear Chat", type="primary"):
            st.session_state['messages'] = []
            st.session_state['pending_followup'] = False
            st.session_state['original_question'] = ""
            st.session_state['followup_question'] = ""
            st.session_state['feedback_given'] = {}
            st.session_state['negative_feedback'] = {}
            st.experimental_rerun()

if __name__ == "__main__":
    main()