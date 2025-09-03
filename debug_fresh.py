#!/usr/bin/env python3
"""Debug with completely fresh database approach."""

import sys
import os
import json
import asyncio

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_fresh_approach():
    """Test with minimal data to isolate the issue."""
    from packages.gen.models import GeneratedContent, GenerationResponse, GenerationStatus
    
    print("Testing minimal GeneratedContent creation...")
    
    try:
        # Create a minimal GeneratedContent with NO images
        content = GeneratedContent(
            title="Test Title",
            content="<p>Test content</p>",
            markdown_content="# Test content",
            summary="Test summary", 
            tags=["test"],
            images=[]  # Explicitly empty
        )
        
        print(f"Content created: {content.title}")
        print(f"Images count: {len(content.images)}")
        
        # Test creating GenerationResponse
        response = GenerationResponse(
            job_id="debug-test-123",
            status=GenerationStatus.COMPLETED,
            message="Test message",
            progress=1.0,
            content=content,
            error=None,
            created_at="2023-01-01T00:00:00",
            completed_at="2023-01-01T00:01:00"
        )
        
        print("Response created successfully")
        
        # Test JSON serialization
        response_dict = response.model_dump()
        json_str = json.dumps(response_dict, ensure_ascii=False)
        print("JSON serialization successful")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_fresh_approach())
    print(f"Fresh approach test: {'PASS' if success else 'FAIL'}")