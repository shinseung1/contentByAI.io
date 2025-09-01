"""Authentication endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime, timedelta
import hashlib
import secrets

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()

# Request/Response models
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]

class UserResponse(BaseModel):
    id: str
    email: str
    name: str

# Mock data for development
MOCK_USERS = {
    "admin@example.com": {
        "id": "1",
        "email": "admin@example.com", 
        "password": "password123",
        "name": "Admin User"
    }
}

# Simple token storage for development
ACTIVE_TOKENS = {}

def create_access_token(user_data: Dict[str, Any]) -> str:
    """Create simple access token."""
    token = secrets.token_urlsafe(32)
    expire_time = datetime.utcnow() + timedelta(hours=24)
    ACTIVE_TOKENS[token] = {
        "user_data": user_data,
        "expires_at": expire_time
    }
    return token

def verify_token(token: str) -> Dict[str, Any]:
    """Verify simple access token."""
    token_data = ACTIVE_TOKENS.get(token)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    if datetime.utcnow() > token_data["expires_at"]:
        del ACTIVE_TOKENS[token]
        raise HTTPException(status_code=401, detail="Token expired")
    
    return token_data["user_data"]

@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """Login endpoint."""
    user = MOCK_USERS.get(request.email)
    
    if not user or user["password"] != request.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user_data = {"id": user["id"], "email": user["email"], "name": user["name"]}
    access_token = create_access_token(user_data)
    
    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_data
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user(token: str = Depends(security)):
    """Get current user info."""
    payload = verify_token(token.credentials)
    user = MOCK_USERS.get(payload["email"])
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user["id"],
        email=user["email"],
        name=user["name"]
    )

@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest):
    """Register new user."""
    if request.email in MOCK_USERS:
        raise HTTPException(status_code=400, detail="User already exists")
    
    user_id = str(len(MOCK_USERS) + 1)
    new_user = {
        "id": user_id,
        "email": request.email,
        "password": request.password,
        "name": request.name
    }
    
    MOCK_USERS[request.email] = new_user
    
    user_data = {"id": user_id, "email": request.email, "name": request.name}
    access_token = create_access_token(user_data)
    
    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_data
    )