import streamlit as st
import requests
import json
from typing import Optional
import uuid
import os

# Constants
API_URL = os.environ.get("API_URL", "http://localhost:8000/api/v1")
DEMO_TOKEN = os.environ.get("DEMO_TOKEN", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkZW1vX3VzZXIiLCJyb2xlIjoiZ2FtZXIifQ.8qPWSSvIY7TfRjd0pc-oYKbpodM6wPVSbI_O_Y9jD20")

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

def main():
    import streamlit as st
    st.write("Streamlit version:", st.__version__)
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
                            st.session_state['feedback_given'][query_id] = "negative_pending"
                            st.session_state['negative_feedback'][query_id] = ""
                            st.experimental_rerun()
                    elif st.session_state['feedback_given'][query_id] == "positive":
                        st.success("Thanks for your positive feedback!")
                    elif st.session_state['feedback_given'][query_id] == "negative_pending":
                        comment = st.text_area("Please tell us how we can improve:", key=f"hist_feedback_comment_{query_id}")
                        if st.button("Submit Feedback", key=f"hist_submit_neg_feedback_{query_id}"):
                            try:
                                submit_feedback(query_id, "negative", comment)
                                st.session_state['feedback_given'][query_id] = "negative_submitted"
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Error submitting feedback: {str(e)}")
                    elif st.session_state['feedback_given'][query_id] == "negative_submitted":
                        st.info("Thanks for your feedback! We'll use it to improve our responses.")
        elif message['type'] == 'followup':
            with st.chat_message("assistant", avatar="❓"):
                st.warning(message['content'])
        elif message['type'] == 'system':
            st.caption(message['content'])

    # Query input
    query = st.chat_input("Type your question here...")
    
    # Check if we have a sample question from a button click
    sample_query = st.session_state.get('sample_question')
    if sample_query:
        query = sample_query
        # Reset sample question to prevent reprocessing
        st.session_state['sample_question'] = None
    
    if query:
        # Only add user query to history if it wasn't added by the sample question button
        # Check if the last message is not already this query
        should_add_to_history = True
        if st.session_state['messages'] and st.session_state['messages'][-1]['type'] == 'user' and st.session_state['messages'][-1]['content'] == query:
            should_add_to_history = False

        if should_add_to_history:
            st.session_state['messages'].append({
                'type': 'user',
                'content': query
            })
            
            # Show user message immediately 
            st.chat_message("user", avatar="👤").write(query)
        
        # Handle follow-up responses intelligently
        if st.session_state['pending_followup'] and st.session_state['original_question']:
            # This is a follow-up response, combine it with original context
            original_q = st.session_state['original_question']
            followup_ctx = st.session_state['followup_context']
            
            # Construct different combined queries based on follow-up context
            if "clan" in followup_ctx.lower():
                # Check for specific clan type query vs generic clan question
                if "type" in original_q.lower():
                    combined_query = f"What is the type of clan {query}?"
                elif "magic" in original_q.lower():
                    combined_query = f"Is {query} a magic clan?"
                elif "how many" in original_q.lower() and "members" in original_q.lower():
                    combined_query = f"How many members does clan {query} have?"
                elif "members" in original_q.lower():
                    combined_query = f"What is the member count of clan {query}?"
                else:
                    combined_query = f"Tell me about clan {query}"
            elif "player" in followup_ctx.lower():
                combined_query = f"{original_q} for player {query}"
            elif "item" in followup_ctx.lower():
                combined_query = f"{original_q} about item {query}"
            elif "rank" in followup_ctx.lower():
                # Remove any trailing periods from original_q
                clean_q = original_q.rstrip('.')
                combined_query = f"What is {query}'s rank?"
            elif "status" in followup_ctx.lower():
                # Remove any trailing periods from original_q
                clean_q = original_q.rstrip('.')
                combined_query = f"What is the status of {query}?"
            else:
                # Generic combination
                # Remove any trailing periods from original_q
                clean_q = original_q.rstrip('.')
                combined_query = f"{clean_q} for {query}"
                
            # Log the combined query for transparency
            st.session_state['messages'].append({
                'type': 'system',
                'content': f"Complete query: {combined_query}"
            })
            
            # Use the combined query
            api_query = combined_query
        else:
            # Regular question
            api_query = query
        
        with st.spinner("Getting answer..."):
            try:
                # Call API
                response = get_support_response(api_query)
                
                # Display assistant response
                with st.chat_message("assistant", avatar="🤖"):
                    st.write(response["answer"])
                    st.caption(f"Source: {response['source_type']}")
                    
                    # Show ticket ID if present
                    if response.get("ticket_id"):
                        st.error(f"Ticket created: {response['ticket_id']}")
                    
                    # Add feedback buttons
                    query_id = response.get("query_id", str(uuid.uuid4()))
                    col1, col2, col3 = st.columns([1, 1, 5])
                    
                    # Check if feedback already given for this query
                    if query_id not in st.session_state['feedback_given']:
                        if col1.button("👍", key=f"thumbs_up_{query_id}"):
                            try:
                                submit_feedback(query_id, "positive")
                                st.session_state['feedback_given'][query_id] = "positive"
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Error submitting feedback: {str(e)}")
                        
                        if col2.button("👎", key=f"thumbs_down_{query_id}"):
                            st.session_state['feedback_given'][query_id] = "negative_pending"
                            st.session_state['negative_feedback'][query_id] = ""
                            st.experimental_rerun()
                    elif st.session_state['feedback_given'][query_id] == "positive":
                        st.success("Thanks for your positive feedback!")
                    elif st.session_state['feedback_given'][query_id] == "negative_pending":
                        comment = st.text_area("Please tell us how we can improve:", key=f"feedback_comment_{query_id}")
                        if st.button("Submit Feedback", key=f"submit_neg_feedback_{query_id}"):
                            try:
                                submit_feedback(query_id, "negative", comment)
                                st.session_state['feedback_given'][query_id] = "negative_submitted"
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Error submitting feedback: {str(e)}")
                    elif st.session_state['feedback_given'][query_id] == "negative_submitted":
                        st.info("Thanks for your feedback! We'll use it to improve our responses.")
                
                # Add assistant response to history
                st.session_state['messages'].append({
                    'type': 'assistant',
                    'content': response["answer"],
                    'source_type': response['source_type'],
                    'ticket_id': response.get('ticket_id'),
                    'query_id': response.get('query_id', str(uuid.uuid4()))
                })
                
                # If follow-up is needed, show it
                if response.get("follow_up_question") and response['source_type'] == 'follow_up':
                    with st.chat_message("assistant", avatar="❓"):
                        st.warning(response["follow_up_question"])
                    
                    # Add follow-up to history
                    st.session_state['messages'].append({
                        'type': 'followup',
                        'content': response["follow_up_question"]
                    })
                    
                    # Save the original question that triggered the follow-up
                    if not st.session_state['pending_followup']:
                        st.session_state['original_question'] = query
                        # Extract context from follow-up question for better combining
                        followup_text = response["follow_up_question"].lower()
                        st.session_state['followup_context'] = followup_text
                    
                    # Mark that we're awaiting a follow-up response
                    st.session_state['pending_followup'] = True
                else:
                    st.session_state['pending_followup'] = False
                    st.session_state['original_question'] = ""
                    st.session_state['followup_context'] = ""
                
                # Force a rerun to refresh the chat input
                st.experimental_rerun()
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")

    # Sample questions in sidebar
    st.sidebar.write("### Sample Questions")
    
    # Create clickable sample questions
    st.sidebar.markdown("#### Static Knowledge Questions")
    st.sidebar.markdown("*Game mechanics & policy queries*")
    static_questions = [
        "What benefits do VIP players get?",
        "Why are legendary items considered rare?",
        "Can XP boosters be stacked with other buffs?",
        "How do magic clans differ from combat clans?",
        "What are the requirements to join a legendary clan?"
    ]
    
    for q in static_questions:
        if st.sidebar.button(q, key=f"static_{q}"):
            # Add user query to history
            st.session_state['messages'].append({
                'type': 'user',
                'content': q
            })
            # Set the sample question to be processed
            st.session_state['sample_question'] = q
            st.experimental_rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### Dynamic Data Questions")
    st.sidebar.markdown("*Player-specific & live data queries*")
    dynamic_questions = [
        "What is the VIP status of ShadowNinja?",
        "What items has IceWarden purchased last week?",
        "What is DragonSlayer99's current rank?",
        "How many legendary items has PixelMage bought?",
        "Is FireMages a magic clan?"
    ]
    
    for q in dynamic_questions:
        if st.sidebar.button(q, key=f"dynamic_{q}"):
            # Add user query to history
            st.session_state['messages'].append({
                'type': 'user',
                'content': q
            })
            # Set the sample question to be processed
            st.session_state['sample_question'] = q
            st.experimental_rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### Hybrid Questions")
    st.sidebar.markdown("*Combining database data & knowledge*")
    hybrid_questions = [
        "Is FireMages a magic clan and what are the benefits?",
        "How many gold achievements has DragonSlayer99 earned and what rewards do they give?",
        "What legendary items has PixelMage purchased and why are they valuable?",
        "How many players and clans are there in total?",
        "Compare BlazeRider's XP to average player levels"
    ]
    
    for q in hybrid_questions:
        if st.sidebar.button(q, key=f"hybrid_{q}"):
            # Add user query to history
            st.session_state['messages'].append({
                'type': 'user',
                'content': q
            })
            # Set the sample question to be processed
            st.session_state['sample_question'] = q
            st.experimental_rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### Follow-Up Requiring Questions")
    st.sidebar.markdown("*Questions needing clarification*")
    followup_questions = [
        "List the legendary items purchased.",
        "What is my clan's type?",
        "Show me my rank.",
        "What items have I purchased?",
        "How many members does my clan have?"
    ]
    
    for q in followup_questions:
        if st.sidebar.button(q, key=f"followup_{q}"):
            # Add user query to history
            st.session_state['messages'].append({
                'type': 'user',
                'content': q
            })
            # Set the sample question to be processed
            st.session_state['sample_question'] = q
            st.experimental_rerun()
    
    # Add reset button in sidebar
    if st.sidebar.button("Reset Chat"):
        st.session_state['messages'] = []
        st.session_state['pending_followup'] = False
        st.session_state['original_question'] = ""
        st.session_state['followup_context'] = ""
        st.experimental_rerun()

if __name__ == "__main__":
    main() 