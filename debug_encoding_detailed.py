#!/usr/bin/env python3
"""
Detailed encoding debug for the specific job issue
"""

import os
import json
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def debug_job_encoding():
    """Debug the specific job encoding issue"""
    
    print("=== SYSTEM ENCODING INFO ===")
    print(f"Default encoding: {sys.getdefaultencoding()}")
    print(f"File system encoding: {sys.getfilesystemencoding()}")
    print(f"Stdout encoding: {sys.stdout.encoding}")
    print()
    
    # Test topic from the job
    print("=== TOPIC ENCODING TEST ===")
    
    # This is what the topic should be (in Korean)
    correct_topic = "인공지능 분야에서 활용되고있는지"
    print(f"Correct topic: {correct_topic}")
    print(f"Correct topic bytes: {correct_topic.encode('utf-8')}")
    print(f"Correct topic repr: {repr(correct_topic)}")
    print()
    
    # Check the database content for the job
    try:
        from database import DatabaseManager
        
        db = DatabaseManager()
        job = db.get_generation_job('0d02d22d-1839-472e-904a-acc7e6ff25d3')
        
        if job:
            print("=== DATABASE JOB INFO ===")
            print(f"Stored topic: {job.topic}")
            print(f"Stored topic repr: {repr(job.topic)}")
            print(f"Stored topic bytes: {job.topic.encode('utf-8')}")
            print()
            
            # Try to decode the topic in different ways
            print("=== TOPIC DECODE ATTEMPTS ===")
            try:
                # Try treating it as latin-1 encoded UTF-8
                topic_bytes = job.topic.encode('latin-1')
                topic_decoded = topic_bytes.decode('utf-8')
                print(f"Latin-1 -> UTF-8: {topic_decoded}")
            except Exception as e:
                print(f"Latin-1 decode failed: {e}")
            
            try:
                # Try treating it as cp1252 encoded UTF-8
                topic_bytes = job.topic.encode('cp1252')
                topic_decoded = topic_bytes.decode('utf-8')
                print(f"CP1252 -> UTF-8: {topic_decoded}")
            except Exception as e:
                print(f"CP1252 decode failed: {e}")
            
            try:
                # Try direct UTF-8 decode
                topic_decoded = job.topic.encode('utf-8').decode('utf-8')
                print(f"Direct UTF-8: {topic_decoded}")
            except Exception as e:
                print(f"Direct UTF-8 failed: {e}")
            
            print()
            
            # Check the content
            if job.content:
                try:
                    content_obj = json.loads(job.content)
                    print("=== CONTENT TITLE ENCODING ===")
                    title = content_obj.get('title', '')
                    print(f"Stored title: {title}")
                    print(f"Title repr: {repr(title)}")
                    
                    # Try to fix title encoding
                    try:
                        title_bytes = title.encode('latin-1')
                        title_decoded = title_bytes.decode('utf-8')
                        print(f"Title Latin-1 -> UTF-8: {title_decoded}")
                    except Exception as e:
                        print(f"Title Latin-1 decode failed: {e}")
                    
                    print()
                    
                    # Check HTML content
                    html_content = content_obj.get('html_content', '')
                    print("=== HTML CONTENT ENCODING (first 200 chars) ===")
                    print(f"HTML content: {html_content[:200]}")
                    print(f"HTML repr: {repr(html_content[:200])}")
                    
                    # Look for Korean characters in HTML
                    import re
                    korean_chars = re.findall(r'[가-힣]+', html_content)
                    print(f"Found Korean chars: {korean_chars[:5]}")  # First 5 matches
                    
                except json.JSONDecodeError as e:
                    print(f"JSON parse error: {e}")
        else:
            print("Job not found in database!")
            
    except Exception as e:
        print(f"Database error: {e}")
        import traceback
        traceback.print_exc()

def test_gemini_client_encoding():
    """Test the Gemini client encoding specifically"""
    
    print("\n=== GEMINI CLIENT ENCODING TEST ===")
    
    try:
        from packages.ai_clients.gemini_client import GeminiClient
        from packages.ai_clients.models import AIClientConfig, AIRequest, AIMessage
        
        # Set up client
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("No GEMINI_API_KEY found")
            return
            
        config = AIClientConfig(
            api_key=api_key,
            model="gemini-1.5-flash",
            temperature=0.7,
            max_tokens=1000
        )
        
        client = GeminiClient(config)
        
        # Test with simple Korean text
        test_text = "안녕하세요"
        print(f"Test text: {test_text}")
        print(f"Test text bytes: {test_text.encode('utf-8')}")
        
        request = AIRequest(
            messages=[
                AIMessage(role="user", content=f"{test_text}라고 한국어로 답변해주세요")
            ]
        )
        
        print("Making Gemini API call...")
        
        import asyncio
        async def test_call():
            try:
                response = await client.generate(request)
                print(f"Response content: {response.content[:200]}")
                print(f"Response content repr: {repr(response.content[:200])}")
                return response.content
            except Exception as e:
                print(f"API call failed: {e}")
                import traceback
                traceback.print_exc()
                return None
        
        return asyncio.run(test_call())
        
    except Exception as e:
        print(f"Gemini client test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_job_encoding()
    test_gemini_client_encoding()