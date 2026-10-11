import asyncio
import sys
from sqlalchemy.future import select

from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.quest import Quest# Pre-loads relationships into SQLAlchemy registry
from app.models.user_quest import UserQuest  # Pre-loads relationships into SQLAlchemy registry
async def make_admin(email: str):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalars().first()

        if not user:
            print(f"Error: User with email '{email}' not found.")
            return

        user.is_admin = True
        await db.commit()
        print(f"Success: User '{email}' is now an admin!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m app.Scripts.set_admin <user_email>")
        sys.exit(1)

    target_email = sys.argv[1]
    asyncio.run(make_admin(target_email))