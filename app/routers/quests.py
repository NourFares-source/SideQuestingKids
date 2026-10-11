import uuid
import random
import os
from datetime import date
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status , UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.quest import Quest
from app.services.ai_verifier import verify_quest_submission
from app.models.user_quest import UserQuest
from app.models.user import User
from app.schemas.quest import QuestCreate, QuestResponse, UserQuestResponse 
from app.schemas.user import UserResponse
from app.auth import get_current_user # Adjust path as needed
from app.utils.time import is_within_active_hours  # Adjust path as needed
from app.models.user_quest import UserQuest, QuestStatus
from app.models.submission import QuestSubmission, VerificationStatus
from app.services.image_validator import verify_image_metadata, check_submission_cooldown
from app.schemas.quest import UserQuestResponse
from app.schemas.submission import QuestSubmissionResponse
router = APIRouter(prefix="/quests", tags=["Quests"])


# --- Helper: Admin Role Dependency ---
async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to ensure the current user is an administrator."""
    if not getattr(current_user, "is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required for this action."
        )
    return current_user


# ==========================================
# ADMIN ENDPOINTS
# ==========================================

@router.get("/all", response_model=List[QuestResponse])
async def get_all_quests_admin(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """[Admin Only] Retrieve all quest templates in the master database."""
    result = await db.execute(select(Quest))
    return result.scalars().all()


@router.get("/getAllUsers", response_model=List[UserResponse])
async def get_all_userss_admin(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """[Admin Only] Retrieve all quest templates in the master database."""
    result = await db.execute(select(User))
    return result.scalars().all()





@router.post("/addQuest", response_model=QuestResponse, status_code=status.HTTP_201_CREATED)
async def create_quest_admin(
    quest_in: QuestCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """[Admin Only] Create a new side quest template."""
    new_quest = Quest(
        title=quest_in.title,
        description=quest_in.description,
        prompt=quest_in.prompt,
        points_reward=quest_in.points_reward,
        total_days=quest_in.total_days
    )
    db.add(new_quest)
    await db.commit()
    await db.refresh(new_quest)
    return new_quest

# ==========================================
# USER ENDPOINTS
# ==========================================

@router.get("/daily", response_model=List[QuestResponse])
async def get_daily_quests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get 2 daily quests selected specifically for today."""
    result = await db.execute(select(Quest).where(Quest.is_active == True))
    all_quests = result.scalars().all()

    if not all_quests:
        return []

    if len(all_quests) <= 2:
        return all_quests

    # Seed RNG using user's ID + current date so the 2 quests remain consistent for the user throughout today
    seed_value = f"{current_user.id}-{date.today().isoformat()}"
    rng = random.Random(seed_value)
    
    return rng.sample(all_quests, 2)


