from pydantic import BaseModel
from typing import Optional
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

class SupportQuery(BaseModel):
    text: str

class SupportResponse(BaseModel):
    query_id: str
    answer: str
    source_type: SourceType
    follow_up_question: Optional[str] = None
    ticket_id: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "answer": "VIP players get exclusive access to special events, bonus XP, and unique cosmetic items.",
                "source_type": "static",
                "follow_up_question": None,
                "ticket_id": None
            }
        }

class Feedback(BaseModel):
    query_id: str
    feedback_type: FeedbackType
    comment: Optional[str] = None 