from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


# ---- Request Schemas ----

class UserCreate(BaseModel):
    """Data needed to register a new user."""
    username: str = Field(..., min_length=3, max_length=50, examples=["john_doe"])
    email: EmailStr = Field(..., examples=["john@example.com"])
    password: str = Field(..., min_length=8, examples=["strongpassword123"])


class UserLogin(BaseModel):
    """Data for login."""
    username: str = Field(..., examples=["john_doe"])
    password: str = Field(..., examples=["strongpassword123"])


# ---- Response Schemas ----

class UserResponse(BaseModel):
    """Public user information returned after registration or in profile."""
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime

    # This tells Pydantic to read data from an ORM object (SQLAlchemy model)
    model_config = {"from_attributes": True}


class Token(BaseModel):
    """JWT access token response."""
    access_token: str
    token_type: str = "bearer"
