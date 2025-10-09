"""Workflow template management router."""

from typing import List, Optional
from datetime import datetime
import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from database import DatabaseManager, WorkflowTemplate

router = APIRouter(prefix="/workflows", tags=["workflows"])


class WorkflowStepModel(BaseModel):
    """Workflow step model."""
    name: str
    prompt_template: str
    approver_role: str
    auto_transition: bool = Field(default=True)


class WorkflowTemplateRequest(BaseModel):
    """Workflow template request model."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    steps: List[WorkflowStepModel]
    version: str = Field("v1.0", max_length=20)
    status: str = Field("active", pattern="^(active|inactive)$")


class WorkflowTemplateResponse(BaseModel):
    """Workflow template response model."""
    id: int
    name: str
    description: Optional[str] = None
    steps: List[WorkflowStepModel]
    version: str
    status: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[int] = None


def _format_workflow_template_response(db_template: WorkflowTemplate) -> WorkflowTemplateResponse:
    """Format database workflow template to response model."""
    try:
        steps_data = json.loads(db_template.steps) if db_template.steps else []
    except json.JSONDecodeError:
        steps_data = []
    
    steps = [WorkflowStepModel(**step) for step in steps_data]
    
    return WorkflowTemplateResponse(
        id=db_template.id,
        name=db_template.name,
        description=db_template.description,
        steps=steps,
        version=db_template.version,
        status=db_template.status,
        created_at=db_template.created_at,
        updated_at=db_template.updated_at,
        created_by=db_template.created_by
    )


@router.get("/", response_model=List[WorkflowTemplateResponse])
async def list_workflow_templates():
    """List all workflow templates."""
    try:
        db = DatabaseManager()
        db_templates = db.get_all_workflow_templates()
        
        templates = [_format_workflow_template_response(template) for template in db_templates]
        return templates
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list workflow templates: {str(e)}")


@router.get("/active", response_model=List[WorkflowTemplateResponse])
async def list_active_workflow_templates():
    """List active workflow templates only."""
    try:
        db = DatabaseManager()
        db_templates = db.get_active_workflow_templates()
        
        templates = [_format_workflow_template_response(template) for template in db_templates]
        return templates
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list active workflow templates: {str(e)}")


@router.get("/{template_id}", response_model=WorkflowTemplateResponse)
async def get_workflow_template(template_id: int):
    """Get workflow template by ID."""
    try:
        db = DatabaseManager()
        db_template = db.get_workflow_template_by_id(template_id)
        
        if not db_template:
            raise HTTPException(status_code=404, detail="Workflow template not found")
        
        return _format_workflow_template_response(db_template)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflow template: {str(e)}")


@router.post("/", response_model=WorkflowTemplateResponse)
async def create_workflow_template(template_data: WorkflowTemplateRequest):
    """Create a new workflow template."""
    try:
        db = DatabaseManager()
        
        # Convert steps to JSON string
        steps_json = json.dumps([step.dict() for step in template_data.steps])
        
        # Create workflow template
        new_template = WorkflowTemplate(
            name=template_data.name,
            description=template_data.description,
            steps=steps_json,
            version=template_data.version,
            status=template_data.status,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            created_by=1  # Default to admin user for now
        )
        
        template_id = db.create_workflow_template(new_template)
        created_template = db.get_workflow_template_by_id(template_id)
        
        return _format_workflow_template_response(created_template)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create workflow template: {str(e)}")


@router.put("/{template_id}", response_model=WorkflowTemplateResponse)
async def update_workflow_template(template_id: int, template_data: WorkflowTemplateRequest):
    """Update workflow template."""
    try:
        db = DatabaseManager()
        
        # Get existing template
        existing_template = db.get_workflow_template_by_id(template_id)
        if not existing_template:
            raise HTTPException(status_code=404, detail="Workflow template not found")
        
        # Convert steps to JSON string
        steps_json = json.dumps([step.dict() for step in template_data.steps])
        
        # Update template
        existing_template.name = template_data.name
        existing_template.description = template_data.description
        existing_template.steps = steps_json
        existing_template.version = template_data.version
        existing_template.status = template_data.status
        existing_template.updated_at = datetime.now().isoformat()
        
        db.update_workflow_template(existing_template)
        updated_template = db.get_workflow_template_by_id(template_id)
        
        return _format_workflow_template_response(updated_template)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update workflow template: {str(e)}")


@router.delete("/{template_id}")
async def delete_workflow_template(template_id: int):
    """Delete workflow template."""
    try:
        db = DatabaseManager()
        
        # Get existing template
        existing_template = db.get_workflow_template_by_id(template_id)
        if not existing_template:
            raise HTTPException(status_code=404, detail="Workflow template not found")
        
        db.delete_workflow_template(template_id)
        return {"message": "Workflow template deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete workflow template: {str(e)}")


@router.post("/{template_id}/activate")
async def activate_workflow_template(template_id: int):
    """Activate workflow template."""
    try:
        db = DatabaseManager()
        
        # Get existing template
        existing_template = db.get_workflow_template_by_id(template_id)
        if not existing_template:
            raise HTTPException(status_code=404, detail="Workflow template not found")
        
        existing_template.status = "active"
        existing_template.updated_at = datetime.now().isoformat()
        
        db.update_workflow_template(existing_template)
        
        return {"message": "Workflow template activated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to activate workflow template: {str(e)}")


@router.post("/{template_id}/deactivate")
async def deactivate_workflow_template(template_id: int):
    """Deactivate workflow template."""
    try:
        db = DatabaseManager()
        
        # Get existing template
        existing_template = db.get_workflow_template_by_id(template_id)
        if not existing_template:
            raise HTTPException(status_code=404, detail="Workflow template not found")
        
        existing_template.status = "inactive"
        existing_template.updated_at = datetime.now().isoformat()
        
        db.update_workflow_template(existing_template)
        
        return {"message": "Workflow template deactivated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to deactivate workflow template: {str(e)}")