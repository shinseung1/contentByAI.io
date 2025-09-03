#!/usr/bin/env python3
"""Simple test without unicode characters."""

import asyncio
import httpx

async def simple_test():
    """Simple test."""
    
    request_data = {
        "topic": "test topic",
        "provider": "openai",
        "tone": "professional",
        "word_count": 300,
        "include_images": True,
        "target_language": "ko"
    }
    
    print("Starting simple test...")
    
    try:
        async with httpx.AsyncClient() as client:
            # Start generation
            response = await client.post(
                "http://127.0.0.1:3000/api/v1/generation/generate",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                job_data = response.json()
                job_id = job_data["job_id"]
                print(f"Job ID: {job_id}")
                
                # Wait and check result
                await asyncio.sleep(30)
                
                job_response = await client.get(f"http://127.0.0.1:3000/api/v1/generation/jobs/{job_id}")
                job_result = job_response.json()
                
                print(f"Final status: {job_result['status']}")
                if job_result['status'] == 'failed':
                    print(f"Error: {job_result.get('error', 'No error message')}")
                elif job_result['status'] == 'completed':
                    print("SUCCESS!")
                    
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(simple_test())