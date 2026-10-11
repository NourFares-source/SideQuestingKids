from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

from typing import List, Optional
from app.models.user_quest import QuestStatus
from app.schemas.submission import QuestSubmissionResponse


class QuestCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    prompt: Optional[str] = Field(
        None, 
        description="Detailed system instructions for Gemini vision model during verification."
    )
    description: str = Field(..., min_length=10)
    points_reward: int = Field(50, ge=10, le=1000)  # Renamed from xp_reward
    total_days: int = Field(1, ge=1, le=30)         # Renamed from duration_days


class QuestResponse(BaseModel):
    id: UUID
    title: str
    description: str
    points_reward: int
    prompt: Optional[str] = None
    total_days: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
        
class UserQuestResponse(BaseModel):
    id: UUID
    user_id: UUID
    quest_id: UUID
    status: QuestStatus
    current_step: int
    total_steps: int
    quest: QuestResponse
    submissions: List[QuestSubmissionResponse] = []

    class Config:
        from_attributes = True