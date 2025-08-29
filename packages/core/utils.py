"""Core utility functions."""

import hashlib
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union


def generate_id() -> str:
    """Generate unique ID."""
    return str(uuid.uuid4())


def generate_short_id() -> str:
    """Generate short unique ID."""
    return str(uuid.uuid4())[:8]


def generate_hash(data: Union[str, Dict[str, Any]]) -> str:
    """Generate MD5 hash of data."""
    if isinstance(data, dict):
        data = json.dumps(data, sort_keys=True)
    return hashlib.md5(data.encode()).hexdigest()


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for filesystem."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '-')
    return filename[:255]  # Limit filename length


def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure directory exists."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_timestamp() -> str:
    """Get current timestamp string."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def get_iso_timestamp() -> str:
    """Get current ISO format timestamp."""
    return datetime.now().isoformat()


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def safe_json_loads(data: str, default: Any = None) -> Any:
    """Safely load JSON data."""
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(data: Any, default: str = "{}") -> str:
    """Safely dump JSON data."""
    try:
        return json.dumps(data, ensure_ascii=False, indent=2)
    except (TypeError, ValueError):
        return default


def chunk_list(lst: list, chunk_size: int) -> list:
    """Split list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"


def validate_url(url: str) -> bool:
    """Validate if string is a valid URL."""
    try:
        from urllib.parse import urlparse
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def extract_domain(url: str) -> Optional[str]:
    """Extract domain from URL."""
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc
    except Exception:
        return None