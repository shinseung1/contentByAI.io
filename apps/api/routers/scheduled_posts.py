"""예약 포스팅 API 라우터"""

from typing import List, Optional
from datetime import datetime, timezone
import json
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from database import DatabaseManager, ScheduledPost

router = APIRouter(prefix="/scheduled-posts", tags=["scheduled-posts"])

class CreateScheduledPostRequest(BaseModel):
    """예약 포스트 생성 요청 모델"""
    title: str = Field(..., min_length=1, max_length=200)
    topic: Optional[str] = Field(None, max_length=1000)
    topic_source: str = Field("user", pattern="^(user|trend)$")
    schedule_time: str = Field(..., description="ISO datetime string")
    provider: str = Field("gemini", max_length=50)
    workflow_template_id: Optional[int] = None
    repeat_config: Optional[dict] = None

class UpdateScheduledPostRequest(BaseModel):
    """예약 포스트 수정 요청 모델"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    topic: Optional[str] = Field(None, max_length=1000)
    topic_source: Optional[str] = Field(None, pattern="^(user|trend)$")
    schedule_time: Optional[str] = Field(None, description="ISO datetime string")
    status: Optional[str] = Field(None, pattern="^(pending|completed|failed|paused)$")
    provider: Optional[str] = Field(None, max_length=50)
    workflow_template_id: Optional[int] = None
    repeat_config: Optional[dict] = None

class ScheduledPostResponse(BaseModel):
    """예약 포스트 응답 모델"""
    id: int
    schedule_id: str
    title: str
    topic: Optional[str]
    topic_source: str
    schedule_time: str
    status: str
    provider: str
    workflow_template_id: Optional[int]
    repeat_config: Optional[dict]
    generated_job_id: Optional[str]
    error_message: Optional[str]
    created_at: str
    updated_at: str
    last_executed_at: Optional[str]

@router.post("/", response_model=dict)
async def create_scheduled_post(request: CreateScheduledPostRequest):
    """예약 포스트 생성"""
    try:
        db = DatabaseManager()
        
        # 입력 검증
        try:
            schedule_datetime = datetime.fromisoformat(request.schedule_time.replace('Z', '+00:00'))
            if schedule_datetime < datetime.now(timezone.utc):
                raise HTTPException(status_code=400, detail="예약 시간은 현재 시간보다 늦어야 합니다")
        except ValueError:
            raise HTTPException(status_code=400, detail="올바른 datetime 형식이 아닙니다")
        
        # topic_source가 'user'인 경우 topic 필수
        if request.topic_source == "user" and not request.topic:
            raise HTTPException(status_code=400, detail="사용자 지정 주제 모드에서는 topic이 필수입니다")
        
        scheduled_post = ScheduledPost(
            schedule_id=str(uuid4()),
            title=request.title,
            topic=request.topic,
            topic_source=request.topic_source,
            schedule_time=request.schedule_time,
            status="pending",
            provider=request.provider,
            workflow_template_id=request.workflow_template_id,
            repeat_config=json.dumps(request.repeat_config) if request.repeat_config else None,
            created_at=datetime.now().isoformat()
        )
        
        schedule_id = db.create_scheduled_post(scheduled_post)
        
        return {
            "schedule_id": scheduled_post.schedule_id,
            "message": "예약 포스트가 생성되었습니다",
            "id": schedule_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"예약 포스트 생성 실패: {str(e)}")

@router.get("/", response_model=List[ScheduledPostResponse])
async def list_scheduled_posts(status: Optional[str] = None, limit: int = 50):
    """예약 포스트 목록 조회"""
    try:
        db = DatabaseManager()
        scheduled_posts = db.list_scheduled_posts(status=status, limit=limit)
        
        results = []
        for post in scheduled_posts:
            results.append(ScheduledPostResponse(
                id=post.id,
                schedule_id=post.schedule_id,
                title=post.title,
                topic=post.topic,
                topic_source=post.topic_source,
                schedule_time=post.schedule_time,
                status=post.status,
                provider=post.provider,
                workflow_template_id=post.workflow_template_id,
                repeat_config=json.loads(post.repeat_config) if post.repeat_config else None,
                generated_job_id=post.generated_job_id,
                error_message=post.error_message,
                created_at=post.created_at,
                updated_at=post.updated_at,
                last_executed_at=post.last_executed_at
            ))
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"목록 조회 실패: {str(e)}")

@router.get("/{schedule_id}", response_model=ScheduledPostResponse)
async def get_scheduled_post(schedule_id: str):
    """특정 예약 포스트 조회"""
    try:
        db = DatabaseManager()
        post = db.get_scheduled_post(schedule_id)
        
        if not post:
            raise HTTPException(status_code=404, detail="예약 포스트를 찾을 수 없습니다")
        
        return ScheduledPostResponse(
            id=post.id,
            schedule_id=post.schedule_id,
            title=post.title,
            topic=post.topic,
            topic_source=post.topic_source,
            schedule_time=post.schedule_time,
            status=post.status,
            provider=post.provider,
            workflow_template_id=post.workflow_template_id,
            repeat_config=json.loads(post.repeat_config) if post.repeat_config else None,
            generated_job_id=post.generated_job_id,
            error_message=post.error_message,
            created_at=post.created_at,
            updated_at=post.updated_at,
            last_executed_at=post.last_executed_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")

@router.put("/{schedule_id}", response_model=dict)
async def update_scheduled_post(schedule_id: str, request: UpdateScheduledPostRequest):
    """예약 포스트 수정"""
    try:
        db = DatabaseManager()
        existing_post = db.get_scheduled_post(schedule_id)
        
        if not existing_post:
            raise HTTPException(status_code=404, detail="예약 포스트를 찾을 수 없습니다")
        
        # 수정할 필드만 업데이트
        if request.title is not None:
            existing_post.title = request.title
        if request.topic is not None:
            existing_post.topic = request.topic
        if request.topic_source is not None:
            existing_post.topic_source = request.topic_source
        if request.schedule_time is not None:
            # 시간 검증
            try:
                schedule_datetime = datetime.fromisoformat(request.schedule_time.replace('Z', '+00:00'))
                if schedule_datetime < datetime.now(timezone.utc) and existing_post.status == "pending":
                    raise HTTPException(status_code=400, detail="예약 시간은 현재 시간보다 늦어야 합니다")
                existing_post.schedule_time = request.schedule_time
            except ValueError:
                raise HTTPException(status_code=400, detail="올바른 datetime 형식이 아닙니다")
        if request.status is not None:
            existing_post.status = request.status
        if request.provider is not None:
            existing_post.provider = request.provider
        if request.workflow_template_id is not None:
            existing_post.workflow_template_id = request.workflow_template_id
        if request.repeat_config is not None:
            existing_post.repeat_config = json.dumps(request.repeat_config)
        
        # topic_source가 'user'인 경우 topic 검증
        if existing_post.topic_source == "user" and not existing_post.topic:
            raise HTTPException(status_code=400, detail="사용자 지정 주제 모드에서는 topic이 필수입니다")
        
        success = db.update_scheduled_post(existing_post)
        
        if success:
            return {"message": "예약 포스트가 수정되었습니다"}
        else:
            raise HTTPException(status_code=500, detail="수정에 실패했습니다")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"수정 실패: {str(e)}")

@router.delete("/{schedule_id}", response_model=dict)
async def delete_scheduled_post(schedule_id: str):
    """예약 포스트 삭제"""
    try:
        db = DatabaseManager()
        success = db.delete_scheduled_post(schedule_id)
        
        if success:
            return {"message": "예약 포스트가 삭제되었습니다"}
        else:
            raise HTTPException(status_code=404, detail="예약 포스트를 찾을 수 없습니다")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"삭제 실패: {str(e)}")

@router.post("/{schedule_id}/toggle-status", response_model=dict)
async def toggle_scheduled_post_status(schedule_id: str):
    """예약 포스트 상태 토글 (pending <-> paused)"""
    try:
        db = DatabaseManager()
        post = db.get_scheduled_post(schedule_id)
        
        if not post:
            raise HTTPException(status_code=404, detail="예약 포스트를 찾을 수 없습니다")
        
        # 상태 토글
        if post.status == "pending":
            post.status = "paused"
        elif post.status == "paused":
            post.status = "pending"
        else:
            raise HTTPException(status_code=400, detail="완료되거나 실패한 작업은 토글할 수 없습니다")
        
        success = db.update_scheduled_post(post)
        
        if success:
            return {
                "message": f"상태가 {post.status}로 변경되었습니다",
                "status": post.status
            }
        else:
            raise HTTPException(status_code=500, detail="상태 변경에 실패했습니다")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상태 변경 실패: {str(e)}")

@router.get("/pending/due", response_model=List[ScheduledPostResponse])
async def get_pending_scheduled_posts():
    """실행 대기 중인 예약 포스트 조회 (스케줄러용)"""
    try:
        db = DatabaseManager()
        current_time = datetime.now().isoformat()
        pending_posts = db.get_pending_scheduled_posts(current_time)
        
        results = []
        for post in pending_posts:
            results.append(ScheduledPostResponse(
                id=post.id,
                schedule_id=post.schedule_id,
                title=post.title,
                topic=post.topic,
                topic_source=post.topic_source,
                schedule_time=post.schedule_time,
                status=post.status,
                provider=post.provider,
                workflow_template_id=post.workflow_template_id,
                repeat_config=json.loads(post.repeat_config) if post.repeat_config else None,
                generated_job_id=post.generated_job_id,
                error_message=post.error_message,
                created_at=post.created_at,
                updated_at=post.updated_at,
                last_executed_at=post.last_executed_at
            ))
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")