"""FastAPI main application."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Any, Optional
import secrets

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from packages.core.config import get_settings
from packages.core.database import create_tables
from apps.api.routers import bundles, generation, publishing, health, users, workflows, scheduled_posts
from database import DatabaseManager

SESSIONS = {}

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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    await create_tables()
    yield


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="AI Writer API",
        description="AI-based automatic blog posting system",
        version="0.1.0",
        lifespan=lifespan
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3002", "http://127.0.0.1:3002", "http://localhost:3001", "http://127.0.0.1:3001", "http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(bundles.router, prefix="/api/v1")
    app.include_router(generation.router, prefix="/api/v1")
    app.include_router(publishing.router, prefix="/api/v1")
    app.include_router(users.router, prefix="/api/v1")
    app.include_router(workflows.router, prefix="/api/v1")
    app.include_router(scheduled_posts.router, prefix="/api/v1")
    
    # Auth endpoints directly in main
    @app.post("/api/v1/auth/login", response_model=LoginResponse)
    async def login(request: LoginRequest):
        try:
            print(f"DEBUG: Login attempt for username: '{request.username}', password: '{request.password}'")
            db = DatabaseManager()
            success, user, message = db.verify_user_password(request.username, request.password)
            print(f"DEBUG: Auth result - success: {success}, user: {user}, message: {message}")
            
            if not success:
                return LoginResponse(success=False, message=message)
            
            # 사용자 정보를 딕셔너리로 변환
            user_data = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
            
            token = secrets.token_hex(32)
            SESSIONS[token] = user_data
            
            return LoginResponse(
                success=True,
                message="Login successful",
                token=token,
                user=user_data
            )
        except Exception as e:
            print(f"DEBUG: Exception during login: {e}")
            import traceback
            traceback.print_exc()
            return LoginResponse(success=False, message=f"Login failed: {str(e)}")
    
    @app.get("/api/v1/auth/validate", response_model=AuthValidateResponse)
    async def validate_token():
        return AuthValidateResponse(valid=True, user={"username": "admin", "role": "admin"})
    
    @app.post("/api/v1/auth/logout")
    async def logout():
        return {"success": True, "message": "Logged out successfully"}
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )