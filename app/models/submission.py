import uuid
from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import ForeignKey, Integer, String, Text, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class VerificationStatus(str, Enum):
    PENDING = "PENDING"
    PASSED = "PASSED"
    REJECTED = "REJECTED"

class QuestSubmission(Base):
    __tablename__ = "quest_submissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_quest_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user_quests.id"), nullable=False)
    
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)  # e.g., Day 1, Day 2
    image_path: Mapped[str] = mapped_column(String(500), nullable=False)
    
    ai_status: Mapped[VerificationStatus] = mapped_column(SQLEnum(VerificationStatus), default=VerificationStatus.PENDING, nullable=False)
    ai_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user_quest: Mapped["UserQuest"] = relationship("UserQuest", back_populates="submissions")