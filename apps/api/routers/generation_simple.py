"""Content generation router - simplified version."""

from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field


router = APIRouter(prefix="/generation", tags=["generation"])


class GenerateContentRequest(BaseModel):
    """Content generation request model."""
    topic: str = Field(..., min_length=1, max_length=500)
    provider: Optional[str] = Field(None, max_length=50)
    tone: Optional[str] = Field("professional", max_length=50)
    word_count: Optional[int] = Field(800, ge=300, le=3000)
    include_images: bool = Field(True)
    target_language: str = Field("ko", max_length=10)
    num_options: Optional[int] = Field(1, ge=1, le=5)
    balance_word_count: bool = Field(True)


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
    try:
        from database import DatabaseManager
        import uuid
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Fix Korean topic encoding if needed
        topic = request.topic
        if request.target_language == "ko" and topic:
            try:
                # Try to fix common encoding issues with Korean text
                if isinstance(topic, str):
                    # Check if Korean characters are corrupted
                    korean_chars = [c for c in topic if '\uAC00' <= c <= '\uD7AF']
                    if len(korean_chars) == 0 and len(topic) > 0:
                        print(f"DEBUG: No Korean chars found in topic, attempting fix: {repr(topic)}")
                        # Try to recover Korean text from bytes
                        topic_bytes = topic.encode('latin-1', errors='ignore')
                        try:
                            topic = topic_bytes.decode('utf-8')
                            print(f"DEBUG: Fixed Korean topic: {repr(topic)}")
                        except UnicodeDecodeError:
                            print(f"DEBUG: Could not fix Korean topic encoding")
            except Exception as e:
                print(f"DEBUG: Error fixing Korean topic: {e}")
        
        # Save job to database
        db = DatabaseManager()
        
        # Import GenerationJob class
        from database import GenerationJob
        from datetime import datetime
        
        # Create the generation job record
        job = GenerationJob(
            job_id=job_id,
            topic=topic,  # Use the potentially fixed topic
            provider=request.provider or "gemini",  # Default to gemini
            tone=request.tone or "professional",
            word_count=request.word_count or 800,
            include_images=request.include_images,
            target_language=request.target_language or "ko",
            status="pending",
            progress=0,
            created_at=datetime.now().isoformat()
        )
        
        db.save_generation_job(job)
        
        # Add background task for actual content generation
        background_tasks.add_task(
            process_generation_job,
            job_id,
            topic,  # Use the potentially fixed topic
            request.provider or "gemini",
            request.tone or "professional",
            request.word_count or 800,
            request.include_images,
            request.target_language or "ko"
        )
        
        return GenerationJobResponse(
            job_id=job_id,
            status="in_progress",
            message="Content generation started"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start generation: {str(e)}")


async def process_generation_job(
    job_id: str,
    topic: str,
    provider: str,
    tone: str,
    word_count: int,
    include_images: bool,
    target_language: str
):
    """Background task to process content generation."""
    try:
        from packages.gen.content_generator import ContentGenerator
        from packages.gen.models import GenerationRequest
        from database import DatabaseManager
        
        # Create content generator
        generator = ContentGenerator()
        
        # Create GenerationRequest object
        request = GenerationRequest(
            topic=topic,
            provider=provider,
            tone=tone,
            word_count=word_count,
            include_images=include_images,
            target_language=target_language
        )
        
        # Generate content using the correct async method
        await generator.generate_content_async(job_id, request)
        
    except Exception as e:
        # Update job with error
        try:
            db = DatabaseManager()
            db.update_generation_job_status(
                job_id=job_id,
                status="failed",
                progress=100,
                error_message=str(e)
            )
        except Exception as db_error:
            print(f"Failed to update job status: {db_error}")
            print(f"Original error: {e}")


@router.get("/jobs/{job_id}")
async def get_generation_job(job_id: str):
    """Get generation job status and result."""
    print(f"=== INDIVIDUAL JOB API HIT FOR {job_id} ===")
    try:
        from database import DatabaseManager
        
        db = DatabaseManager()
        job = db.get_generation_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Parse content if it exists
        content = None
        if job.content:
            try:
                import json
                content = json.loads(job.content) if isinstance(job.content, str) else job.content
            except:
                content = {"title": "Generated Content", "content": job.content}
        
        return {
            "job_id": job.job_id,
            "status": job.status,
            "message": f"Job {job.status}",
            "progress": float(job.progress / 100.0) if job.progress else 0.0,
            "content": content,
            "error": job.error_message,
            "created_at": job.created_at,
            "completed_at": job.updated_at if job.status in ['completed', 'failed'] else None,
            "tone": job.tone,
            "word_count": job.word_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/jobs")
async def list_generation_jobs():
    """List all generation jobs with details."""
    try:
        from database import DatabaseManager
        
        db = DatabaseManager()
        db_jobs = db.get_generation_jobs(limit=10)
        
        jobs = []
        for db_job in db_jobs:
            # Use topic as is (encoding is now handled in database layer)
            topic = db_job.topic if db_job.topic else "Unknown topic"
            if isinstance(topic, str) and len(topic) > 100:
                topic = topic[:100] + "..."
            
            # Parse content if it exists
            content = None
            if db_job.content:
                try:
                    import json
                    import re
                    
                    # First level JSON parsing
                    parsed_content = json.loads(db_job.content) if isinstance(db_job.content, str) else db_job.content
                    
                    # Check if html_content contains nested JSON
                    if isinstance(parsed_content, dict) and 'html_content' in parsed_content:
                        html_content = parsed_content['html_content']
                        
                        # Check if html_content contains nested JSON (legacy data format)
                        if isinstance(html_content, str) and ('```json' in html_content or (html_content.strip().startswith('{') and 'html_content' in html_content)):
                            try:
                                # Extract JSON content from html_content field
                                if '```json' in html_content:
                                    # Remove markdown markers
                                    clean_content = html_content.replace('```json', '').replace('```', '').strip()
                                else:
                                    clean_content = html_content.strip()
                                
                                # Parse the nested JSON
                                nested_content = json.loads(clean_content)
                                if isinstance(nested_content, dict) and 'html_content' in nested_content:
                                    # Use the nested JSON as the actual content
                                    content = nested_content
                                else:
                                    content = parsed_content
                            except (json.JSONDecodeError, Exception) as e:
                                print(f"Legacy format parse error for job {db_job.job_id}: {e}")
                                # If nested parsing fails, use the outer content but clean the html_content
                                if '```json' in html_content:
                                    # Extract just the actual HTML part if possible
                                    html_start = html_content.find('<')
                                    if html_start > 0:
                                        parsed_content['html_content'] = html_content[html_start:]
                                content = parsed_content
                        else:
                            content = parsed_content
                    else:
                        content = parsed_content
                        
                except Exception as e:
                    # If all parsing fails, treat as plain text
                    print(f"JSON parse error for job {db_job.job_id}: {e}")
                    content = {"title": "Generated Content", "content": str(db_job.content)}
            
            job_dict = {
                "job_id": db_job.job_id,
                "status": db_job.status,
                "message": topic,
                "progress": (db_job.progress / 100.0) if db_job.progress else 0.0,
                "content": content,
                "error": db_job.error_message,
                "created_at": db_job.created_at,
                "completed_at": db_job.updated_at if db_job.status in ['completed', 'failed'] else None,
                "tone": db_job.tone or "professional",
                "word_count": db_job.word_count or 800
            }
            jobs.append(job_dict)
        
        return jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")