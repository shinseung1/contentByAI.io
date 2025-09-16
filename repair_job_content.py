#!/usr/bin/env python3
"""Repair malformed JSON content in job."""

import sys
import os
import json
import re
sys.path.insert(0, os.path.abspath('.'))

from database import DatabaseManager

def repair_malformed_json_content(job_id):
    """Repair malformed JSON content for a specific job."""
    
    db = DatabaseManager()
    job = db.get_generation_job(job_id)
    
    if not job or not job.content:
        print(f"Job {job_id} not found or has no content")
        return False
    
    try:
        content_obj = json.loads(job.content)
        html_content = content_obj.get('html_content', '')
        
        if not html_content.startswith('```json'):
            print("Content doesn't appear to have nested JSON issue")
            return False
        
        print(f"Repairing malformed JSON for job: {job.topic}")
        
        # Extract the content between ```json and ```
        if html_content.startswith('```json'):
            # The content is all on one line, so let's handle it differently
            # Remove the ```json prefix
            if html_content.startswith('```json '):
                json_content = html_content[8:]  # Remove '```json '
            elif html_content.startswith('```json'):
                json_content = html_content[7:]  # Remove '```json'
            
            # Look for closing ``` if it exists
            if json_content.endswith('```'):
                json_content = json_content[:-3]
            
            # The JSON content is now the remainder
            json_content = json_content.strip()
            
            # Try to fix common JSON issues
            # 1. Fix unescaped quotes in HTML attributes
            # This is a complex task, so let's use a different approach
            # Let's try to extract the key components manually
            
            # Extract title
            title_match = re.search(r'"title":\s*"([^"]*(?:\\.[^"]*)*)"', json_content)
            title = title_match.group(1) if title_match else f"Content about {job.topic}"
            
            # Extract summary 
            summary_match = re.search(r'"summary":\s*"([^"]*(?:\\.[^"]*)*)"', json_content)
            summary = summary_match.group(1) if summary_match else None
            
            # Extract tags
            tags_match = re.search(r'"tags":\s*\[(.*?)\]', json_content, re.DOTALL)
            tags = []
            if tags_match:
                tags_content = tags_match.group(1)
                # Extract individual tag strings
                tag_matches = re.findall(r'"([^"]*)"', tags_content)
                tags = tag_matches
            
            # For HTML content, we need a more sophisticated approach
            # Let's find the html_content field and extract until we find the next field
            html_start = json_content.find('"html_content":')
            if html_start == -1:
                print("Could not find html_content field")
                return False
            
            # Find the opening quote after the colon
            quote_start = json_content.find('"', html_start + len('"html_content":'))
            if quote_start == -1:
                print("Could not find opening quote for html_content")
                return False
            
            # Now we need to find the closing quote, but it's tricky due to nested quotes
            # Let's look for the pattern: " , "markdown_content" or similar
            content_start = quote_start + 1
            
            # Look for the end pattern
            end_patterns = ['" , "markdown_content"', '" ,"markdown_content"', '", "markdown_content"']
            html_end = -1
            for pattern in end_patterns:
                pos = json_content.find(pattern, content_start)
                if pos != -1:
                    html_end = pos
                    break
            
            if html_end == -1:
                print("Could not find end of html_content field")
                return False
            
            # Extract the raw HTML content
            html_content_raw = json_content[content_start:html_end]
            
            # The HTML is likely to have unescaped quotes, so let's try to clean it
            # Remove obvious JSON escaping artifacts
            actual_html = html_content_raw.replace('\\"', '"').replace('\\n', '\n').replace('\\/', '/')
            
            print(f"Extracted HTML content length: {len(actual_html)}")
            print(f"HTML starts with: {actual_html[:100]}...")
            
            if not actual_html.strip():
                print("Extracted HTML content is empty")
                return False
            
            # Create clean content object
            clean_content = {
                "title": title,
                "html_content": actual_html,
                "summary": summary,
                "tags": tags,
                "images": content_obj.get('images', [])  # Keep original images
            }
            
            # Update the job content
            job.content = json.dumps(clean_content, ensure_ascii=False, indent=2)
            db.save_generation_job(job)
            
            print("Successfully repaired malformed JSON content")
            print(f"Title: {title}")
            print(f"Summary: {summary}")
            print(f"Tags: {tags}")
            print(f"HTML content length: {len(actual_html)}")
            return True
            
    except Exception as e:
        print(f"Failed to repair content: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    job_id = "5e47d449-b613-48eb-90ec-bc6f685b3675"
    success = repair_malformed_json_content(job_id)
    
    if success:
        print(f"\nSuccess: Job {job_id} content has been repaired!")
        print("You should now see properly formatted content in the frontend.")
    else:
        print(f"\nFailed to repair job {job_id}")