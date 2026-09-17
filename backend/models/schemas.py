from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any


class LoginRequest(BaseModel):
    email: EmailStr


class LoginResponse(BaseModel):
    user_id: int
    email: str


class AnalyzeRequest(BaseModel):
    user_id: int
    language: str = Field(pattern="^(python|java|cpp|c)$")
    code: str
    mode: str = Field(default="beginner", pattern="^(beginner|developer)$")


class ReviewRequest(BaseModel):
    user_id: int
    rating: int = Field(ge=1, le=5)
    feedback: Optional[str] = ""


class HistoryItem(BaseModel):
    id: int
    language: str
    summary: Optional[str]
    quality_score: Optional[int]
    created_at: str
