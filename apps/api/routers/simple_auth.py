"""Simple authentication router."""

import secrets
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

router = APIRouter(tags=["auth"])
security = HTTPBearer(auto_error=False)

# 간단한 인메모리 사용자 데이터
USERS = {
    "admin": {
        "password": "admin123!",
        "role": "admin",
        "id": 1,
        "username": "admin",
        "email": "admin@company.com"
    }
}

# 세션 토큰 저장
SESSIONS = {}

# Request/Response models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None
    user: Optional[Dict[str, Any]] = None

class AuthValidateResponse(BaseModel):
    valid: bool
    user: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

class SimpleUser:
    def __init__(self, id, username, email, role):
        self.id = id
        self.username = username
        self.email = email
        self.role = role

@router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """User login endpoint."""
    try:
        # Check credentials
        if request.username not in USERS:
            return LoginResponse(
                success=False,
                message="Invalid username"
            )
        
        user_data = USERS[request.username]
        if user_data["password"] != request.password:
            return LoginResponse(
                success=False,
                message="Invalid password"
            )
        
        # Create session token
        token = secrets.token_hex(32)
        SESSIONS[token] = SimpleUser(
            user_data["id"],
            user_data["username"], 
            user_data["email"],
            user_data["role"]
        )
        
        return LoginResponse(
            success=True,
            message="Login successful",
            token=token,
            user={
                "id": user_data["id"],
                "username": user_data["username"],
                "email": user_data["email"],
                "role": user_data["role"]
            }
        )
        
    except Exception as e:
        print(f"Login error: {e}")
        return LoginResponse(
            success=False,
            message="Login failed due to server error"
        )

@router.get("/auth/validate", response_model=AuthValidateResponse)
async def validate_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Token validation endpoint."""
    if not credentials:
        return AuthValidateResponse(
            valid=False,
            message="No token provided"
        )
    
    token = credentials.credentials
    if token not in SESSIONS:
        return AuthValidateResponse(
            valid=False,
            message="Invalid or expired token"
        )
    
    user = SESSIONS[token]
    return AuthValidateResponse(
        valid=True,
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
    )

@router.post("/auth/logout")
async def logout(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """User logout endpoint."""
    if credentials and credentials.credentials in SESSIONS:
        del SESSIONS[credentials.credentials]
    
    return {"success": True, "message": "Logged out successfully"}