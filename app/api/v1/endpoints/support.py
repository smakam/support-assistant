from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List
from app.schemas.support import SupportQuery, SupportResponse
from app.schemas.support import Feedback, FeedbackType, ConversationMessage
from app.services.agents.router import query_router
from app.core.security import get_current_user
from app.schemas.user import User
import uuid
import json
import os
from datetime import datetime
from app.core.config import settings
import logging
from langsmith import traceable, Client

router = APIRouter()
logger = logging.getLogger("uvicorn.error")
langsmith_client = Client()

@router.post("/query", response_model=SupportResponse)
@traceable(name="handle_support_query")
async def handle_support_query(
    query: SupportQuery,
    current_user: User = Depends(get_current_user)
) -> SupportResponse:
    """
    Handle a support query from a user.
    The query will be routed to appropriate agents based on its content.
    """
    logger.info(f"Received support query: {query.text} from user: {current_user.username}")
    
    # Debug logging for conversation history
    if query.conversation_history:
        logger.info(f"Request includes {len(query.conversation_history)} conversation history messages")
    else:
        logger.info("No conversation history in request")
    
    # Check if this is an escalation request to maintain trace continuity
    is_escalation = any(phrase in query.text.lower() for phrase in [
        "escalate", "support ticket", "create a ticket", "speak to a human", 
        "speak to an agent", "talk to a person", "need human support"
    ])
    
    # Get parent_run_id from the last conversation message if available
    parent_run_id = None
    if query.conversation_history:
        # Find the last assistant message that might have a run_id
        for message in reversed(query.conversation_history):
            if message.type == "assistant" and hasattr(message, 'metadata') and message.metadata:
                if isinstance(message.metadata, dict) and 'run_id' in message.metadata:
                    parent_run_id = message.metadata['run_id']
                    logger.info(f"Found parent run ID for continuity: {parent_run_id}")
                    break
                elif isinstance(message.metadata, dict) and 'query_id' in message.metadata:
                    # Use query_id as fallback if no run_id
                    parent_run_id = message.metadata['query_id']
                    logger.info(f"Using query_id as parent run ID: {parent_run_id}")
                    break
        
        if parent_run_id:
            logger.info(f"Linking request to previous conversation with parent_run_id: {parent_run_id}")
        else:
            logger.info("No parent run ID found in conversation history")
    
    try:
        # Convert conversation_history from the schema to a list of dictionaries
        conversation_history = None
        if query.conversation_history:
            conversation_history = [
                {
                    "type": message.type,
                    "content": message.content,
                    "metadata": message.metadata if hasattr(message, 'metadata') else None
                }
                for message in query.conversation_history
            ]
            logger.info(f"Converted {len(conversation_history)} conversation messages to dict format")
        
        # For escalation queries, make sure we're passing the conversation history
        if is_escalation and not conversation_history:
            logger.warning("Escalation query without conversation history")
        
        # Get the current run ID from the LangSmith context
        current_run_id = None
        try:
            # First try the standard LangSmith v2 method
            from langsmith.run_trees import get_run_tree_context
            run_context = get_run_tree_context()
            if run_context and hasattr(run_context, 'run') and run_context.run:
                current_run_id = run_context.run.id
                logger.info(f"Current run ID from run_tree_context: {current_run_id}")
        except Exception as e:
            logger.warning(f"Could not get current run ID from run_tree_context: {e}")
            
        # Fallback to alternative methods if run_id is still not available
        if not current_run_id:
            try:
                # Try to get current run directly from client
                from langsmith import Client
                client = Client()
                
                # Generate a run ID if one doesn't exist yet
                current_run_id = str(uuid.uuid4())
                logger.info(f"Generated fallback run ID: {current_run_id}")
            except Exception as e:
                logger.warning(f"Could not generate fallback run ID: {e}")
                # Last resort - use query ID as run ID
                current_run_id = str(uuid.uuid4())
                logger.info(f"Using UUID as run ID: {current_run_id}")
        
        response = await query_router.route_query(
            query.text,
            user_context={
                "username": current_user.username,
                "role": current_user.role
            },
            conversation_history=conversation_history,
            parent_run_id=parent_run_id
        )
        
        # Generate a unique ID for this query-response pair
        query_id = str(uuid.uuid4())
        
        # Store the query and response pair in a JSON file for feedback reference
        feedback_data = {
            "query_id": query_id,
            "query": query.text,
            "response": response.answer,
            "source_type": response.source_type,
            "timestamp": datetime.now().isoformat(),
            "user_context": {
                "username": current_user.username,
                "role": current_user.role
            },
            "run_id": current_run_id,
            "parent_run_id": parent_run_id
        }
        
        # Create feedback directory if it doesn't exist
        os.makedirs(settings.FEEDBACK_DIR, exist_ok=True)
        
        # Write feedback_data to a JSON file
        with open(os.path.join(settings.FEEDBACK_DIR, f"{query_id}.json"), "w") as f:
            json.dump(feedback_data, f, indent=2)
        
        logger.info(f"Query response: {response.answer}, query_id: {query_id}")
        
        # Include comprehensive metadata in the response for trace continuity
        metadata = {
            "run_id": current_run_id,
            "query_id": query_id,
            "parent_run_id": parent_run_id,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Returning response with metadata: {metadata}")
        
        return SupportResponse(
            query_id=query_id,
            answer=response.answer,
            source_type=response.source_type,
            follow_up_question=response.follow_up_question,
            ticket_id=response.ticket_id,
            metadata=metadata
        )
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )

@router.post("/feedback", status_code=201)
@traceable(name="submit_feedback")
async def submit_feedback(feedback: Feedback):
    """Store user feedback for a specific query."""
    logger.info(f"Received feedback for query_id: {feedback.query_id}, type: {feedback.feedback_type}, comment: {feedback.comment}")
    try:
        # Check if the query exists
        if not os.path.exists(os.path.join(settings.FEEDBACK_DIR, f"{feedback.query_id}.json")):
            raise HTTPException(status_code=404, detail="Query not found for feedback")
        
        # Read the existing query data
        with open(os.path.join(settings.FEEDBACK_DIR, f"{feedback.query_id}.json"), "r") as f:
            query_data = json.load(f)
        
        # Add the feedback to the data
        query_data["feedback"] = {
            "type": feedback.feedback_type,
            "comment": feedback.comment,
            "timestamp": datetime.now().isoformat()
        }
        
        # Write the updated data back to the file
        with open(os.path.join(settings.FEEDBACK_DIR, f"{feedback.query_id}.json"), "w") as f:
            json.dump(query_data, f, indent=2)
        
        logger.info(f"Feedback recorded for query_id: {feedback.query_id}")
        return {"status": "success", "message": "Feedback recorded successfully"}
    except Exception as e:
        logger.error(f"Error recording feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Error recording feedback: {str(e)}") 