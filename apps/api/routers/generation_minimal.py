"""Minimal generation router."""

from fastapi import APIRouter

router = APIRouter(prefix="/generation", tags=["generation"])

@router.get("/jobs")
async def list_generation_jobs():
    """List all generation jobs with details."""
    return [
        {
            "job_id": "test-1",
            "status": "completed",
            "message": "Test job 1",
            "progress": 1.0,
            "content": None,
            "error": None,
            "created_at": "2024-01-01T00:00:00",
            "completed_at": "2024-01-01T00:01:00",
            "tone": "professional",
            "word_count": 800
        }
    ]