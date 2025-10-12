#!/usr/bin/env python3
"""
Compare two jobs to see encoding differences
"""

import json
from database import DatabaseManager

def compare_jobs():
    """Compare the two jobs with same topic"""
    
    job_id_1 = '8a3c9fb7-ee33-4b66-ac04-e94600a1b166'  # 첫 번째 (인코딩 문제)
    job_id_2 = 'c885aa61-dbfd-4d85-bde7-0869236d0274'  # 두 번째 (인코딩 정상)
    
    db = DatabaseManager()
    
    job1 = db.get_generation_job(job_id_1)
    job2 = db.get_generation_job(job_id_2)
    
    if not job1 or not job2:
        print("One or both jobs not found!")
        return
    
    print("=== JOB COMPARISON ===")
    print(f"Job 1 ID: {job1.job_id}")
    print(f"Job 1 Topic: {repr(job1.topic)}")
    print(f"Job 1 Created: {job1.created_at}")
    print(f"Job 1 Updated: {job1.updated_at}")
    print()
    
    print(f"Job 2 ID: {job2.job_id}")
    print(f"Job 2 Topic: {repr(job2.topic)}")
    print(f"Job 2 Created: {job2.created_at}")
    print(f"Job 2 Updated: {job2.updated_at}")
    print()
    
    # Compare content
    if job1.content and job2.content:
        try:
            content1 = json.loads(job1.content)
            content2 = json.loads(job2.content)
            
            title1 = content1.get('title', '')
            title2 = content2.get('title', '')
            
            html1 = content1.get('html_content', '')
            html2 = content2.get('html_content', '')
            
            print("=== TITLE COMPARISON ===")
            print(f"Job 1 title: {repr(title1)}")
            print(f"Job 2 title: {repr(title2)}")
            print()
            
            # Count Korean characters
            korean1 = sum(1 for c in title1 if '\uAC00' <= c <= '\uD7AF')
            korean2 = sum(1 for c in title2 if '\uAC00' <= c <= '\uD7AF')
            
            print(f"Korean chars in Job 1 title: {korean1}")
            print(f"Korean chars in Job 2 title: {korean2}")
            print()
            
            # Check HTML content for Korean
            korean_html1 = sum(1 for c in html1 if '\uAC00' <= c <= '\uD7AF')
            korean_html2 = sum(1 for c in html2 if '\uAC00' <= c <= '\uD7AF')
            
            print(f"Korean chars in Job 1 HTML: {korean_html1}")
            print(f"Korean chars in Job 2 HTML: {korean_html2}")
            print()
            
            # Save content samples for analysis
            with open('job1_content_sample.txt', 'w', encoding='utf-8') as f:
                f.write(f"Title: {title1}\n\n")
                f.write(f"HTML (first 1000 chars): {html1[:1000]}")
            
            with open('job2_content_sample.txt', 'w', encoding='utf-8') as f:
                f.write(f"Title: {title2}\n\n")
                f.write(f"HTML (first 1000 chars): {html2[:1000]}")
            
            print("Content samples saved to job1_content_sample.txt and job2_content_sample.txt")
            
            # Check if Job 1 needs fixing
            if korean1 < korean2 or korean_html1 < korean_html2:
                print(f"\n*** Job 1 appears to have encoding issues ***")
                print(f"Job 1 has significantly fewer Korean characters")
                
                # Let's see if we can identify the pattern
                if 'Content about' in title1:
                    print("Job 1 has fallback title, indicating processing issues")
                
                # Check for spaces that might be from removed Korean characters
                spaces1 = title1.count('  ')  # Double spaces
                spaces2 = title2.count('  ')
                print(f"Double spaces in Job 1: {spaces1}")
                print(f"Double spaces in Job 2: {spaces2}")
                
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
    else:
        print("One or both jobs have no content")

if __name__ == "__main__":
    compare_jobs()