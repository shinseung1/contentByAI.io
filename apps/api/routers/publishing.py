"""Publishing router."""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from packages.publisher.manager import PublisherManager
from packages.publisher.models import PublishRequest, PublishResponse, PublishMode


router = APIRouter(prefix="/publishing", tags=["publishing"])


class PublishJobRequest(BaseModel):
    """Publish job request model."""
    bundle_id: str = Field(..., min_length=1)
    platform: str = Field(..., pattern="^(wordpress|blogger)$")
    mode: PublishMode = Field(PublishMode.DRAFT)
    scheduled_datetime: Optional[datetime] = None


class PublishJobResponse(BaseModel):
    """Publish job response model."""
    job_id: str
    status: str
    message: str


@router.post("/publish", response_model=PublishJobResponse)
async def publish_content(
    request: PublishJobRequest,
    background_tasks: BackgroundTasks
) -> PublishJobResponse:
    """Publish content to platform."""
    manager = PublisherManager()
    
    publish_request = PublishRequest(
        bundle_id=request.bundle_id,
        platform=request.platform,
        mode=request.mode,
        scheduled_datetime=request.scheduled_datetime
    )
    
    job_id = manager.create_job_id()
    background_tasks.add_task(
        manager.publish_async,
        job_id,
        publish_request
    )
    
    return PublishJobResponse(
        job_id=job_id,
        status="started",
        message=f"Publishing to {request.platform} started"
    )


@router.get("/jobs/{job_id}", response_model=PublishResponse)
async def get_publish_job(job_id: str) -> PublishResponse:
    """Get publish job status and result."""
    manager = PublisherManager()
    
    try:
        response = manager.get_job_result(job_id)
        return response
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Job not found")


@router.get("/jobs", response_model=List[str])
async def list_publish_jobs() -> List[str]:
    """List all publish jobs."""
    manager = PublisherManager()
    return manager.list_jobs()


@router.post("/test-connection/{platform}")
async def test_platform_connection(platform: str) -> dict:
    """Test connection to publishing platform."""
    if platform not in ["wordpress", "blogger"]:
        raise HTTPException(status_code=400, detail="Invalid platform")
    
    manager = PublisherManager()
    try:
        result = await manager.test_connection(platform)
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}