"""Bundle management functionality."""

import json
import uuid
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from .models import PostBundle


class BundleManager:
    """Manager for post bundles."""
    
    def __init__(self, bundles_dir: str = "bundles"):
        self.bundles_dir = Path(bundles_dir)
        self.bundles_dir.mkdir(exist_ok=True)
    
    def create_bundle(self, title: str, description: str = None) -> str:
        """Create a new bundle."""
        bundle_id = str(uuid.uuid4())
        bundle = PostBundle(
            id=bundle_id,
            title=title,
            description=description,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.save_bundle(bundle)
        return bundle_id
    
    def save_bundle(self, bundle: PostBundle) -> None:
        """Save bundle to file."""
        bundle.updated_at = datetime.now()
        bundle_file = self.bundles_dir / f"{bundle.id}.json"
        
        with open(bundle_file, 'w', encoding='utf-8') as f:
            json.dump(bundle.model_dump(mode='json'), f, ensure_ascii=False, indent=2, default=str)
    
    def load_bundle(self, bundle_id: str) -> PostBundle:
        """Load bundle from file."""
        bundle_file = self.bundles_dir / f"{bundle_id}.json"
        
        if not bundle_file.exists():
            raise FileNotFoundError(f"Bundle {bundle_id} not found")
        
        with open(bundle_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return PostBundle(**data)
    
    def list_bundles(self) -> List[str]:
        """List all bundle IDs."""
        return [f.stem for f in self.bundles_dir.glob("*.json")]
    
    def delete_bundle(self, bundle_id: str) -> None:
        """Delete a bundle."""
        bundle_file = self.bundles_dir / f"{bundle_id}.json"
        
        if not bundle_file.exists():
            raise FileNotFoundError(f"Bundle {bundle_id} not found")
        
        bundle_file.unlink()
    
    def add_post_to_bundle(self, bundle_id: str, post_data: Dict[str, Any]) -> None:
        """Add post to bundle."""
        bundle = self.load_bundle(bundle_id)
        bundle.posts.append(post_data)
        self.save_bundle(bundle)