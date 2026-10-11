import uuid
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., max_length=72)
    age: int = Field(..., ge=4, le=18)  # Tailored for kids/teens

class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    age: int
    score: int
    current_streak: int
    is_admin: bool

    class Config:
        from_attributes = True