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
import sys

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import from our streamlit_app.py file
from streamlit_app import (
    get_support_response, submit_feedback, process_sample_question, 
    ensure_trace_continuity, create_system_diagram, 
    read_knowledge_base, get_db_schema, get_sample_data, find_file,
    API_URL, DEMO_TOKEN
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Streamlit app started")
    
    # Regular chat UI
    st.title("KGen AI Support Assistant")
    st.write("Ask any question about game mechanics, player stats, or clan information!")

    # Add brief info about what the app does
    with st.expander("About this demo"):
        st.markdown("""
        This demo showcases an AI-powered customer support assistant for a fictional gaming platform. 
        
        - Ask questions about game mechanics, policies, or player/clan data
        - The system will route your query to the appropriate specialized agent
        - For more details on how it works, see the **System Help** page
        - To explore available data, check the **Data Explorer** page
        """)
        
        col1, col2 = st.columns(2)
        col1.markdown("[📚 System Architecture](pages/1_System_Help.py)")
        col2.markdown("[📊 Data Explorer](pages/2_Data_Explorer.py)")

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
                
        # Navigation links
        st.sidebar.markdown("---")
        st.sidebar.markdown("### Navigation")
        
        st.sidebar.markdown("[💬 Chat Assistant](Home.py)")
        st.sidebar.markdown("[📚 System Architecture](pages/1_System_Help.py)")
        st.sidebar.markdown("[📊 Data Explorer](pages/2_Data_Explorer.py)")
        
        # Clear chat
        st.sidebar.markdown("---")
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