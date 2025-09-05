#!/usr/bin/env python3
"""Test Asiana mileage with fixed prompts."""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_asiana_fixed():
    """Test with Asiana mileage topic using fixed prompts."""
    from packages.gen.content_generator import ContentGenerator
    from packages.gen.models import GenerationRequest
    
    print("Testing Asiana mileage with fixed prompts...")
    
    generator = ContentGenerator()
    
    request = GenerationRequest(
        topic="아시아나 마일리지 사용 꿀팁",
        provider="openai",
        tone="professional", 
        word_count=1800,
        include_images=True,
        target_language="ko"
    )
    
    job_id = generator.create_job_id()
    print(f"Created job ID: {job_id}")
    
    try:
        print("Starting generation with fixed prompts...")
        await generator.generate_content_async(job_id, request)
        
        print("Generation completed, analyzing...")
        
        # Get the result
        response = generator.get_job_result(job_id)
        print(f"Status: {response.status}")
        
        if response.status.value == 'completed':
            print("SUCCESS: Generation completed!")
            
            # Save and analyze content
            if response.content and response.content.content:
                with open('asiana_fixed_content.html', 'w', encoding='utf-8') as f:
                    f.write(response.content.content)
                
                # Quick analysis
                content = response.content.content
                import re
                
                # Check for problematic links
                google_links = re.findall(r'google\.com', content, re.IGNORECASE)
                see_more = re.findall(r'바로가기|자세히.*?보기', content, re.IGNORECASE)
                all_links = re.findall(r'<a[^>]*>', content, re.IGNORECASE)
                tables = re.findall(r'<table[^>]*>', content, re.IGNORECASE)
                h2_sections = re.findall(r'<h2[^>]*>', content, re.IGNORECASE)
                em_dash = '—' in content
                
                print(f"Content length: {len(content)} characters")
                print(f"H2 sections: {len(h2_sections)}")
                print(f"Tables: {len(tables)}")
                print(f"Google links: {len(google_links)}")
                print(f"See more/바로가기: {len(see_more)}")
                print(f"All links: {len(all_links)}")
                print(f"Em dash in title: {em_dash}")
                
                # Success criteria
                success_score = 0
                if len(h2_sections) >= 8: success_score += 2
                if len(tables) >= 3: success_score += 2
                if len(google_links) == 0: success_score += 2
                if len(see_more) == 0: success_score += 2
                if len(all_links) == 0: success_score += 1
                if em_dash: success_score += 1
                
                print(f"SUCCESS SCORE: {success_score}/10")
                
                return job_id, success_score
            else:
                print("No content generated")
                return job_id, 0
        else:
            print(f"FAILED: {response.error}")
            return None, 0
            
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()
        return None, 0

if __name__ == "__main__":
    job_id, score = asyncio.run(test_asiana_fixed())
    if job_id and score >= 8:
        print(f"🎉 EXCELLENT RESULT! Job {job_id} scored {score}/10")
        print("✅ Ready for UI testing")
    elif job_id and score >= 6:
        print(f"👍 GOOD RESULT! Job {job_id} scored {score}/10")  
        print("⚠️ Minor improvements needed")
    elif job_id:
        print(f"⚠️ NEEDS WORK: Job {job_id} scored {score}/10")
        print("❌ Major improvements needed")  
    else:
        print("❌ COMPLETE FAILURE: No content generated")