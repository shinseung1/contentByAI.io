#!/usr/bin/env python3
"""View generated content sample."""

import requests
import json

def view_content():
    job_id = "acbcce7f-6757-41a2-b3cc-e21ae7f76b05"
    url = f"http://127.0.0.1:3001/api/v1/generation/jobs/{job_id}"
    
    response = requests.get(url)
    result = response.json()
    
    if result.get('content'):
        content = result['content']
        
        print("=== GENERATED TITLE ===")
        print(content.get('title', 'No title'))
        print()
        
        print("=== HTML CONTENT (first 1000 chars) ===")
        html_content = content.get('content', '')
        print(html_content[:1000] + "..." if len(html_content) > 1000 else html_content)
        print()
        
        print("=== MARKDOWN CONTENT (first 800 chars) ===")
        md_content = content.get('markdown_content', '')
        print(md_content[:800] + "..." if len(md_content) > 800 else md_content)
        print()
        
        print("=== SUMMARY ===")
        print(content.get('summary', 'No summary'))
        print()
        
        print("=== TAGS ===")
        print(content.get('tags', []))

if __name__ == "__main__":
    view_content()