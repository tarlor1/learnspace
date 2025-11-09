import os
from typing import Optional, Dict, Any
from functools import lru_cache
from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWKClient
from jwt.exceptions import (
    ExpiredSignatureError,
    InvalidAudienceError,
    InvalidTokenError,
)
from dotenv import load_dotenv

load_dotenv()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")

if not all([AUTH0_DOMAIN, AUTH0_AUDIENCE]):
    raise ValueError("AUTH0_DOMAIN and AUTH0_AUDIENCE must be set in .env")

ISSUER = f"https://{AUTH0_DOMAIN}/"
JWKS_URL = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
ALGORITHMS = ["RS256"]

security = HTTPBearer()

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


@lru_cache(maxsize=1)
def get_jwk_client() -> PyJWKClient:
    return PyJWKClient(JWKS_URL)


def verify_token(token: str) -> Dict[str, Any]:
    """Verify RS256 Auth0 JWT using JWKS."""
    try:
        jwk_client = get_jwk_client()
        signing_key = jwk_client.get_signing_key_from_jwt(token).key
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=ALGORITHMS,
            audience=AUTH0_AUDIENCE,
            issuer=ISSUER,
            options={"verify_exp": True},
        )
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except InvalidAudienceError:
        raise HTTPException(status_code=401, detail="Invalid audience")
    except InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {e}")


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Dict[str, Any]:
    """
    FastAPI dependency to get current authenticated user

    Args:
        credentials: HTTP bearer token from request header

    Returns:
        User info from decoded token

    Raises:
        HTTPException: If authentication fails
    """
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authorization token missing")

    token = credentials.credentials
    payload = verify_token(token)
    return payload


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
) -> Optional[dict]:
    """
    FastAPI dependency to get current user if authenticated, None otherwise
    Useful for optional authentication on public endpoints

    Args:
        credentials: HTTP bearer token from request header (optional)

    Returns:
        User info from decoded token or None
    """
    if credentials is None:
        return None

    try:
        token = credentials.credentials
        payload = verify_token(token)
        return payload
    except HTTPException:
        return None


@router.get("/me", response_model=dict)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Returns the profile of the currently authenticated user.
    """
    return current_user
