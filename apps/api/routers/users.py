"""User management router."""

from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import hashlib
import secrets

from database import DatabaseManager

router = APIRouter(prefix="/users", tags=["users"])


class UserResponse(BaseModel):
    """User response model."""
    id: int
    username: str
    email: Optional[str] = None
    role: str
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    expires_at: Optional[str] = None
    last_login: Optional[str] = None
    login_attempts: int = 0
    
    # Additional fields for admin dashboard
    last_seen_at: Optional[str] = None
    monthly_token_limit: int = 100000
    monthly_cost_cap: float = 50.0
    mfa_enabled: bool = False


class CreateUserRequest(BaseModel):
    """Create user request model."""
    username: str = Field(..., min_length=1, max_length=50)
    email: str
    password: str = Field(..., min_length=6)
    role: str = Field("user", pattern="^(admin|user|editor|viewer|owner|service)$")
    expires_at: Optional[str] = None
    monthly_token_limit: int = Field(100000, ge=1000)
    monthly_cost_cap: float = Field(50.0, ge=1.0)


class UpdateUserRequest(BaseModel):
    """Update user request model."""
    username: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[str] = None
    role: Optional[str] = Field(None, pattern="^(admin|user|editor|viewer|owner|service)$")
    is_active: Optional[bool] = None
    expires_at: Optional[str] = None
    monthly_token_limit: Optional[int] = Field(None, ge=1000)
    monthly_cost_cap: Optional[float] = Field(None, ge=1.0)
    mfa_enabled: Optional[bool] = None


def _format_user_response(db_user) -> UserResponse:
    """Format database user to response model."""
    # Calculate last_seen_at from last_login
    last_seen_at = None
    if db_user.last_login:
        try:
            last_login_dt = datetime.fromisoformat(db_user.last_login.replace('Z', '+00:00'))
            now = datetime.now()
            diff = now - last_login_dt
            
            if diff.days > 0:
                last_seen_at = f"{diff.days}일 전"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                last_seen_at = f"{hours}시간 전"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                last_seen_at = f"{minutes}분 전"
            else:
                last_seen_at = "방금 전"
        except:
            last_seen_at = "알 수 없음"
    else:
        last_seen_at = "로그인 기록 없음"
    
    return UserResponse(
        id=db_user.id,
        username=db_user.username,
        email=db_user.email,
        role=db_user.role,
        is_active=db_user.is_active,
        created_at=db_user.created_at,
        updated_at=db_user.updated_at,
        expires_at=db_user.expires_at,
        last_login=db_user.last_login,
        login_attempts=db_user.login_attempts,
        last_seen_at=last_seen_at,
        monthly_token_limit=100000 if db_user.role == "user" else 500000 if db_user.role == "editor" else 1000000,
        monthly_cost_cap=50.0 if db_user.role == "user" else 200.0 if db_user.role == "editor" else 500.0,
        mfa_enabled=db_user.role in ["admin", "owner"]  # Simulate MFA based on role
    )


@router.get("/", response_model=List[UserResponse])
async def list_users():
    """List all users."""
    try:
        db = DatabaseManager()
        db_users = db.get_all_users()
        
        users = [_format_user_response(user) for user in db_users]
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list users: {str(e)}")


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """Get user by ID."""
    try:
        db = DatabaseManager()
        db_user = db.get_user_by_id(user_id)
        
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return _format_user_response(db_user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user: {str(e)}")


@router.post("/", response_model=UserResponse)
async def create_user(user_data: CreateUserRequest):
    """Create a new user."""
    try:
        db = DatabaseManager()
        
        # Check if username or email already exists
        existing_user = db.get_user_by_username(user_data.username)
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Hash password
        password_hash = hashlib.sha256(user_data.password.encode()).hexdigest()
        
        # Create user
        from database import User
        new_user = User(
            username=user_data.username,
            password_hash=password_hash,
            email=user_data.email,
            role=user_data.role,
            is_active=True,
            created_at=datetime.now().isoformat(),
            expires_at=user_data.expires_at
        )
        
        user_id = db.create_user_from_object(new_user)
        created_user = db.get_user_by_id(user_id)
        
        return _format_user_response(created_user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_data: UpdateUserRequest):
    """Update user."""
    try:
        db = DatabaseManager()
        
        # Get existing user
        existing_user = db.get_user_by_id(user_id)
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update fields that were provided
        if user_data.username is not None:
            existing_user.username = user_data.username
        if user_data.email is not None:
            existing_user.email = user_data.email
        if user_data.role is not None:
            existing_user.role = user_data.role
        if user_data.is_active is not None:
            existing_user.is_active = user_data.is_active
        if user_data.expires_at is not None:
            existing_user.expires_at = user_data.expires_at
        
        existing_user.updated_at = datetime.now().isoformat()
        
        db.update_user(existing_user)
        updated_user = db.get_user_by_id(user_id)
        
        return _format_user_response(updated_user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")


@router.delete("/{user_id}")
async def delete_user(user_id: int):
    """Delete user."""
    try:
        db = DatabaseManager()
        
        # Get existing user
        existing_user = db.get_user_by_id(user_id)
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Don't allow deleting admin users
        if existing_user.role == "admin":
            raise HTTPException(status_code=400, detail="Cannot delete admin users")
        
        db.delete_user(user_id)
        return {"message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")


@router.post("/{user_id}/reset-password")
async def reset_password(user_id: int):
    """Reset user password."""
    try:
        db = DatabaseManager()
        
        # Get existing user
        existing_user = db.get_user_by_id(user_id)
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Generate new temporary password
        temp_password = secrets.token_urlsafe(12)
        password_hash = hashlib.sha256(temp_password.encode()).hexdigest()
        
        existing_user.password_hash = password_hash
        existing_user.updated_at = datetime.now().isoformat()
        
        db.update_user(existing_user)
        
        return {
            "message": "Password reset successfully",
            "temporary_password": temp_password,
            "note": "User should change this password on next login"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset password: {str(e)}")