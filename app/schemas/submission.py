# app/schemas/submission.py
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.submission import VerificationStatus

class QuestSubmissionResponse(BaseModel):
    id: uuid.UUID
    user_quest_id: uuid.UUID
    step_number: int
    image_path: str
    ai_status: VerificationStatus
    ai_feedback: Optional[str] = None
    submitted_at: datetime

    class Config:
        from_attributes = True