@router.post("/accept/{quest_id}", response_model=UserQuestResponse)
async def accept_quest(
    quest_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Accept a daily quest template into an active UserQuest track."""
    result = await db.execute(select(Quest).where(Quest.id == quest_id, Quest.is_active == True))
    quest = result.scalars().first()
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")

    # Check for active quest
    existing = await db.execute(
        select(UserQuest).where(
            UserQuest.user_id == current_user.id,
            UserQuest.quest_id == quest_id,
            UserQuest.status == QuestStatus.ACTIVE
        )
    )
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Quest already active")

    # Create UserQuest using enum and total steps from quest model
    user_quest = UserQuest(
        user_id=current_user.id,
        quest_id=quest.id,
        status=QuestStatus.ACTIVE,
        current_step=1,
        total_steps=quest.total_days
    )
    db.add(user_quest)
    await db.commit()

    # Return with relations loaded
    res = await db.execute(
        select(UserQuest)
        .options(selectinload(UserQuest.quest), selectinload(UserQuest.submissions))
        .where(UserQuest.id == user_quest.id)
    )
    return res.scalars().first()




@router.get("/active", response_model=List[UserQuestResponse])
async def get_active_quests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve current user's active (accepted & uncompleted) quests."""
    result = await db.execute(
        select(UserQuest)
        .options(selectinload(UserQuest.quest))
        .where(
            UserQuest.user_id == current_user.id,
            UserQuest.is_completed == False
        )
    )
    return result.scalars().all()


@router.post("/complete/{user_quest_id}", response_model=UserQuestResponse)
async def complete_quest(
    user_quest_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Complete an accepted active quest and receive points."""
    result = await db.execute(
        select(UserQuest)
        .options(selectinload(UserQuest.quest))
        .where(
            UserQuest.id == user_quest_id,
            UserQuest.user_id == current_user.id
        )
    )
    user_quest = result.scalars().first()

    if not user_quest:
        raise HTTPException(status_code=404, detail="Active quest not found")

    if user_quest.is_completed:
        raise HTTPException(status_code=400, detail="Quest is already completed")

    # Mark quest as completed
    user_quest.is_completed = True

    # Award points to the current user (if your User model tracks points)
    if hasattr(current_user, "points") and user_quest.quest:
        current_user.points += user_quest.quest.points_reward

    await db.commit()
    await db.refresh(user_quest)

    return user_quest


# --- 2. New Submission Endpoint (Preps Phase 3 AI Pipeline) ---
@router.post("/submit/{user_quest_id}", response_model=QuestSubmissionResponse)
async def submit_quest_step(
    user_quest_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit image proof with EXIF validation, cooldown rate-limiting, and AI verification."""
    
    # 1. Fetch UserQuest with related Quest and prior Submissions
    result = await db.execute(
        select(UserQuest)
        .options(
            selectinload(UserQuest.quest),
            selectinload(UserQuest.submissions)
        )
        .where(UserQuest.id == user_quest_id, UserQuest.user_id == current_user.id)
    )
    user_quest = result.scalars().first()

    if not user_quest or user_quest.status != QuestStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="No active quest found with this ID")

    # 2. Rate-limiting check: Prevent spamming submissions within 60 seconds
    if user_quest.submissions:
        latest_sub = max(user_quest.submissions, key=lambda s: s.submitted_at)
        check_submission_cooldown(latest_sub.submitted_at)

    # 3. Save image temporarily to disk for validation & AI inspection
    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/{uuid.uuid4()}_{file.filename}"
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    # 4. Run EXIF Fraud Prevention Check
    try:
        verify_image_metadata(file_path)
    except HTTPException:
        # Clean up file if validation fails
        if os.path.exists(file_path):
            os.remove(file_path)
        raise

    # 5. Format previous submission history context for Gemini
    past_subs = [
        {
            "step_number": sub.step_number,
            "feedback": sub.ai_feedback,
            "image_path": sub.image_path
        }
        for sub in user_quest.submissions
        if sub.ai_status == VerificationStatus.PASSED
    ]

    # 6. Call AI Vision Verification
    try:
        ai_result = await verify_quest_submission(
            current_image_path=file_path,
            quest_title=user_quest.quest.title,
            quest_description=user_quest.quest.description,
            system_prompt=user_quest.quest.prompt,
            previous_submissions=past_subs
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"AI verification failed to execute: {str(e)}"
        )

    # 7. Create submission record
    verification_status = (
        VerificationStatus.PASSED if ai_result.passed else VerificationStatus.REJECTED
    )
    
    submission = QuestSubmission(
        user_quest_id=user_quest.id,
        step_number=user_quest.current_step,
        image_path=file_path,
        ai_status=verification_status,
        ai_feedback=ai_result.feedback
    )
    db.add(submission)

    # 8. Increment progress ONLY if verification PASSED
    if ai_result.passed:
        if user_quest.current_step >= user_quest.total_steps:
            user_quest.status = QuestStatus.COMPLETED
            current_user.score += user_quest.quest.points_reward
        else:
            user_quest.current_step += 1

    await db.commit()
    await db.refresh(submission)
    return submission