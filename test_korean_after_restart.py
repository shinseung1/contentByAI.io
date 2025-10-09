#!/usr/bin/env python3
"""
Test Korean content generation after server restart
"""

import asyncio
import json
from packages.gen.content_generator import ContentGenerator
from packages.gen.models import GenerationRequest

async def test_korean_after_restart():
    """Test Korean content generation after server restart"""
    
    print("Testing Korean content generation after server restart...")
    
    # Create request with Korean topic
    request = GenerationRequest(
        topic="한국의 K-팝 문화와 세계적 영향",  # K-pop culture and global influence
        provider="gemini",
        tone="friendly", 
        word_count=300,
        include_images=False,
        target_language="ko"
    )
    
    print(f"Test topic: {request.topic}")
    
    generator = ContentGenerator()
    job_id = generator.create_job_id()
    
    print(f"Job ID: {job_id}")
    
    try:
        # Generate content
        await generator.generate_content_async(job_id, request)
        print("Content generation completed")
        
        # Check the result immediately
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
                with open('korean_test_after_restart.txt', 'w', encoding='utf-8') as f:
                    f.write("=== KOREAN TEST AFTER SERVER RESTART ===\n")
                    f.write(f"Job ID: {job_id}\n")
                    f.write(f"Status: {job.status}\n")
                    f.write(f"Original topic: {request.topic}\n")
                    f.write(f"Topic in DB: {job.topic}\n\n")
                    
                    f.write(f"Generated title: {title}\n")
                    f.write(f"Korean words in title: {korean_chars_title}\n")
                    f.write(f"Korean words in content: {korean_chars_content}\n\n")
                    
                    f.write("Content preview (first 1000 chars):\n")
                    f.write(html_content[:1000] + "...\n\n")
                    
                    if korean_chars_title > 0 and korean_chars_content > 0:
                        f.write("SUCCESS: Korean characters found in both title and content!\n")
                        f.write("The encoding fix has been successfully applied.\n")
                    elif korean_chars_title > 0 or korean_chars_content > 0:
                        f.write("PARTIAL SUCCESS: Korean characters found in some content.\n")
                    else:
                        f.write("FAILURE: No Korean characters found in generated content.\n")
                        f.write("The encoding issue may still persist.\n")
                
                print("Test completed - check korean_test_after_restart.txt")
                print(f"Korean chars found - title: {korean_chars_title}, content: {korean_chars_content}")
                
                if korean_chars_title > 0 and korean_chars_content > 0:
                    print("✓ SUCCESS: Korean encoding fix is working!")
                    return True
                else:
                    print("✗ ISSUE: Korean characters still missing")
                    return False
                
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")
                return False
        else:
            print("No job content found")
            return False
            
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test_korean_after_restart())
        if result:
            print("\nOVERALL: Korean encoding fix SUCCESSFUL")
        else:
            print("\nOVERALL: Korean encoding issue PERSISTS")
    except Exception as e:
        print(f"Test error: {e}")