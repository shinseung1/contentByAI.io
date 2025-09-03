#!/usr/bin/env python3
"""Test API directly with requests library."""

import asyncio
import httpx
import json

async def test_api_direct():
    """Test API generation directly."""
    
    # Test data
    request_data = {
        "topic": "아시아나 항공 마일리지 사용법",
        "provider": "openai",
        "tone": "professional",
        "word_count": 600,
        "include_images": True,
        "target_language": "ko"
    }
    
    print("Testing API generation...")
    print(f"Request: {request_data}")
    
    try:
        async with httpx.AsyncClient() as client:
            # Start generation
            response = await client.post(
                "http://127.0.0.1:3000/api/v1/generation/generate",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 200:
                job_data = response.json()
                job_id = job_data["job_id"]
                print(f"Job ID: {job_id}")
                
                # Poll for result
                for i in range(30):  # Wait up to 30 seconds
                    await asyncio.sleep(2)
                    
                    job_response = await client.get(f"http://127.0.0.1:3000/api/v1/generation/jobs/{job_id}")
                    job_result = job_response.json()
                    
                    print(f"Poll {i+1}: Status = {job_result['status']}")
                    
                    if job_result['status'] == 'completed':
                        print("✅ Generation completed!")
                        if job_result.get('content'):
                            print(f"Content preview: {job_result['content']['content'][:100]}...")
                        break
                    elif job_result['status'] == 'failed':
                        print(f"❌ Generation failed: {job_result.get('error', 'Unknown error')}")
                        break
            else:
                print("Failed to start generation")
                
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api_direct())