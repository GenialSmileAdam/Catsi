from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token
from app.core.rate_limiter import limiter, user_limiter
from app.api.v1.dependencies import get_db
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    # Check if username or email already exists

    existing = await db.execute(
        select(User).where(
            or_(
                User.username == user_data.username,
                User.email == user_data.email,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already registered",
        )

    # Create user object with hashed password
    hashed_pw = hash_password(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_pw,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)   # get the id and timestamps from DB
    return db_user


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(
        request : Request,
        user_data: UserLogin,
        db: AsyncSession = Depends(get_db),
        ):
    """Authenticate user and return JWT token."""
    # Find user by username
    result = await db.execute(select(User).where(User.username == user_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Create access token with subject = username
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}