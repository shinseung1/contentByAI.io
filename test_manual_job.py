#!/usr/bin/env python3
"""Test manual job creation and retrieval."""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_full_job_flow():
    """Test the complete job flow."""
    from packages.gen.content_generator import ContentGenerator
    from packages.gen.models import GenerationRequest
    
    print("Testing full job flow...")
    
    generator = ContentGenerator()
    
    request = GenerationRequest(
        topic="manual test topic",
        provider="openai",
        tone="professional",
        word_count=300,
        include_images=True,  # Test with images enabled
        target_language="ko"
    )
    
    job_id = generator.create_job_id()
    print(f"Created job ID: {job_id}")
    
    try:
        # Run the async generation
        print("Starting content generation...")
        await generator.generate_content_async(job_id, request)
        
        print("Content generation completed, retrieving result...")
        
        # Get the result
        response = generator.get_job_result(job_id)
        print(f"Status: {response.status}")
        
        if response.status.value == 'completed':
            print("Generation successful!")
            print(f"Title: {response.content.title if response.content else 'No title'}")
            print(f"Images: {len(response.content.images) if response.content else 0}")
            return True
        else:
            print(f"Generation failed: {response.error}")
            return False
            
    except Exception as e:
        print(f"Exception during generation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_full_job_flow())
    print(f"Manual job test result: {'PASS' if success else 'FAIL'}")