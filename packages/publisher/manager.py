"""Publisher manager."""

import json
import uuid
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from .models import PublishRequest, PublishResponse, PublishStatus


class PublisherManager:
    """Manager for publishing operations."""
    
    def __init__(self, jobs_dir: str = "runs/publish_jobs"):
        self.jobs_dir = Path(jobs_dir)
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
    
    def create_job_id(self) -> str:
        """Create a unique job ID."""
        return str(uuid.uuid4())
    
    def get_job_file_path(self, job_id: str) -> Path:
        """Get the file path for a job."""
        return self.jobs_dir / f"{job_id}.json"
    
    def save_job_status(self, job_id: str, response: PublishResponse) -> None:
        """Save job status to file."""
        job_file = self.get_job_file_path(job_id)
        with open(job_file, 'w', encoding='utf-8') as f:
            json.dump(response.model_dump(mode='json'), f, ensure_ascii=False, indent=2, default=str)
    
    def get_job_result(self, job_id: str) -> PublishResponse:
        """Get job result from file."""
        job_file = self.get_job_file_path(job_id)
        if not job_file.exists():
            raise FileNotFoundError(f"Job {job_id} not found")
        
        with open(job_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return PublishResponse(**data)
    
    def list_jobs(self) -> List[str]:
        """List all job IDs."""
        return [f.stem for f in self.jobs_dir.glob("*.json")]
    
    async def publish_async(self, job_id: str, request: PublishRequest) -> None:
        """Publish content asynchronously."""
        # Update status to in_progress
        response = PublishResponse(
            job_id=job_id,
            status=PublishStatus.IN_PROGRESS,
            message=f"Publishing to {request.platform}...",
            created_at=datetime.now()
        )
        self.save_job_status(job_id, response)
        
        try:
            # Simulate publishing logic
            await self._simulate_publish(request)
            
            # Update status to completed
            response.status = PublishStatus.COMPLETED
            response.message = f"Successfully published to {request.platform}"
            response.completed_at = datetime.now()
            
        except Exception as e:
            # Update status to failed
            response.status = PublishStatus.FAILED
            response.message = f"Publishing to {request.platform} failed"
            response.error = str(e)
            response.completed_at = datetime.now()
        
        self.save_job_status(job_id, response)
    
    async def _simulate_publish(self, request: PublishRequest) -> None:
        """Simulate publishing process."""
        import asyncio
        # Simulate some work
        await asyncio.sleep(2)
        # Here you would implement actual publishing logic
        pass
    
    async def test_connection(self, platform: str) -> Dict[str, Any]:
        """Test connection to publishing platform."""
        # Simulate connection test
        return {
            "platform": platform,
            "connected": True,
            "timestamp": datetime.now().isoformat()
        }