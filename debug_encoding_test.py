#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug script to test Gemini API encoding step by step
"""

import os
import json
import httpx
from packages.ai_clients.models import AIRequest, AIMessage

# Set up test data
test_topic = "인공지능 분야에서 활용되고있는지"
print(f"Original topic: {test_topic}")
print(f"Topic bytes (utf-8): {test_topic.encode('utf-8')}")
print(f"Topic repr: {repr(test_topic)}")
print()

# Simulate Gemini API request
async def test_gemini_encoding():
    # Get API key from environment
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("No GEMINI_API_KEY found in environment")
        return
    
    # Create test request
    messages = [
        AIMessage(role="system", content="You are a helpful assistant that writes in Korean."),
        AIMessage(role="user", content=f"'{test_topic}'에 대해 간단히 설명해주세요.")
    ]
    
    # Format request like GeminiClient does
    contents = []
    system_instruction = None
    
    for msg in messages:
        if msg.role == "system":
            system_instruction = {"parts": [{"text": msg.content}]}
        else:
            role = "user" if msg.role == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg.content}]
            })
    
    formatted_request = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1000
        }
    }
    
    if system_instruction:
        formatted_request["systemInstruction"] = system_instruction
    
    print("=== REQUEST PAYLOAD ===")
    print(json.dumps(formatted_request, ensure_ascii=False, indent=2))
    print()
    
    # Make actual API call
    base_url = "https://generativelanguage.googleapis.com"
    model = "gemini-1.5-flash"
    url = f"{base_url}/v1beta/models/{model}:generateContent"
    
    headers = {
        "Content-Type": "application/json; charset=utf-8"
    }
    
    params = {"key": api_key}
    
    print("=== MAKING API CALL ===")
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print()
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url,
                json=formatted_request,
                params=params,
                headers=headers,
                timeout=30.0
            )
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print()
            
            if response.status_code == 200:
                response_data = response.json()
                
                print("=== RAW RESPONSE ===")
                print(json.dumps(response_data, ensure_ascii=False, indent=2)[:1000])
                print("...")
                print()
                
                # Extract content like GeminiClient does
                content = ""
                if (response_data.get("candidates") and 
                    len(response_data["candidates"]) > 0):
                    candidate = response_data["candidates"][0]
                    if candidate.get("content") and candidate["content"].get("parts"):
                        content = candidate["content"]["parts"][0].get("text", "")
                
                print("=== EXTRACTED CONTENT ===")
                print(f"Content type: {type(content)}")
                print(f"Content length: {len(content)}")
                print(f"Content (first 500 chars): {repr(content[:500])}")
                print()
                
                # Test encoding conversion
                print("=== ENCODING TESTS ===")
                print(f"Original content: {content[:100]}")
                
                try:
                    # Test the latin-1 to utf-8 conversion that's in the current code
                    content_bytes = content.encode('latin-1')
                    content_converted = content_bytes.decode('utf-8')
                    print(f"After latin-1 -> utf-8: {content_converted[:100]}")
                except Exception as e:
                    print(f"Latin-1 conversion failed: {e}")
                
                try:
                    # Test direct UTF-8 handling
                    content_utf8 = content.encode('utf-8').decode('utf-8')
                    print(f"Direct UTF-8: {content_utf8[:100]}")
                except Exception as e:
                    print(f"Direct UTF-8 failed: {e}")
                
                return content
                
            else:
                print(f"API Error: {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"Request failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_gemini_encoding())