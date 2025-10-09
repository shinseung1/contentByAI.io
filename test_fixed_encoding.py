#!/usr/bin/env python3
"""
Test if the encoding fixes work
"""

import asyncio
import json
from packages.gen.content_generator import ContentGenerator
from packages.gen.models import GenerationRequest

async def test_fixed_encoding():
    """Test content generation with fixed encoding"""
    
    print("=== TESTING FIXED ENCODING ===")
    
    # Create a simple test request
    request = GenerationRequest(
        topic="인공지능의 활용 방안",  # Korean topic
        provider="gemini",
        tone="professional",
        word_count=300,
        include_images=False,
        target_language="ko"
    )
    
    print(f"Test topic: {request.topic}")
    print(f"Target language: {request.target_language}")
    print()
    
    generator = ContentGenerator()
    job_id = generator.create_job_id()
    
    print(f"Generated job ID: {job_id}")
    
    try:
        # Generate content
        print("Starting content generation...")
        await generator.generate_content_async(job_id, request)
        print("Content generation completed!")
        
        # Check the result
        from database import DatabaseManager
        db = DatabaseManager()
        job = db.get_generation_job(job_id)
        
        if job:
            print(f"\n=== JOB RESULTS ===")
            print(f"Status: {job.status}")
            print(f"Topic in DB: {repr(job.topic)}")
            
            if job.content:
                try:
                    content_obj = json.loads(job.content)
                    title = content_obj.get('title', '')
                    html_content = content_obj.get('html_content', '')
                    
                    print(f"Title: {repr(title)}")
                    print(f"Content length: {len(html_content)}")
                    print(f"Content preview: {html_content[:200]}")
                    
                    # Check for Korean characters
                    import re
                    korean_chars = re.findall(r'[가-힣]+', html_content)
                    print(f"Korean words found: {len(korean_chars)}")
                    if korean_chars:
                        print(f"Sample Korean words: {korean_chars[:5]}")
                        print("✓ Encoding appears to be working correctly!")
                    else:
                        print("✗ No Korean characters found - encoding issue may persist")
                        
                except json.JSONDecodeError as e:
                    print(f"JSON parsing error: {e}")
            else:
                print("No content generated")
        else:
            print("Job not found in database")
            
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fixed_encoding())