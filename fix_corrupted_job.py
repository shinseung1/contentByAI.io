#!/usr/bin/env python3
"""
Fix corrupted job by regenerating content with proper encoding
"""

import asyncio
import json
from database import DatabaseManager
from packages.gen.content_generator import ContentGenerator
from packages.gen.models import GenerationRequest

async def fix_job_encoding():
    """Fix the corrupted job by regenerating its content"""
    
    corrupted_job_id = '8a3c9fb7-ee33-4b66-ac04-e94600a1b166'
    good_job_id = 'c885aa61-dbfd-4d85-bde7-0869236d0274'
    
    db = DatabaseManager()
    
    # Get the corrupted job
    corrupted_job = db.get_generation_job(corrupted_job_id)
    if not corrupted_job:
        print(f"Corrupted job {corrupted_job_id} not found!")
        return
    
    # Get the good job to copy settings
    good_job = db.get_generation_job(good_job_id)
    if not good_job:
        print(f"Good job {good_job_id} not found!")
        return
    
    print(f"=== FIXING JOB {corrupted_job_id} ===")
    print(f"Original topic: {repr(corrupted_job.topic)}")
    print(f"Provider: {corrupted_job.provider}")
    print(f"Settings: tone={corrupted_job.tone}, word_count={corrupted_job.word_count}")
    
    # Create a new generation request with same settings
    request = GenerationRequest(
        topic="대한민국 가장 이슈 top 3",  # Fixed Korean topic
        provider=corrupted_job.provider,
        tone=corrupted_job.tone,
        word_count=corrupted_job.word_count,
        include_images=corrupted_job.include_images,
        target_language=corrupted_job.target_language or "ko"
    )
    
    print(f"Regenerating content with fixed encoding...")
    print(f"Request topic: {request.topic}")
    
    # Generate new content
    generator = ContentGenerator()
    
    try:
        # Generate content using the same job ID (this will update the existing job)
        await generator.generate_content_async(corrupted_job_id, request)
        
        print("Content regeneration completed!")
        
        # Verify the fix
        updated_job = db.get_generation_job(corrupted_job_id)
        if updated_job and updated_job.content:
            try:
                content_obj = json.loads(updated_job.content)
                title = content_obj.get('title', '')
                html_content = content_obj.get('html_content', '')
                
                # Count Korean characters
                korean_chars_title = sum(1 for c in title if '\uAC00' <= c <= '\uD7AF')
                korean_chars_html = sum(1 for c in html_content if '\uAC00' <= c <= '\uD7AF')
                
                print(f"\n=== VERIFICATION ===")
                print(f"New title: {repr(title[:100])}...")
                print(f"Korean chars in title: {korean_chars_title}")
                print(f"Korean chars in HTML: {korean_chars_html}")
                
                if korean_chars_title > 0 and korean_chars_html > 0:
                    print("✓ SUCCESS: Job has been fixed with proper Korean encoding!")
                    
                    # Save the fixed content sample
                    with open('job1_fixed_content_sample.txt', 'w', encoding='utf-8') as f:
                        f.write(f"Title: {title}\n\n")
                        f.write(f"HTML (first 1000 chars): {html_content[:1000]}")
                    
                    print("Fixed content sample saved to 'job1_fixed_content_sample.txt'")
                else:
                    print("✗ ISSUE: Korean characters still missing")
                    
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")
        else:
            print("No content generated")
            
    except Exception as e:
        print(f"Error during regeneration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(fix_job_encoding())