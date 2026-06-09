import uuid
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from api.database import get_async_db
from api.models import User, Tenant
from utils.security import hash_password, verify_password, create_access_token
from utils.auth import ClerkUser, get_current_user

router = APIRouter()

class RegisterRequest(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    company_name: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class UserProfileResponse(BaseModel):
    id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str
    tenant_id: Optional[str] = None

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_async_db)):
    """Register a new user, auto-provisions a secure tenant space, and returns an access token."""
    # Check if user exists
    user_stmt = select(User).where(User.email == req.email.lower().strip())
    res = await db.execute(user_stmt)
    if res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    # 1. Create Tenant
    tenant_name = req.company_name or f"{req.first_name}'s Advisory Firm"
    new_tenant = Tenant(
        id=str(uuid.uuid4()),
        company_name=tenant_name,
        subscription_tier="free",
        subscription_status="active"
    )
    db.add(new_tenant)
    await db.flush()

    # 2. Create User
    custom_clerk_id = f"usr_local_{uuid.uuid4().hex[:12]}"
    new_user = User(
        id=str(uuid.uuid4()),
        tenant_id=new_tenant.id,
        email=req.email.lower().strip(),
        clerk_user_id=custom_clerk_id,
        hashed_password=hash_password(req.password),
        first_name=req.first_name,
        last_name=req.last_name,
        role="admin"
    )
    db.add(new_user)
    await db.commit()

    # 3. Create Token
    token_data = {
        "sub": new_user.clerk_user_id,
        "email": new_user.email,
        "first_name": new_user.first_name,
        "last_name": new_user.last_name
    }
    access_token = create_access_token(data=token_data)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_async_db)):
    """Validate username and password, issuing a standard JWT session access token."""
    # Find user
    user_stmt = select(User).where(User.email == req.email.lower().strip())
    res = await db.execute(user_stmt)
    user = res.scalar_one_or_none()

    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    # Issue Token
    token_data = {
        "sub": user.clerk_user_id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name
    }
    access_token = create_access_token(data=token_data)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserProfileResponse)
async def get_me(
    current_user: ClerkUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Retrieve details of the currently authenticated user profile."""
    user_stmt = select(User).where(User.clerk_user_id == current_user.clerk_id)
    res = await db.execute(user_stmt)
    user = res.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found."
        )

    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role,
        "tenant_id": user.tenant_id
    }
