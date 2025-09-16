"""Content generation router."""

from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

# from packages.gen.content_generator import ContentGenerator
# from packages.gen.models import GenerationRequest, GenerationResponse


router = APIRouter(prefix="/generation", tags=["generation"])


class GenerateContentRequest(BaseModel):
    """Content generation request model."""
    topic: str = Field(..., min_length=1, max_length=500)
    provider: Optional[str] = Field(None, max_length=50)
    tone: Optional[str] = Field("professional", max_length=50)
    word_count: Optional[int] = Field(800, ge=300, le=3000)
    include_images: bool = Field(True)
    target_language: str = Field("ko", max_length=10)
    num_options: Optional[int] = Field(1, ge=1, le=5, description="Number of content options to generate")
    balance_word_count: bool = Field(True, description="Whether to balance word count across multiple options")


class GenerationJobResponse(BaseModel):
    """Generation job response model."""
    job_id: str
    status: str
    message: str


@router.post("/generate", response_model=GenerationJobResponse)
async def generate_content(
    request: GenerateContentRequest,
    background_tasks: BackgroundTasks
) -> GenerationJobResponse:
    """Generate content from topic."""
    # Temporarily disabled
    return GenerationJobResponse(
        job_id="temp-disabled",
        status="disabled",
        message="Generation temporarily disabled"
    )


@router.get("/jobs/{job_id}")  # Remove response_model temporarily
async def get_generation_job(job_id: str):
    """Get generation job status and result."""
    # Temporarily disabled
    return {
        "job_id": job_id,
        "status": "disabled", 
        "message": "Job lookup temporarily disabled"
    }


@router.get("/jobs")  # Remove response_model temporarily  
async def list_generation_jobs():
    """List all generation jobs with details."""
    return {"message": "Simple test", "count": 0}