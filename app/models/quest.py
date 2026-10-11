import uuid
from datetime import datetime
from typing import List
from sqlalchemy import String, Text, Integer, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class Quest(Base):
    __tablename__ = "quests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    total_days: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    points_reward: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=True , default="Please submit your response for this quest.")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    assignments: Mapped[List["UserQuest"]] = relationship("UserQuest", back_populates="quest")
  
from app.models.submission import QuestSubmission