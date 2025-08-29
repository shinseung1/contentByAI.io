"""Content generation router."""

from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from packages.gen.content_generator import ContentGenerator
from packages.gen.models import GenerationRequest, GenerationResponse


router = APIRouter(prefix="/generation", tags=["generation"])


class GenerateContentRequest(BaseModel):
    """Content generation request model."""
    topic: str = Field(..., min_length=1, max_length=500)
    tone: Optional[str] = Field("professional", max_length=50)
    word_count: Optional[int] = Field(800, ge=300, le=3000)
    include_images: bool = Field(True)
    target_language: str = Field("ko", max_length=10)


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
    generator = ContentGenerator()
    
    generation_request = GenerationRequest(
        topic=request.topic,
        tone=request.tone,
        word_count=request.word_count,
        include_images=request.include_images,
        target_language=request.target_language
    )
    
    job_id = generator.create_job_id()
    background_tasks.add_task(
        generator.generate_content_async,
        job_id,
        generation_request
    )
    
    return GenerationJobResponse(
        job_id=job_id,
        status="started",
        message="Content generation started"
    )


@router.get("/jobs/{job_id}", response_model=GenerationResponse)
async def get_generation_job(job_id: str) -> GenerationResponse:
    """Get generation job status and result."""
    generator = ContentGenerator()
    
    try:
        response = generator.get_job_result(job_id)
        return response
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Job not found")


@router.get("/jobs", response_model=List[str])
async def list_generation_jobs() -> List[str]:
    """List all generation jobs."""
    generator = ContentGenerator()
    return generator.list_jobs()