#!/usr/bin/env python3
"""Test simplified prompt generation."""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_simplified():
    """Test generation with simplified prompt."""
    from packages.gen.content_generator import ContentGenerator
    from packages.gen.models import GenerationRequest
    
    print("Testing simplified prompt generation...")
    
    generator = ContentGenerator()
    
    request = GenerationRequest(
        topic="대한항공 스카이패스 마일리지 적립과 사용방법",
        provider="openai",
        tone="professional", 
        word_count=1500,  # Reasonable length
        include_images=True,
        target_language="ko"
    )
    
    job_id = generator.create_job_id()
    print(f"Created job ID: {job_id}")
    
    try:
        print("Starting simplified generation...")
        await generator.generate_content_async(job_id, request)
        
        print("Generation completed, checking result...")
        
        # Get the result
        response = generator.get_job_result(job_id)
        print(f"Status: {response.status}")
        
        if response.status.value == 'completed':
            print("SUCCESS: Generation completed!")
            print(f"Content length: {len(response.content.content) if response.content else 0}")
            print(f"Images: {len(response.content.images) if response.content else 0}")
            
            return job_id
        else:
            print(f"FAILED: {response.error}")
            return None
            
    except Exception as e:
        print(f"Exception: {e}")
        return None

if __name__ == "__main__":
    job_id = asyncio.run(test_simplified())
    if job_id:
        print(f"SUCCESS: Job {job_id}")
    else:
        print("FAILED: No job ID returned")