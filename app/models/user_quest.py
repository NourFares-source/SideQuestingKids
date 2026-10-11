import uuid
from datetime import datetime
from enum import Enum
from typing import List
from sqlalchemy import ForeignKey, Integer, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class QuestStatus(str, Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class UserQuest(Base):
    __tablename__ = "user_quests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    quest_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quests.id"), nullable=False)
    
    status: Mapped[QuestStatus] = mapped_column(SQLEnum(QuestStatus), default=QuestStatus.ACTIVE, nullable=False)
    current_step: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    total_steps: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="assignments")
    quest: Mapped["Quest"] = relationship("Quest", back_populates="assignments")
    submissions: Mapped[List["QuestSubmission"]] = relationship("QuestSubmission", back_populates="user_quest", cascade="all, delete-orphan")