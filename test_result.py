#!/usr/bin/env python3
"""Test result retrieval."""

import requests
import json

def test_result():
    job_id = "acbcce7f-6757-41a2-b3cc-e21ae7f76b05"
    url = f"http://127.0.0.1:3001/api/v1/generation/jobs/{job_id}"
    
    print("Getting job result...")
    response = requests.get(url)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Job status: {result.get('status')}")
    
    if result.get('content'):
        content = result['content']
        print(f"Title: {content.get('title', 'No title')}")
        print(f"Content length: {len(content.get('content', ''))}")
        print(f"Markdown length: {len(content.get('markdown_content', ''))}")
        print(f"Images count: {len(content.get('images', []))}")
        print(f"Summary: {content.get('summary', 'No summary')}")
        print(f"Tags: {content.get('tags', [])}")

if __name__ == "__main__":
    test_result()