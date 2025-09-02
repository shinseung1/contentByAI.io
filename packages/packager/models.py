"""Bundle models."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class PostBundle(BaseModel):
    """Post bundle model."""
    id: str = Field(..., description="Bundle identifier")
    title: str = Field(..., description="Bundle title")
    description: Optional[str] = Field(None, description="Bundle description")
    posts: List[Dict[str, Any]] = Field(default_factory=list, description="Post data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Bundle metadata")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")