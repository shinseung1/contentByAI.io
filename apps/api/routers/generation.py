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
    provider: Optional[str] = Field(None, max_length=50)
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
        provider=request.provider,
        tone=request.tone,
        word_count=request.word_count,
        include_images=request.include_images,
        target_language=request.target_language
    )
    
    job_id = generator.create_job_id()
    
    # TEMPORARY: Generate content synchronously for debugging
    try:
        print(f"DEBUG SYNC: Starting generation for {job_id}")
        await generator.generate_content_async(job_id, generation_request)
        print(f"DEBUG SYNC: Generation completed for {job_id}")
        return GenerationJobResponse(
            job_id=job_id,
            status="completed",
            message="Content generation completed"
        )
    except Exception as e:
        print(f"DEBUG SYNC ERROR: {e}")
        import traceback
        print(f"DEBUG SYNC TRACEBACK: {traceback.format_exc()}")
        return GenerationJobResponse(
            job_id=job_id,
            status="failed", 
            message=str(e)
        )


@router.get("/jobs/{job_id}")  # Remove response_model temporarily
async def get_generation_job(job_id: str):
    """Get generation job status and result."""
    generator = ContentGenerator()
    
    try:
        print(f"DEBUG API: Getting job result for {job_id}")
        response = generator.get_job_result(job_id)
        print(f"DEBUG API: Got response, status: {response.status}")
        
        # Debug: check response content for ImageInfo objects
        print(f"DEBUG API: Response has content: {response.content is not None}")
        if response.content:
            print(f"DEBUG API: Content has images: {response.content.images is not None}")
            if response.content.images:
                print(f"DEBUG API: Response has {len(response.content.images)} images")
                for i, img in enumerate(response.content.images):
                    print(f"DEBUG API: Image {i} type: {type(img)}")
                    print(f"DEBUG API: Image {i} content: {img}")
            else:
                print(f"DEBUG API: No images in response.content.images")
        
        # Convert to dict manually to bypass Pydantic serialization
        response_dict = {
            "job_id": response.job_id,
            "status": response.status.value if hasattr(response.status, 'value') else str(response.status),
            "message": response.message,
            "progress": response.progress,
            "content": None if not response.content else {
                "title": response.content.title,
                "content": response.content.content,
                "markdown_content": response.content.markdown_content,
                "summary": response.content.summary,
                "tags": response.content.tags,
                "images": response.content.images  # This might be the problematic line
            },
            "error": response.error,
            "created_at": response.created_at,
            "completed_at": response.completed_at
        }
        
        print(f"DEBUG API: Returning response dict")
        return response_dict
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Job not found")
    except Exception as e:
        print(f"DEBUG API ERROR: {e}")
        import traceback
        print(f"DEBUG API TRACEBACK: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs", response_model=List[GenerationResponse])
async def list_generation_jobs() -> List[GenerationResponse]:
    """List all generation jobs with details."""
    generator = ContentGenerator()
    job_ids = generator.list_jobs()
    
    jobs = []
    for job_id in job_ids:
        try:
            job_data = generator.get_job_result(job_id)
            jobs.append(job_data)
        except FileNotFoundError:
            continue
    
    # Sort by created_at descending (newest first)
    jobs.sort(key=lambda x: x.created_at or "", reverse=True)
    return jobs