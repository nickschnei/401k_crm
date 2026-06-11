from fastapi import HTTPException, Header, Depends, Query
from pydantic import BaseModel
import jwt
import config
from typing import Optional

class ClerkUser(BaseModel):
    clerk_id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

async def get_current_user(
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None)
) -> ClerkUser:
    """
    Open-access bypass: Always returns a default mock user for passwordless public access.
    """
    return ClerkUser(
        clerk_id="user_mock_123",
        email="advisor@example.com",
        first_name="Advisor",
        last_name="Demo"
    )
