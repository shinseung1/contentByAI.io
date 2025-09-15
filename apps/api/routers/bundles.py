"""Bundle management router."""

from typing import List, Optional, Dict, Any
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from packages.packager.bundle import BundleManager
from packages.packager.models import PostBundle


router = APIRouter(prefix="/bundles", tags=["bundles"])


class BundleListResponse(BaseModel):
    """Bundle list response model."""
    bundles: List[str]
    total: int


class BundleDetailResponse(BaseModel):
    """Bundle detail response model."""
    bundle_id: str
    bundle: PostBundle


class CreateBundleRequest(BaseModel):
    """Create bundle request model."""
    title: str
    description: Optional[str] = None


class CreateBundleResponse(BaseModel):
    """Create bundle response model."""
    bundle_id: str
    message: str


class AddPostRequest(BaseModel):
    """Add post to bundle request model."""
    post_data: Dict[str, Any]


class AddPostResponse(BaseModel):
    """Add post to bundle response model."""
    message: str


@router.post("/", response_model=CreateBundleResponse)
async def create_bundle(request: CreateBundleRequest) -> CreateBundleResponse:
    """Create a new bundle."""
    bundle_manager = BundleManager()
    
    try:
        bundle_id = bundle_manager.create_bundle(
            title=request.title,
            description=request.description
        )
        return CreateBundleResponse(
            bundle_id=bundle_id,
            message=f"Bundle '{request.title}' created successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create bundle: {str(e)}")


@router.get("/", response_model=BundleListResponse)
async def list_bundles(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> BundleListResponse:
    """List available bundles."""
    bundle_manager = BundleManager()
    bundle_ids = bundle_manager.list_bundles()
    
    total = len(bundle_ids)
    bundles = bundle_ids[offset:offset + limit]
    
    return BundleListResponse(bundles=bundles, total=total)


@router.get("/{bundle_id}", response_model=BundleDetailResponse)
async def get_bundle(bundle_id: str) -> BundleDetailResponse:
    """Get bundle details."""
    bundle_manager = BundleManager()
    
    try:
        bundle = bundle_manager.load_bundle(bundle_id)
        return BundleDetailResponse(bundle_id=bundle_id, bundle=bundle)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Bundle not found")


@router.post("/{bundle_id}/posts", response_model=AddPostResponse)
async def add_post_to_bundle(bundle_id: str, request: AddPostRequest) -> AddPostResponse:
    """Add a post to a bundle."""
    bundle_manager = BundleManager()
    
    try:
        bundle_manager.add_post_to_bundle(bundle_id, request.post_data)
        return AddPostResponse(message=f"Post added to bundle {bundle_id} successfully")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Bundle not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add post to bundle: {str(e)}")


@router.delete("/{bundle_id}")
async def delete_bundle(bundle_id: str) -> dict:
    """Delete a bundle."""
    bundle_manager = BundleManager()
    
    try:
        bundle_manager.delete_bundle(bundle_id)
        return {"message": f"Bundle {bundle_id} deleted successfully"}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Bundle not found")