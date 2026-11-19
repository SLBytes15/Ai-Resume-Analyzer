from pydantic import BaseModel, EmailStr, Field
from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, description="User password")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
