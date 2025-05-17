from pydantic import BaseModel
from typing import Optional, List, Literal, Dict, Any
from enum import Enum

class SourceType(str, Enum):
    STATIC = "static"
    DYNAMIC = "dynamic"
    HYBRID = "hybrid"
    FOLLOW_UP = "follow_up"
    ESCALATION = "escalation"

class FeedbackType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"

class ConversationMessage(BaseModel):
    type: Literal["user", "assistant", "followup", "system"]
    content: str
    metadata: Optional[Dict[str, Any]] = None

class SupportQuery(BaseModel):
    text: str
    conversation_history: Optional[List[ConversationMessage]] = None

class SupportResponse(BaseModel):
    query_id: str
    answer: str
    source_type: SourceType
    follow_up_question: Optional[str] = None
    ticket_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        schema_extra = {
            "example": {
                "answer": "VIP players get exclusive access to special events, bonus XP, and unique cosmetic items.",
                "source_type": "static",
                "follow_up_question": None,
                "ticket_id": None,
                "metadata": {"run_id": "uuid-sample-123456789"}
            }
        }

class Feedback(BaseModel):
    query_id: str
    feedback_type: FeedbackType
    comment: Optional[str] = None