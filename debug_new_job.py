#!/usr/bin/env python3
"""
Debug the new job aae0d82a-36df-40a1-8b9f-7c2e527720a9
"""

import json
from database import DatabaseManager

def debug_new_job():
    """Debug the new job to see Korean text issues"""
    
    job_id = 'aae0d82a-36df-40a1-8b9f-7c2e527720a9'
    
    db = DatabaseManager()
    job = db.get_generation_job(job_id)
    
    if not job:
        print(f"Job {job_id} not found!")
        return
    
    print(f"=== DEBUGGING JOB {job_id} ===")
    print(f"Status: {job.status}")
    print(f"Topic: {repr(job.topic)}")
    print(f"Created: {job.created_at}")
    print()
    
    if job.content:
        try:
            content_obj = json.loads(job.content)
            
            # Save full content to file for analysis
            with open('new_job_full_content.json', 'w', encoding='utf-8') as f:
                json.dump(content_obj, f, ensure_ascii=False, indent=2)
            
            print("Full content saved to 'new_job_full_content.json'")
            
            title = content_obj.get('title', '')
            html_content = content_obj.get('html_content', '')
            
            print(f"Title: {repr(title)}")
            print(f"Title length: {len(title)}")
            
            # Check for Korean characters in title
            korean_chars_title = sum(1 for c in title if '\uAC00' <= c <= '\uD7AF')
            print(f"Korean chars in title: {korean_chars_title}")
            
            # Check HTML content
            print(f"HTML content length: {len(html_content)}")
            
            # Save HTML content to file
            with open('new_job_html_content.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print("HTML content saved to 'new_job_html_content.html'")
            
            # Check for Korean in HTML
            korean_chars_html = sum(1 for c in html_content if '\uAC00' <= c <= '\uD7AF')
            print(f"Korean chars in HTML content: {korean_chars_html}")
            
            # Look for any Korean text patterns
            import re
            korean_words = re.findall(r'[가-힣]+', html_content)
            print(f"Korean words found: {len(korean_words)}")
            if korean_words:
                print(f"Sample Korean words: {korean_words[:5]}")
            
            # Check if this looks like our emoji removal issue
            spaces_count = html_content.count('   ')  # Multiple spaces might indicate removed Korean
            print(f"Multiple spaces found: {spaces_count}")
            
            # Look for embedded JSON in HTML
            if '```json' in html_content:
                print("Found embedded JSON in HTML")
                start = html_content.find('{')
                end = html_content.rfind('}') + 1
                if start != -1 and end > start:
                    embedded_json = html_content[start:end]
                    try:
                        embedded_data = json.loads(embedded_json)
                        embedded_title = embedded_data.get('title', '')
                        korean_in_embedded = sum(1 for c in embedded_title if '\uAC00' <= c <= '\uD7AF')
                        print(f"Korean chars in embedded JSON title: {korean_in_embedded}")
                        
                        with open('new_job_embedded_json.json', 'w', encoding='utf-8') as f:
                            json.dump(embedded_data, f, ensure_ascii=False, indent=2)
                        print("Embedded JSON saved to 'new_job_embedded_json.json'")
                        
                    except json.JSONDecodeError as e:
                        print(f"Failed to parse embedded JSON: {e}")
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse job content: {e}")
            print(f"Raw content: {job.content[:200]}...")
    else:
        print("No content in job")

if __name__ == "__main__":
    debug_new_job()