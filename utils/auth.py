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
    Enterprise-grade dependency injection validation of Clerk JWTs.
    Clean sandbox fallbacks are enabled for local development.
    Supports token retrieval from both headers and query parameters (for direct anchor link actions).
    """
    jwt_token = None
    if authorization:
        try:
            scheme, jwt_token = authorization.split(" ", 1)
            if scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=401,
                    detail="Authentication failed: Authorization scheme must be Bearer."
                )
        except ValueError:
            raise HTTPException(
                status_code=401,
                detail="Authentication failed: Invalid authorization header format."
            )
    elif token:
        jwt_token = token

    # 1. If we have a token, attempt to validate it (preferring HS256 custom tokens)
    if jwt_token:
        # Try custom HS256 JWT decoding first
        try:
            payload = jwt.decode(
                jwt_token,
                config.SECRET_KEY,
                algorithms=["HS256"]
            )
            clerk_id = payload.get("sub")
            email = payload.get("email")
            if not clerk_id or not email:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication failed: Invalid custom token claims."
                )
            return ClerkUser(
                clerk_id=clerk_id,
                email=email,
                first_name=payload.get("first_name"),
                last_name=payload.get("last_name")
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=401,
                detail="Authentication failed: JWT session has expired."
            )
        except jwt.InvalidSignatureError:
            # Signature verification failed - it might be a Clerk RS256 token
            pass
        except jwt.InvalidTokenError as err:
            raise HTTPException(
                status_code=401,
                detail=f"Authentication failed: Invalid token - {str(err)}"
            )

        # Fallback to Clerk RS256 decoding if configured
        if config.CLERK_JWT_VERIFICATION_KEY and config.CLERK_JWT_VERIFICATION_KEY != "clerk_jwt_key_here":
            try:
                payload = jwt.decode(
                    jwt_token,
                    config.CLERK_JWT_VERIFICATION_KEY,
                    algorithms=["RS256"],
                    options={"verify_aud": False}
                )
                clerk_id = payload.get("sub")
                email = payload.get("email")
                if not clerk_id or not email:
                    raise HTTPException(
                        status_code=401,
                        detail="Authentication failed: Invalid Clerk token claims."
                    )
                return ClerkUser(
                    clerk_id=clerk_id,
                    email=email,
                    first_name=payload.get("first_name"),
                    last_name=payload.get("last_name")
                )
            except jwt.ExpiredSignatureError:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication failed: Clerk session has expired."
                )
            except jwt.InvalidTokenError as jwt_err:
                raise HTTPException(
                    status_code=401,
                    detail=f"Authentication failed: Invalid Clerk token - {str(jwt_err)}"
                )

        raise HTTPException(
            status_code=401,
            detail="Authentication failed: Invalid token signature (Clerk is not configured)."
        )

    # 2. Fallback to developer mock session in local/sandbox environments (Non-Production)
    # Triggered if no token is provided and Clerk domain secrets are not configured or hold defaults
    if config.ENVIRONMENT != "production" and (not config.CLERK_JWT_VERIFICATION_KEY or config.CLERK_JWT_VERIFICATION_KEY == "clerk_jwt_key_here"):
        # Simulate active session validation
        return ClerkUser(
            clerk_id="user_mock_123",
            email="advisor@example.com",
            first_name="Advisor",
            last_name="Demo"
        )

    raise HTTPException(
        status_code=401,
        detail="Authentication failed: Authorization header or token query parameter is missing."
    )
