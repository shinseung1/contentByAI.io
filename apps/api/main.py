"""FastAPI main application."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Any, Optional
import secrets

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from packages.core.config import get_settings
from packages.core.database import create_tables
from apps.api.routers import bundles, publishing, health
from apps.api.routers import generation_simple as generation

# 간단한 인메모리 인증
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
        allow_origins=["*"],
        allow_credentials=False,  # credentials를 false로 변경
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(bundles.router, prefix="/api/v1")
    app.include_router(generation.router, prefix="/api/v1")
    app.include_router(publishing.router, prefix="/api/v1")
    
    # Auth endpoints directly in main
    @app.post("/api/v1/auth/login", response_model=LoginResponse)
    async def login(request: LoginRequest):
        try:
            if request.username not in USERS:
                return LoginResponse(success=False, message="Invalid username")
            
            user_data = USERS[request.username]
            if user_data["password"] != request.password:
                return LoginResponse(success=False, message="Invalid password")
            
            token = secrets.token_hex(32)
            SESSIONS[token] = user_data
            
            return LoginResponse(
                success=True,
                message="Login successful",
                token=token,
                user=user_data
            )
        except Exception as e:
            return LoginResponse(success=False, message=f"Login failed: {str(e)}")
    
    @app.get("/api/v1/auth/validate", response_model=AuthValidateResponse)
    async def validate_token():
        return AuthValidateResponse(valid=True, user={"username": "admin", "role": "admin"})
    
    @app.post("/api/v1/auth/logout")
    async def logout():
        return {"success": True, "message": "Logged out successfully"}
    
    # Add simple test endpoint
    @app.get("/api/v1/simple-test")
    async def simple_test():
        """Simple test endpoint."""
        return {"message": "hello"}
    
    
    @app.get("/api/v1/admin/dashboard/stats")
    async def get_dashboard_stats():
        """Get dashboard statistics."""
        try:
            from database import DatabaseManager
            
            db = DatabaseManager()
            stats = db.get_dashboard_stats()
            
            return {
                "success": True,
                "data": stats
            }
        except Exception as e:
            print(f"Error in get_dashboard_stats: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    @app.get("/api/v1/admin/dashboard/activities")
    async def get_recent_activities(limit: int = 10):
        """Get recent activities."""
        try:
            from database import DatabaseManager
            
            db = DatabaseManager()
            activities = db.get_recent_activities(limit=limit)
            
            return {
                "success": True,
                "data": activities
            }
        except Exception as e:
            print(f"Error in get_recent_activities: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": []
            }
    
    @app.get("/api/v1/admin/dashboard/alerts")
    async def get_dashboard_alerts():
        """Get dashboard alerts."""
        try:
            from database import DatabaseManager
            
            db = DatabaseManager()
            alerts = db.get_dashboard_alerts()
            
            return {
                "success": True,
                "data": alerts
            }
        except Exception as e:
            print(f"Error in get_dashboard_alerts: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": []
            }
    
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