#!/usr/bin/env python3
"""Debug database content."""

import sqlite3
import json

DATABASE_PATH = "data/aiwriter.db"

def debug_db():
    """Check what's in the database."""
    print("Checking database content...")
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.execute("""
            SELECT job_id, provider, status, content 
            FROM generation_jobs 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        
        for row in cursor.fetchall():
            job_id, provider, status, content = row
            print(f"\n=== Job {job_id} ===")
            print(f"Provider: {provider}")
            print(f"Status: {status}")
            print(f"Content type: {type(content)}")
            
            if content:
                try:
                    content_data = json.loads(content)
                    print(f"Content keys: {content_data.keys()}")
                    if 'images' in content_data:
                        images = content_data['images']
                        print(f"Images count: {len(images)}")
                        if images:
                            print(f"First image type: {type(images[0])}")
                            print(f"First image: {images[0]}")
                except json.JSONDecodeError:
                    print("Content is not valid JSON")
                except Exception as e:
                    print(f"Error parsing content: {e}")

if __name__ == "__main__":
    debug_db()