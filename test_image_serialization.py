#!/usr/bin/env python3
"""Test image serialization issue."""

import asyncio
import json
from packages.gen.content_generator import ContentGenerator
from packages.gen.models import GenerationRequest

async def test_image_serialization():
    """Test content generation with image serialization."""
    
    generator = ContentGenerator()
    
    # Test with images enabled
    request = GenerationRequest(
        topic="AI 기술의 미래",
        provider="openai",
        tone="professional", 
        word_count=400,
        include_images=True,
        target_language="ko"
    )
    
    print("Testing image serialization...")
    print(f"Request: {request.topic}")
    
    job_id = generator.create_job_id()
    print(f"Job ID: {job_id}")
    
    try:
        # Run generation
        await generator.generate_content_async(job_id, request)
        
        # Get result
        result = generator.get_job_result(job_id)
        print(f"Status: {result.status}")
        
        if result.error:
            print(f"Error: {result.error}")
        
        if result.content:
            print(f"Title: {result.content.title}")
            print(f"Content length: {len(result.content.content)}")
            print(f"Images count: {len(result.content.images) if result.content.images else 0}")
            if result.content.images:
                print("First image:", result.content.images[0])
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_image_serialization())