#!/usr/bin/env python3
"""
Test the complete encoding flow from request to database storage
"""

import os
import json
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def test_complete_flow():
    """Test the complete flow to identify where encoding breaks"""
    
    # Test with proper Korean text
    test_topic = "인공지능의 활용 방안"
    
    print("=== STARTING ENCODING FLOW TEST ===")
    print(f"Original topic: {test_topic}")
    print(f"Topic bytes (UTF-8): {test_topic.encode('utf-8')}")
    print(f"Topic hex: {test_topic.encode('utf-8').hex()}")
    print()
    
    try:
        # Step 1: Test Gemini API directly without any encoding fixes
        from packages.ai_clients.models import AIClientConfig, AIRequest, AIMessage
        import httpx
        
        api_key = os.getenv('GEMINI_API_KEY')
        model = "gemini-2.5-flash"
        
        # Create request
        messages = [
            AIMessage(role="user", content=f"'{test_topic}'에 대해 간단히 한국어로 설명해주세요.")
        ]
        
        # Format request manually to see exact data
        contents = []
        for msg in messages:
            contents.append({
                "role": "user",
                "parts": [{"text": msg.content}]
            })
        
        request_data = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 500
            }
        }
        
        print("=== REQUEST TO GEMINI ===")
        request_json = json.dumps(request_data, ensure_ascii=False, indent=2)
        print(f"Request JSON (first 300 chars): {request_json[:300]}")
        print(f"Request JSON bytes: {request_json.encode('utf-8')[:100].hex()}")
        print()
        
        # Make API call
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        headers = {
            "Content-Type": "application/json; charset=utf-8"
        }
        params = {"key": api_key}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=request_data,  # Let httpx handle JSON encoding
                params=params,
                headers=headers,
                timeout=30.0
            )
            
            print(f"=== GEMINI RESPONSE ===")
            print(f"Status: {response.status_code}")
            print(f"Response encoding: {response.encoding}")
            print(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                # Get raw response
                response_text = response.text
                print(f"Raw response text (first 300 chars): {response_text[:300]}")
                print(f"Raw response bytes: {response_text.encode('utf-8')[:100].hex()}")
                print()
                
                # Parse JSON
                response_data = response.json()
                
                # Extract content without any encoding fixes
                content = ""
                if (response_data.get("candidates") and 
                    len(response_data["candidates"]) > 0):
                    candidate = response_data["candidates"][0]
                    if candidate.get("content") and candidate["content"].get("parts"):
                        content = candidate["content"]["parts"][0].get("text", "")
                
                print(f"=== EXTRACTED CONTENT (NO ENCODING FIXES) ===")
                print(f"Content type: {type(content)}")
                print(f"Content length: {len(content)}")
                print(f"Content (first 200 chars): {content[:200]}")
                print(f"Content repr: {repr(content[:200])}")
                print(f"Content bytes: {content.encode('utf-8')[:100].hex()}")
                print()
                
                # Test if content is already properly encoded
                print("=== ENCODING VERIFICATION ===")
                try:
                    # Check if content contains proper Korean
                    import re
                    korean_chars = re.findall(r'[가-힣]+', content)
                    print(f"Found Korean characters: {korean_chars[:3]}")
                    
                    if korean_chars:
                        print("✓ Content contains proper Korean characters - no encoding fix needed!")
                        return content
                    else:
                        print("✗ No Korean characters found - there might be an encoding issue")
                        
                        # Try the latin-1 fix to see what happens
                        try:
                            content_fixed = content.encode('latin-1').decode('utf-8')
                            korean_chars_fixed = re.findall(r'[가-힣]+', content_fixed)
                            print(f"After latin-1 fix: {korean_chars_fixed[:3]}")
                            if korean_chars_fixed:
                                print("✓ Latin-1 fix worked!")
                                return content_fixed
                        except Exception as e:
                            print(f"Latin-1 fix failed: {e}")
                            
                except Exception as e:
                    print(f"Encoding verification failed: {e}")
                
                return content
                
            else:
                print(f"API Error: {response.status_code}")
                print(f"Error response: {response.text}")
                return None
                
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_complete_flow())