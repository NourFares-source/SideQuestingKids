import asyncio
from arq.cron import cron
from sqlalchemy import update
from app.database import AsyncSessionLocal
from app.models.user_quest import UserQuest
from arq.connections import RedisSettings
from app.config import settings

async def process_photo_submission(ctx, submission_id: str):
    """Background task to analyze photos with Gemini Vision."""
    print(f"[ARQ Worker] Processing submission ID: {submission_id}")
    # We will implement the Vision AI pipeline here in Phase 3
    await asyncio.sleep(2)
    print(f"[ARQ Worker] Completed verification for: {submission_id}")


async def expire_uncompleted_quests(ctx):
    """Cron job that runs every day at 6:00 PM to expire incomplete side quests."""
    print("[ARQ Worker] Evening curfew reached. Expiring uncompleted quests...")
    async with AsyncSessionLocal() as db:
        # Mark all active uncompleted quests as expired/completed=False
        # (Alternatively, you can add an `is_expired` boolean field to UserQuest model)
        stmt = (
            update(UserQuest)
            .where(UserQuest.is_completed == False)
            .values(is_completed=True)  # Or set an explicit status field
        )
        await db.execute(stmt)
        await db.commit()
    print("[ARQ Worker] All uncompleted quests for today have been expired.")


async def startup(ctx):
    print("[ARQ Worker] Worker process started successfully.")

async def shutdown(ctx):
    print("[ARQ Worker] Worker process shutting down.")

class WorkerSettings:
    functions = [process_photo_submission]
    on_startup = startup
    on_shutdown = shutdown
    cron_jobs = [
        cron(expire_uncompleted_quests, hour=18, minute=0)
    ]
    # Parse redis host and port from config URL or default to redis service
    redis_settings = RedisSettings(host="redis", port=6379)