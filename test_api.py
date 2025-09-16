#!/usr/bin/env python3

import requests
import json

def test_api():
    try:
        print("Testing generation jobs API...")
        response = requests.get("http://localhost:3000/api/v1/generation/jobs")
        print(f"Status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Response text: {response.text}")
        if response.status_code == 200:
            print(f"JSON response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_api()