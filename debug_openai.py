#!/usr/bin/env python3
"""Debug OpenAI API with full content generation flow."""

import asyncio
import json
from packages.gen.content_generator import ContentGenerator
from packages.gen.models import GenerationRequest

async def debug_openai_generation():
    """Debug OpenAI content generation."""
    
    generator = ContentGenerator()
    
    # Create test request
    request = GenerationRequest(
        topic="OpenAI API 테스트",
        provider="openai",
        tone="professional", 
        word_count=500,
        include_images=True,
        target_language="ko"
    )
    
    print("Testing OpenAI content generation...")
    print(f"Request: {request}")
    
    # Create job ID
    job_id = generator.create_job_id()
    print(f"Job ID: {job_id}")
    
    try:
        # Run generation
        await generator.generate_content_async(job_id, request)
        
        # Get result
        result = generator.get_job_result(job_id)
        print(f"Result status: {result.status}")
        print(f"Result error: {result.error}")
        if result.content:
            print(f"Result content preview: {result.content.content[:200]}...")
        
    except Exception as e:
        print(f"Generation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_openai_generation())