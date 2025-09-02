"""Authentication router."""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import secrets

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from fastapi import HTTPException
from pydantic import BaseModel

# 임시로 간단한 인증 시스템 사용
USERS = {
    "admin": {
        "password": "admin123!",
        "role": "admin",
        "id": 1,
        "username": "admin",
        "email": "admin@company.com"
    }
}

SESSIONS = {}

class SimpleUser:
    def __init__(self, id, username, email, role):
        self.id = id
        self.username = username
        self.email = email
        self.role = role

router = APIRouter(tags=["auth"])
security = HTTPBearer()

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

def generate_session_token() -> str:
    """세션 토큰 생성"""
    return secrets.token_urlsafe(32)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """현재 인증된 사용자 반환"""
    token = credentials.credentials
    user = db.validate_session(token)
    
    if not user:
        raise HTTPException(
            status_code=401, 
            detail="Invalid or expired session token"
        )
    
    return user

@router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """로그인"""
    try:
        # 사용자 인증
        is_valid, user, error_message = db.verify_user_password(request.username, request.password)
        
        if not is_valid:
            return LoginResponse(
                success=False,
                message=error_message
            )
        
        # 세션 생성 (토큰은 자동 생성됨)
        token = db.create_session(user.id)
        
        # 로그인 시도 횟수 초기화 (메서드가 있는 경우)
        try:
            db.reset_failed_attempts(user.username)
        except AttributeError:
            pass  # 메서드가 없으면 무시
        
        return LoginResponse(
            success=True,
            message="로그인 성공",
            token=token,
            user={
                "username": user.username,
                "role": user.role,
                "isActive": user.is_active,
                "expiresAt": user.expires_at
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@router.post("/auth/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """로그아웃"""
    try:
        token = credentials.credentials
        db.delete_session(token)
        return {"success": True, "message": "로그아웃 되었습니다"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")

@router.get("/auth/validate", response_model=AuthValidateResponse)
async def validate_token(current_user: User = Depends(get_current_user)):
    """토큰 유효성 검증"""
    try:
        return AuthValidateResponse(
            valid=True,
            user={
                "username": current_user.username,
                "role": current_user.role,
                "isActive": current_user.is_active,
                "expiresAt": current_user.expires_at
            }
        )
    except Exception as e:
        return AuthValidateResponse(
            valid=False,
            message=str(e)
        )