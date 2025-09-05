#!/usr/bin/env python3
"""Extract content to file for analysis."""

import json
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def extract_content():
    from database import DatabaseManager
    
    db = DatabaseManager()
    job = db.get_generation_job('aa5d023b-d159-4efc-be02-3104e5964dea')
    
    if not job:
        with open('extraction_result.txt', 'w', encoding='utf-8') as f:
            f.write("Job not found")
        return
    
    try:
        content_data = json.loads(job.content)
        html_content = content_data.get('html_content', '')
        
        # Save HTML content
        with open('generated_content.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Save analysis to file
        with open('content_analysis.txt', 'w', encoding='utf-8') as f:
            f.write("=== GENERATED CONTENT ANALYSIS ===\n")
            f.write(f"Title: {content_data.get('title', 'No title')}\n")
            f.write(f"Summary exists: {bool(content_data.get('summary'))}\n")
            f.write(f"Tags count: {len(content_data.get('tags', []))}\n")
            f.write(f"Images count: {len(content_data.get('images', []))}\n")
            f.write(f"Content length: {len(html_content)} characters\n")
            
            # Count structure elements
            import re
            h1_count = len(re.findall(r'<h1[^>]*>', html_content, re.IGNORECASE))
            h2_count = len(re.findall(r'<h2[^>]*>', html_content, re.IGNORECASE))
            h3_count = len(re.findall(r'<h3[^>]*>', html_content, re.IGNORECASE))
            table_count = len(re.findall(r'<table[^>]*>', html_content, re.IGNORECASE))
            
            f.write("\n=== STRUCTURE ANALYSIS ===\n")
            f.write(f"H1 headings: {h1_count}\n")
            f.write(f"H2 headings: {h2_count}\n")
            f.write(f"H3 headings: {h3_count}\n")
            f.write(f"Tables: {table_count}\n")
            
            # Extract headings
            h2_headings = re.findall(r'<h2[^>]*>(.*?)</h2>', html_content, re.IGNORECASE | re.DOTALL)
            if h2_headings:
                f.write("\n=== H2 HEADINGS ===\n")
                for i, heading in enumerate(h2_headings, 1):
                    clean_heading = re.sub(r'<[^>]+>', '', heading).strip()
                    f.write(f"{i}. {clean_heading}\n")
                    
        print("Content extracted to generated_content.html")
        print("Analysis saved to content_analysis.txt")
        
    except Exception as e:
        with open('extraction_error.txt', 'w', encoding='utf-8') as f:
            f.write(f"Error: {e}\n")
            import traceback
            f.write(traceback.format_exc())
        print("Error occurred - check extraction_error.txt")

if __name__ == "__main__":
    extract_content()