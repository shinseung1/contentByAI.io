#!/usr/bin/env python3
"""Test direct API call."""

import requests
import json
import time

def test_direct():
    url = "http://127.0.0.1:3001/api/v1/generation/generate"
    data = {
        "topic": "ChatGPT 활용법 완전 정복: 업무 효율성을 10배 높이는 프롬프트 작성법",
        "provider": "openai", 
        "tone": "professional",
        "word_count": 800,
        "include_images": True,
        "target_language": "ko"
    }
    
    print("Making direct API call...")
    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == "__main__":
    test_direct()