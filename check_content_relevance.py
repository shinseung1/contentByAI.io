#!/usr/bin/env python3
"""Check if content matches the requested topic."""

import sys
import os
import json
import re
sys.path.insert(0, os.path.abspath('.'))

from database import DatabaseManager

def check_content_relevance(job_id):
    """Check if content matches the topic."""
    
    db = DatabaseManager()
    job = db.get_generation_job(job_id)
    
    if not job or not job.content:
        print(f"Job {job_id} not found or has no content")
        return False
    
    try:
        content_obj = json.loads(job.content)
        html_content = content_obj.get('html_content', '')
        title = content_obj.get('title', '')
        
        # Topic should be about comparing stock vs bond vs gold
        topic = job.topic
        print(f"Requested topic: {topic}")
        print(f"Content title: {title}")
        
        # Remove HTML tags for analysis
        plain_text = re.sub(r'<[^>]*>', '', html_content)
        plain_text_lower = plain_text.lower()
        
        # Keywords to check for
        stock_keywords = ['주식', '증권', '기업주식', '주가', '배당']
        bond_keywords = ['채권', '국채', '회사채', '이자', '원금보장']  
        gold_keywords = ['금', '골드', '귀금속', '금값', '금 투자']
        comparison_keywords = ['vs', '비교', '차이', '대비', '장단점', '선택']
        
        # Check presence of each category
        stock_found = any(keyword in plain_text for keyword in stock_keywords)
        bond_found = any(keyword in plain_text for keyword in bond_keywords)
        gold_found = any(keyword in plain_text for keyword in gold_keywords)
        comparison_found = any(keyword in plain_text for keyword in comparison_keywords)
        
        print(f"\\nKeyword analysis:")
        print(f"Stock keywords found: {stock_found}")
        print(f"Bond keywords found: {bond_found}")
        print(f"Gold keywords found: {gold_found}")
        print(f"Comparison keywords found: {comparison_found}")
        
        # Show some content sample
        print(f"\\nContent sample (first 300 chars):")
        content_sample = plain_text[:300].replace('\\n', ' ')
        print(content_sample)
        
        # Determine if content is relevant
        if stock_found and bond_found and gold_found and comparison_found:
            print(f"\\nCONTENT ANALYSIS: RELEVANT - Contains all three investment types and comparison")
            return True
        elif (stock_found or bond_found or gold_found) and comparison_found:
            print(f"\\nCONTENT ANALYSIS: PARTIALLY RELEVANT - Contains some investment types and comparison")
            return True
        else:
            print(f"\\nCONTENT ANALYSIS: NOT RELEVANT - Missing key topics or comparison")
            return False
            
    except Exception as e:
        print(f"Error analyzing content: {e}")
        return False

if __name__ == "__main__":
    job_id = "978a1acd-5b87-4d47-9bc7-7bc9d47d5ae5"
    check_content_relevance(job_id)