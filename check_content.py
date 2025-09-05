#!/usr/bin/env python3
"""Check generated content structure."""

import json
import re
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_content():
    from database import DatabaseManager
    
    db = DatabaseManager()
    job = db.get_generation_job('aa5d023b-d159-4efc-be02-3104e5964dea')
    
    if not job:
        print("Job not found")
        return
    
    try:
        content_data = json.loads(job.content)
        html_content = content_data.get('html_content', '')
        
        print("=== GENERATED CONTENT ANALYSIS ===")
        print(f"Title: {content_data.get('title', 'No title')}")
        print(f"Summary exists: {bool(content_data.get('summary'))}")
        print(f"Tags count: {len(content_data.get('tags', []))}")
        print(f"Images count: {len(content_data.get('images', []))}")
        print(f"Content length: {len(html_content)} characters")
        
        # Save HTML content
        with open('generated_content.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("HTML content saved to generated_content.html")
        
        # Analyze structure
        h1_count = len(re.findall(r'<h1[^>]*>', html_content, re.IGNORECASE))
        h2_count = len(re.findall(r'<h2[^>]*>', html_content, re.IGNORECASE))  
        h3_count = len(re.findall(r'<h3[^>]*>', html_content, re.IGNORECASE))
        table_count = len(re.findall(r'<table[^>]*>', html_content, re.IGNORECASE))
        
        print("=== STRUCTURE ANALYSIS ===")
        print(f"H1 headings: {h1_count}")
        print(f"H2 headings: {h2_count}")
        print(f"H3 headings: {h3_count}")
        print(f"Tables: {table_count}")
        
        # Extract headings text
        h2_headings = re.findall(r'<h2[^>]*>(.*?)</h2>', html_content, re.IGNORECASE | re.DOTALL)
        if h2_headings:
            print("=== H2 HEADINGS ===")
            for i, heading in enumerate(h2_headings[:10], 1):  # Show first 10
                clean_heading = re.sub(r'<[^>]+>', '', heading).strip()
                print(f"{i}. {clean_heading}")
        
        # Check for template patterns
        template_patterns = [
            r'완전.*가이드',
            r'전체.*통합본', 
            r'## \d+\.',
            r'스카이패스',
            r'대한항공'
        ]
        
        print("=== TEMPLATE PATTERN CHECK ===")
        for pattern in template_patterns:
            matches = len(re.findall(pattern, html_content, re.IGNORECASE))
            print(f"{pattern}: {matches} matches")
            
    except Exception as e:
        print(f"Error analyzing content: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_content()