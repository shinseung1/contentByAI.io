#!/usr/bin/env python3
"""Test response serialization."""

import json
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_response_serialization():
    """Test if GenerationResponse can be serialized."""
    from packages.gen.models import GenerationResponse, GeneratedContent, GenerationStatus
    
    print("Testing response serialization...")
    
    # Create a GeneratedContent with dict images
    content = GeneratedContent(
        title="Test Title",
        content="<p>Test content</p>",
        markdown_content="# Test markdown",
        summary="Test summary",
        tags=["test", "content"],
        images=[
            {
                "url": "https://example.com/image1.jpg",
                "alt": "Test image 1",
                "caption": "Test caption 1"
            },
            {
                "url": "https://example.com/image2.jpg", 
                "alt": "Test image 2",
                "caption": "Test caption 2"
            }
        ]
    )
    
    response = GenerationResponse(
        job_id="test-job-123",
        status=GenerationStatus.COMPLETED,
        message="Test completed",
        progress=1.0,
        content=content,
        error=None,
        created_at="2023-01-01T00:00:00",
        completed_at="2023-01-01T00:01:00"
    )
    
    try:
        # Test Pydantic serialization
        response_dict = response.model_dump()
        print("+ Pydantic model_dump() successful")
        
        # Test JSON serialization
        json_str = json.dumps(response_dict, ensure_ascii=False)
        print("+ JSON serialization successful")
        
        # Test back to object
        back_to_dict = json.loads(json_str)
        print("+ JSON deserialization successful")
        
        return True
        
    except Exception as e:
        print(f"- Serialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_response_serialization()
    if success:
        print("Response serialization test passed")
    else:
        print("Response serialization test failed")