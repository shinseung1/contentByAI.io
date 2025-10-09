#!/usr/bin/env python3
"""
Test complete content generation pipeline for Korean encoding
"""

import asyncio
import json
from packages.gen.content_generator import ContentGenerator
from packages.gen.models import GenerationRequest

async def test_complete_pipeline():
    """Test the complete content generation pipeline with Korean text"""
    
    print("Starting complete pipeline test...")
    
    # Create a simple test request with Korean topic
    request = GenerationRequest(
        topic="한국의 전통 음식과 문화",  # Korean traditional food and culture
        provider="gemini", 
        tone="professional",
        word_count=300,  # Minimum required
        include_images=False,
        target_language="ko"
    )
    
    print("Test request created")
    
    generator = ContentGenerator()
    job_id = generator.create_job_id()
    
    print(f"Job ID: {job_id}")
    
    try:
        # Generate content
        await generator.generate_content_async(job_id, request)
        print("Content generation completed")
        
        # Check the result
        from database import DatabaseManager
        db = DatabaseManager()
        job = db.get_generation_job(job_id)
        
        if job and job.content:
            try:
                content_obj = json.loads(job.content)
                title = content_obj.get('title', '')
                html_content = content_obj.get('html_content', '')
                
                # Count Korean characters 
                import re
                korean_chars_title = len(re.findall(r'[가-힣]+', title))
                korean_chars_content = len(re.findall(r'[가-힣]+', html_content))
                
                # Write results to file
                with open('pipeline_test_results.txt', 'w', encoding='utf-8') as f:
                    f.write("=== COMPLETE PIPELINE TEST RESULTS ===\n")
                    f.write(f"Job ID: {job_id}\n")
                    f.write(f"Status: {job.status}\n")
                    f.write(f"Original topic: {request.topic}\n")
                    f.write(f"Topic in DB: {job.topic}\n\n")
                    
                    f.write(f"Generated title: {title}\n")
                    f.write(f"Korean words in title: {korean_chars_title}\n")
                    f.write(f"Korean words in content: {korean_chars_content}\n\n")
                    
                    f.write("Content preview (first 500 chars):\n")
                    f.write(html_content[:500] + "...\n\n")
                    
                    if korean_chars_title > 0 and korean_chars_content > 0:
                        f.write("SUCCESS: Korean characters found in both title and content!\n")
                        f.write("The encoding fix appears to be working correctly.\n")
                    elif korean_chars_title > 0 or korean_chars_content > 0:
                        f.write("PARTIAL SUCCESS: Korean characters found in some content.\n")
                    else:
                        f.write("FAILURE: No Korean characters found in generated content.\n")
                
                print("Pipeline test completed - check pipeline_test_results.txt")
                print(f"Korean chars found - title: {korean_chars_title}, content: {korean_chars_content}")
                
                return korean_chars_title > 0 and korean_chars_content > 0
                
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")
                return False
        else:
            print("No job content found")
            return False
            
    except Exception as e:
        print(f"Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test_complete_pipeline())
        if result:
            print("OVERALL: Pipeline test SUCCESSFUL")
        else:
            print("OVERALL: Pipeline test FAILED")
    except Exception as e:
        print(f"Test error: {e}")