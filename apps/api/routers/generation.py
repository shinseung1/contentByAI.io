"""Content generation router."""

from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from packages.gen.content_generator import ContentGenerator
print(f"DEBUG IMPORT: ContentGenerator imported from {ContentGenerator.__module__}")
from packages.gen.models import GenerationRequest, GenerationResponse


router = APIRouter(prefix="/generation", tags=["generation"])
print("DEBUG ROUTER: Generation router created")


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
    workflow_template_id: Optional[int] = Field(None, description="ID of workflow template to use")


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
        target_language=request.target_language,
        num_options=request.num_options,
        balance_word_count=request.balance_word_count,
        workflow_template_id=request.workflow_template_id
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


@router.get("/jobs/{job_id}")
async def get_generation_job(job_id: str):
    """Get generation job status and result."""
    try:
        # Direct database access to bypass ContentGenerator completely
        from database import DatabaseManager
        
        db = DatabaseManager()
        db_job = db.get_generation_job(job_id)
        if not db_job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Return complete job info directly from database
        return {
            "job_id": db_job.job_id,
            "provider": db_job.provider,
            "status": db_job.status,
            "message": db_job.topic,
            "progress": (db_job.progress or 0) / 100.0,
            "created_at": str(db_job.created_at) if db_job.created_at else None,
            "completed_at": str(db_job.updated_at) if db_job.status in ['completed', 'failed'] and db_job.updated_at else None,
            "tone": db_job.tone,
            "word_count": db_job.word_count,
            "content": db_job.content if db_job.status == 'completed' else None,
            "error": db_job.error_message,
            "target_language": db_job.target_language,
            "include_images": db_job.include_images
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-db")
async def test_database():
    """Test database connection."""
    try:
        from database import DatabaseManager
        db = DatabaseManager()
        jobs = db.get_generation_jobs()
        return {"success": True, "job_count": len(jobs)}
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}

@router.get("/jobs")
async def list_generation_jobs():
    """List all generation jobs with basic info."""
    try:
        # Direct database access to avoid ContentGenerator issues
        from database import DatabaseManager
        
        db = DatabaseManager()
        db_jobs = db.get_generation_jobs()
        
        jobs = []
        for db_job in db_jobs:
            jobs.append({
                "job_id": db_job.job_id,
                "provider": db_job.provider,
                "status": db_job.status,
                "message": db_job.topic,
                "progress": (db_job.progress or 0) / 100.0,
                "created_at": str(db_job.created_at) if db_job.created_at else None,
                "completed_at": str(db_job.updated_at) if db_job.status in ['completed', 'failed'] and db_job.updated_at else None,
                "tone": db_job.tone,
                "word_count": db_job.word_count,
                "content": db_job.content if db_job.status == 'completed' else None,
                "error": db_job.error_message,
                "target_language": db_job.target_language,
                "include_images": db_job.include_images
            })
        
        # Sort by created_at descending (newest first)
        jobs.sort(key=lambda x: x.get('created_at', '') or '', reverse=True)
        return jobs
    except Exception as e:
        return {"error": f"Database error: {str(e)}", "jobs": []}


@router.get("/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics for admin panel."""
    try:
        from database import DatabaseManager
        from datetime import datetime, timedelta
        
        db = DatabaseManager()
        db_jobs = db.get_generation_jobs()
        
        # Calculate today's date
        today = datetime.now().date()
        
        # Initialize stats
        today_count = 0
        failed_count = 0
        total_cost = 0.0
        pending_count = 0
        
        # Process jobs
        for job in db_jobs:
            # Count today's jobs
            if job.created_at and job.created_at.date() == today:
                today_count += 1
            
            # Count failed/retry jobs
            if job.status in ['failed', 'error']:
                failed_count += 1
            
            # Count pending jobs
            if job.status in ['pending', 'running']:
                pending_count += 1
            
            # Estimate cost (simplified calculation)
            if job.word_count and job.status == 'completed':
                # Rough estimate: $0.001 per 100 words
                total_cost += (job.word_count / 100) * 0.001
        
        # Get recent activities (last 10 jobs)
        recent_jobs = sorted(db_jobs, key=lambda x: x.created_at or datetime.min, reverse=True)[:10]
        recent_activities = []
        
        for job in recent_jobs:
            activity = {
                "id": job.job_id,
                "action": "콘텐츠 생성",
                "user": "admin",  # Default user for now
                "model": job.provider or "Unknown",
                "status": "success" if job.status == "completed" else ("error" if job.status == "failed" else "warning"),
                "timestamp": _format_relative_time(job.created_at) if job.created_at else "알 수 없음"
            }
            if job.status == "completed":
                activity["action"] += " 완료"
            elif job.status == "failed":
                activity["action"] += " 실패"
            else:
                activity["action"] += f" ({job.status})"
            
            recent_activities.append(activity)
        
        # Generate alerts based on actual data
        alerts = []
        
        # Alert for high failure rate
        if len(db_jobs) > 10:  # Only if we have enough data
            failure_rate = failed_count / len(db_jobs)
            if failure_rate > 0.1:  # More than 10% failure rate
                alerts.append({
                    "type": "error",
                    "message": f"생성 실패율이 {failure_rate*100:.1f}%로 높습니다 ({failed_count}건 실패)",
                    "action": "설정 확인"
                })
        
        # Alert for high pending count
        if pending_count > 5:
            alerts.append({
                "type": "warning", 
                "message": f"{pending_count}건의 작업이 대기 중입니다",
                "action": "상태 확인"
            })
        
        # Alert for high cost
        if total_cost > 10:
            alerts.append({
                "type": "info",
                "message": f"오늘 토큰 비용이 ${total_cost:.2f}에 도달했습니다",
                "action": "사용량 검토"
            })
        
        # Check for recent errors
        recent_errors = [job for job in db_jobs if job.status == 'failed' and job.updated_at and (datetime.now() - job.updated_at).seconds < 3600]
        if len(recent_errors) > 2:
            alerts.append({
                "type": "error",
                "message": "최근 1시간 동안 3건 이상의 작업이 실패했습니다",
                "action": "로그 확인"
            })
        
        return {
            "today_count": today_count,
            "failed_count": failed_count,
            "total_cost": round(total_cost, 2),
            "pending_count": pending_count,
            "recent_activities": recent_activities,
            "alerts": alerts
        }
    except Exception as e:
        import traceback
        return {
            "error": f"Dashboard stats error: {str(e)}",
            "traceback": traceback.format_exc(),
            "today_count": 0,
            "failed_count": 0,
            "total_cost": 0.0,
            "pending_count": 0,
            "recent_activities": [],
            "alerts": []
        }


def _format_relative_time(dt):
    """Format datetime as relative time string."""
    if not dt:
        return "알 수 없음"
    
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days}일 전"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours}시간 전"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes}분 전"
    else:
        return "방금 전"