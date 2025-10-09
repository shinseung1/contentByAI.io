#!/usr/bin/env python3
"""
Test raw Gemini response to see actual Korean characters
"""

import asyncio
import json
import os
import sys
from dotenv import load_dotenv
from packages.ai_clients.models import AIClientConfig, AIRequest, AIMessage
from packages.ai_clients.gemini_client import GeminiClient

load_dotenv()

async def test_raw_gemini():
    """Test what Gemini actually returns for Korean content"""
    
    print("=== RAW GEMINI TEST ===")
    
    # Create client
    config = AIClientConfig(
        api_key=os.getenv('GEMINI_API_KEY'),
        model="gemini-2.5-flash",
        temperature=0.7,
        max_tokens=500
    )
    
    client = GeminiClient(config)
    
    # Create request for Korean content
    request = AIRequest(
        messages=[
            AIMessage(role="user", content="Generate a simple JSON response with Korean text. Include title and content fields with Korean text about AI technology. Keep it simple and valid JSON.")
        ]
    )
    
    try:
        print("Making Gemini request...")
        response = await client.generate(request)
        
        print(f"Response type: {type(response.content)}")
        print(f"Response length: {len(response.content)}")
        
        # Write raw response to file to avoid console encoding issues
        with open('raw_gemini_response.txt', 'w', encoding='utf-8') as f:
            f.write(response.content)
        
        print("Raw response saved to 'raw_gemini_response.txt'")
        
        # Try to find JSON in response
        content = response.content.strip()
        if content.startswith('```json'):
            content = content[7:]
        if content.startswith('```'):
            content = content[3:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        
        # Find JSON boundaries
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        
        if start_idx != -1 and end_idx > start_idx:
            json_str = content[start_idx:end_idx]
            
            # Save JSON to file
            with open('extracted_json.txt', 'w', encoding='utf-8') as f:
                f.write(json_str)
            
            print("Extracted JSON saved to 'extracted_json.txt'")
            
            # Try to parse JSON
            try:
                data = json.loads(json_str)
                print("JSON parsing successful!")
                
                title = data.get('title', '')
                print(f"Title length: {len(title)}")
                
                # Save parsed data
                with open('parsed_data.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                print("Parsed data saved to 'parsed_data.json'")
                
                # Check for Korean characters in raw bytes
                title_bytes = title.encode('utf-8')
                print(f"Title bytes: {title_bytes}")
                
                # Check for Korean character ranges
                korean_count = 0
                for char in title:
                    if '가' <= char <= '힣':
                        korean_count += 1
                
                print(f"Korean characters found: {korean_count}")
                
                if korean_count > 0:
                    print("SUCCESS: Korean characters properly preserved!")
                else:
                    print("No Korean characters found in parsed title")
                    
            except json.JSONDecodeError as e:
                print(f"JSON parsing failed: {e}")
                print(f"JSON string (first 200 chars): {repr(json_str[:200])}")
        else:
            print("No JSON found in response")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_raw_gemini())