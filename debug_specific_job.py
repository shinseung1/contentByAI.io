#!/usr/bin/env python3
"""
Debug the specific job e7afd5f7-8145-452e-ad57-01c2e21b9dee to find where Korean gets lost
"""

import json
import re
from database import DatabaseManager

def debug_job_processing():
    """Debug the exact job to see where Korean text disappears"""
    
    db = DatabaseManager()
    job = db.get_generation_job('e7afd5f7-8145-452e-ad57-01c2e21b9dee')
    
    if not job:
        print("Job not found!")
        return
    
    print("=== DEBUGGING JOB PROCESSING ===")
    print(f"Job ID: {job.job_id}")
    print(f"Topic: {repr(job.topic)}")
    
    # The topic bytes are correct UTF-8
    topic_bytes = b'\xec\x9d\xb8\xea\xb3\xb5\xec\xa7\x80\xeb\x8a\xa5 \xea\xb8\xb0\xec\x88\xa0\xec\x9d\x98 \xeb\xb0\x9c\xec\xa0\x84'
    topic_decoded = topic_bytes.decode('utf-8')
    print(f"Correct topic: {topic_decoded}")
    print()
    
    # Load the content
    content_obj = json.loads(job.content)
    
    # The raw HTML content contains the original JSON response
    html_content = content_obj['html_content']
    print(f"HTML content length: {len(html_content)}")
    
    # Extract the JSON from the HTML content
    if html_content.startswith('```json'):
        print("Found embedded JSON in HTML content")
        
        # Find the JSON boundaries
        start_idx = html_content.find('{')
        end_idx = html_content.rfind('}') + 1
        
        if start_idx != -1 and end_idx > start_idx:
            embedded_json = html_content[start_idx:end_idx]
            
            print("=== ANALYZING EMBEDDED JSON ===")
            print(f"JSON length: {len(embedded_json)}")
            
            # Save to file for analysis
            with open('embedded_json_debug.txt', 'w', encoding='utf-8') as f:
                f.write(embedded_json)
            
            print("Embedded JSON saved to 'embedded_json_debug.txt'")
            
            # Try to parse the embedded JSON
            try:
                embedded_data = json.loads(embedded_json)
                print("Embedded JSON parsed successfully!")
                
                embedded_title = embedded_data.get('title', '')
                print(f"Embedded title: {repr(embedded_title)}")
                print(f"Embedded title length: {len(embedded_title)}")
                
                # Count Korean characters
                korean_count = sum(1 for c in embedded_title if '가' <= c <= '힣')
                print(f"Korean chars in embedded title: {korean_count}")
                
                if korean_count > 0:
                    print("✓ Korean found in embedded JSON!")
                    
                    # This means the issue is in the processing after JSON extraction
                    print("ISSUE: Korean gets lost during JSON processing in ContentGenerator")
                    
                else:
                    print("✗ No Korean in embedded JSON")
                    print("ISSUE: Korean gets corrupted before JSON storage")
                
            except json.JSONDecodeError as e:
                print(f"Failed to parse embedded JSON: {e}")
                print("ISSUE: JSON structure is malformed")
        else:
            print("No JSON found in HTML content")
    else:
        print("HTML content doesn't start with ```json")
        print(f"Content starts with: {repr(html_content[:100])}")

def test_text_processing_functions():
    """Test the text processing functions to see if they corrupt Korean"""
    
    test_korean = "인공지능 기술의 발전"
    print(f"\n=== TESTING TEXT PROCESSING ===")
    print(f"Original: {test_korean}")
    
    # Test safe_print function
    from packages.gen.content_generator import safe_print, remove_emojis
    
    safe_result = safe_print(test_korean)
    print(f"After safe_print: {safe_result}")
    
    emoji_result = remove_emojis(test_korean)
    print(f"After remove_emojis: {emoji_result}")
    
    # Test if these functions are corrupting Korean
    if test_korean != safe_result:
        print("WARNING: safe_print is modifying Korean text!")
    
    if test_korean != emoji_result:
        print("WARNING: remove_emojis is modifying Korean text!")

if __name__ == "__main__":
    debug_job_processing()
    test_text_processing_functions()