#!/usr/bin/env python3
"""Test job 1629f78d API response."""

import sys
import os
import json
sys.path.insert(0, os.path.abspath('.'))

from database import DatabaseManager

def test_job_api_response():
    """Test if job API response includes proper tone and word_count."""
    
    job_id = "1629f78d-9532-4d05-b8df-029f2eef29a2"
    db = DatabaseManager()
    job = db.get_generation_job(job_id)
    
    if not job:
        print(f"Job {job_id} not found")
        return
    
    print(f"=== DATABASE JOB INFO ===")
    print(f"Job ID: {job.job_id}")
    print(f"Topic: {job.topic}")
    print(f"Status: {job.status}")
    print(f"Tone: {job.tone}")
    print(f"Word Count Target: {job.word_count}")
    print(f"Created At: {job.created_at}")
    
    if job.content:
        try:
            content_obj = json.loads(job.content)
            word_count_actual = content_obj.get('word_count_actual')
            html_content = content_obj.get('html_content', '')
            
            print(f"\n=== CONTENT INFO ===")
            print(f"word_count_actual: {word_count_actual}")
            print(f"HTML content length: {len(html_content)}")
            
            # Check military branch coverage
            army_count = html_content.count('육군')
            navy_count = html_content.count('해군')
            air_force_count = html_content.count('공군')
            
            print(f"\n=== CONTENT COVERAGE ===")
            print(f"육군 mentions: {army_count}")
            print(f"해군 mentions: {navy_count}")
            print(f"공군 mentions: {air_force_count}")
            
            if air_force_count >= 5:
                print("SUCCESS: 공군 content sufficiently covered")
            else:
                print("ISSUE: 공군 content still insufficient")
                
            print(f"\n=== API RESPONSE SIMULATION ===")
            print(f"tone: '{job.tone}'")
            print(f"word_count: {job.word_count}")
            print(f"created_at: '{job.created_at}'")
            print(f"actual_word_count: {word_count_actual}")
            
        except Exception as e:
            print(f"Error parsing content: {e}")

if __name__ == "__main__":
    test_job_api_response()