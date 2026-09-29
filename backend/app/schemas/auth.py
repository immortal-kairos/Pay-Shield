from pydantic import BaseModel, EmailStr, Field, ConfigDict
from uuid import UUID
from app.models.user import UserRole

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: UserRole
    org_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: UUID
    org_id: UUID
    email: EmailStr
    role: UserRole
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str