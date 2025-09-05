#!/usr/bin/env python3
"""Test content generation with template-specific topic."""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_template_comparison():
    """Test generation with a topic similar to templates."""
    from packages.gen.content_generator import ContentGenerator
    from packages.gen.models import GenerationRequest
    
    print("Testing template comparison with airline topic...")
    
    generator = ContentGenerator()
    
    request = GenerationRequest(
        topic="대한항공 스카이패스 마일리지 적립과 사용방법",  # Same as template
        provider="openai",
        tone="professional", 
        word_count=1000,
        include_images=True,
        target_language="ko"
    )
    
    job_id = generator.create_job_id()
    print(f"Created job ID: {job_id}")
    
    try:
        print("Starting content generation...")
        await generator.generate_content_async(job_id, request)
        
        print("Content generation completed, retrieving result...")
        
        # Get the result
        response = generator.get_job_result(job_id)
        print(f"Status: {response.status}")
        
        if response.status.value == 'completed':
            print("Generation successful!")
            print(f"Title: {response.content.title if response.content else 'No title'}")
            print(f"Content length: {len(response.content.content) if response.content else 0}")
            print(f"Images: {len(response.content.images) if response.content else 0}")
            
            # Save content to file for analysis
            if response.content and response.content.content:
                with open("generated_content.html", "w", encoding="utf-8") as f:
                    f.write(response.content.content)
                print("Content saved to generated_content.html")
            
            return job_id
        else:
            print(f"Generation failed: {response.error}")
            return None
            
    except Exception as e:
        print(f"Exception during generation: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    job_id = asyncio.run(test_template_comparison())
    print(f"Template comparison test result: {'PASS' if job_id else 'FAIL'}")
    if job_id:
        print(f"Job ID for comparison: {job_id}")