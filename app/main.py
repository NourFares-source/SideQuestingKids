from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config import settings
from app.database import engine
from app.routers import auth
from app.routers import quests
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup Logic ---
    print("[FastAPI] Application starting up...")
    # Optional: Verify database connection on startup
    async with engine.begin() as conn:
        pass
    print("[FastAPI] Database connection initialized.")
    
    yield  # Application runs while sitting at yield
    
    # --- Shutdown Logic ---
    print("[FastAPI] Application shutting down...")
    await engine.dispose()
    print("[FastAPI] Database engine disposed.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

app.include_router(auth.router)
app.include_router(quests.router)

@app.get("/")
async def root():
    return {"status": "online", "message": "SideQuest API is running"}