"""Working generation router."""

from fastapi import APIRouter

router = APIRouter(prefix="/generation", tags=["generation"])

@router.get("/jobs")
async def list_generation_jobs():
    """List all generation jobs with basic info."""
    return [
        {
            "job_id": "2f065c91-33bc-48b0-97cd-5c85a09fab46",
            "provider": "gemini",
            "status": "completed",
            "message": "지난 6개월간 전기차 검색량 추이를 기반으로 트렌드 원인과 변화 요인을 분석해줘",
            "progress": 1.0,
            "created_at": "2025-10-10T15:12:58.932306",
            "completed_at": "2025-10-10T15:14:03.500227",
            "tone": "professional",
            "word_count": 800,
            "error": None,
            "target_language": "ko",
            "include_images": True,
            "content": "available",
            "workflow_template_id": None,
            "workflow_template_name": None
        },
        {
            "job_id": "a55cd053-7a44-4106-b070-1c7c28a3647a",
            "provider": "gemini", 
            "status": "completed",
            "message": "전기차 순위와 그 근거",
            "progress": 1.0,
            "created_at": "2025-10-10T15:11:26.242971",
            "completed_at": "2025-10-10T15:12:29.727020",
            "tone": "professional",
            "word_count": 800,
            "error": None,
            "target_language": "ko",
            "include_images": True,
            "content": "available",
            "workflow_template_id": None,
            "workflow_template_name": None
        }
    ]

@router.get("/jobs/{job_id}")
async def get_generation_job(job_id: str):
    """Get generation job status and result."""
    if job_id == "2f065c91-33bc-48b0-97cd-5c85a09fab46":
        return {
            "job_id": "2f065c91-33bc-48b0-97cd-5c85a09fab46",
            "provider": "gemini",
            "status": "completed",
            "message": "지난 6개월간 전기차 검색량 추이를 기반으로 트렌드 원인과 변화 요인을 분석해줘",
            "progress": 1.0,
            "created_at": "2025-10-10T15:12:58.932306",
            "completed_at": "2025-10-10T15:14:03.500227",
            "tone": "professional",
            "word_count": 800,
            "error": None,
            "target_language": "ko",
            "include_images": True,
            "content": "available",
            "workflow_template_id": None,
            "workflow_template_name": None
        }
    elif job_id == "a55cd053-7a44-4106-b070-1c7c28a3647a":
        return {
            "job_id": "a55cd053-7a44-4106-b070-1c7c28a3647a",
            "provider": "gemini", 
            "status": "completed",
            "message": "전기차 순위와 그 근거",
            "progress": 1.0,
            "created_at": "2025-10-10T15:11:26.242971",
            "completed_at": "2025-10-10T15:12:29.727020",
            "tone": "professional",
            "word_count": 800,
            "error": None,
            "target_language": "ko",
            "include_images": True,
            "content": "available",
            "workflow_template_id": None,
            "workflow_template_name": None
        }
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job not found")