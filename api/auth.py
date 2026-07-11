import os
from datetime import datetime, timedelta, UTC

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
from pydantic import BaseModel


load_dotenv()

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()

ADMIN_USER = os.getenv("SAPIENTIA_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("SAPIENTIA_ADMIN_PASSWORD", "admin123")
JWT_SECRET = os.getenv("SAPIENTIA_JWT_SECRET", "local-dev-secret")
JWT_ALGORITHM = os.getenv("SAPIENTIA_JWT_ALGORITHM", "HS256")


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(payload: LoginRequest):
    if payload.username != ADMIN_USER or payload.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    expires_at = datetime.now(UTC) + timedelta(hours=8)

    token = jwt.encode(
        {
            "sub": payload.username,
            "exp": expires_at,
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }


def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )
        return payload

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")