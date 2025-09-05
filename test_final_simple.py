#!/usr/bin/env python3
"""Final simple test."""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_final():
    """Final test with simplified prompts."""
    from packages.gen.content_generator import ContentGenerator
    from packages.gen.models import GenerationRequest
    
    print("Final test with ultra-simplified prompts...")
    
    generator = ContentGenerator()
    
    request = GenerationRequest(
        topic="아시아나 마일리지 사용 꿀팁",
        provider="openai",
        tone="professional", 
        word_count=1200,  # Shorter target
        include_images=True,
        target_language="ko"
    )
    
    job_id = generator.create_job_id()
    print(f"Job ID: {job_id}")
    
    try:
        await generator.generate_content_async(job_id, request)
        response = generator.get_job_result(job_id)
        
        if response.status.value == 'completed':
            print("SUCCESS!")
            
            if response.content and response.content.content:
                content = response.content.content
                print(f"Content length: {len(content)} chars")
                
                # Save for UI testing
                with open('final_test_content.html', 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Quick check
                import re
                has_em_dash = '—' in content
                h2_count = len(re.findall(r'<h2[^>]*>', content, re.IGNORECASE))
                table_count = len(re.findall(r'<table[^>]*>', content, re.IGNORECASE))
                google_links = len(re.findall(r'google\.com', content, re.IGNORECASE))
                
                print(f"Em dash: {has_em_dash}")
                print(f"H2 sections: {h2_count}")
                print(f"Tables: {table_count}")
                print(f"Google links: {google_links}")
                
                if h2_count >= 5 and table_count >= 1 and google_links == 0:
                    print("READY FOR UI TESTING!")
                    return job_id
                else:
                    print("Needs more work")
                    return job_id
            else:
                print("No content generated")
                return None
        else:
            print(f"Failed: {response.error}")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    job_id = asyncio.run(test_final())
    print(f"Final result: {job_id}")