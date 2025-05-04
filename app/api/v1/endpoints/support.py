from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from app.schemas.support import SupportQuery, SupportResponse
from app.schemas.support import Feedback, FeedbackType
from app.services.agents.router import query_router
from app.core.security import get_current_user
from app.schemas.user import User
import uuid
import json
import os
from datetime import datetime

router = APIRouter()

@router.post("/query", response_model=SupportResponse)
async def handle_support_query(
    query: SupportQuery,
    current_user: User = Depends(get_current_user)
) -> SupportResponse:
    """
    Handle a support query from a user.
    The query will be routed to appropriate agents based on its content.
    """
    try:
        response = await query_router.route_query(
            query.text,
            user_context={
                "username": current_user.username,
                "role": current_user.role
            }
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
            }
        }
        
        # Create feedback directory if it doesn't exist
        os.makedirs("feedback", exist_ok=True)
        
        # Write feedback_data to a JSON file
        with open(f"feedback/{query_id}.json", "w") as f:
            json.dump(feedback_data, f, indent=2)
        
        return SupportResponse(
            query_id=query_id,
            answer=response.answer,
            source_type=response.source_type,
            follow_up_question=response.follow_up_question,
            ticket_id=response.ticket_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )

@router.post("/feedback", status_code=201)
async def submit_feedback(feedback: Feedback):
    """Store user feedback for a specific query."""
    try:
        # Check if the query exists
        if not os.path.exists(f"feedback/{feedback.query_id}.json"):
            raise HTTPException(status_code=404, detail="Query not found")
        
        # Read the existing query data
        with open(f"feedback/{feedback.query_id}.json", "r") as f:
            query_data = json.load(f)
        
        # Add the feedback to the data
        query_data["feedback"] = {
            "type": feedback.feedback_type,
            "comment": feedback.comment,
            "timestamp": datetime.now().isoformat()
        }
        
        # Write the updated data back to the file
        with open(f"feedback/{feedback.query_id}.json", "w") as f:
            json.dump(query_data, f, indent=2)
        
        return {"status": "success", "message": "Feedback recorded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording feedback: {str(e)}") 