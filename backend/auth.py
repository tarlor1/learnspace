import os
from typing import Optional
from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWKClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.local")

# Auth0 configuration
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", f"https://{AUTH0_DOMAIN}/api/v2/")

if not AUTH0_DOMAIN:
    raise ValueError("AUTH0_DOMAIN must be set in environment variables")

if not AUTH0_AUDIENCE:
    raise ValueError("AUTH0_AUDIENCE must be set in environment variables")

# JWT configuration
ALGORITHMS = ["RS256"]
ISSUER = f"https://{AUTH0_DOMAIN}/"

# Security scheme
security = HTTPBearer()

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


class AuthError(Exception):
    """Custom exception for auth errors"""

    def __init__(self, error: dict, status_code: int):
        self.error = error
        self.status_code = status_code


def verify_token(token: str) -> dict:
    """
    Verify Auth0 JWT token

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        AuthError: If token is invalid
    """
    try:
        # Get the public key from Auth0
        jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
        jwks_client = PyJWKClient(jwks_url)

        # Get signing key
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        # Decode and verify token
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=ALGORITHMS,
            audience=AUTH0_AUDIENCE,
            issuer=ISSUER,
        )

        return payload

    except jwt.ExpiredSignatureError:
        raise AuthError(
            {"code": "token_expired", "description": "Token has expired"}, 401
        )
    except (jwt.InvalidAudienceError, jwt.InvalidIssuerError):
        raise AuthError(
            {
                "code": "invalid_claims",
                "description": "Incorrect claims, please check the audience and issuer",
            },
            401,
        )
    except Exception as e:
        raise AuthError(
            {
                "code": "invalid_token",
                "description": f"Unable to parse authentication token: {str(e)}",
            },
            401,
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    FastAPI dependency to get current authenticated user

    Args:
        credentials: HTTP bearer token from request header

    Returns:
        User info from decoded token

    Raises:
        HTTPException: If authentication fails
    """
    try:
        token = credentials.credentials
        payload = verify_token(token)
        return payload
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.error,
        )


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
    except AuthError:
        return None


@router.get("/me", response_model=dict)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Returns the profile of the currently authenticated user.
    """
    return current_user
