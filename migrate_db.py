#!/usr/bin/env python3
"""Database migration script to add new columns."""

import sqlite3
import os

DATABASE_PATH = "data/aiwriter.db"

def migrate_database():
    """Add new columns to existing database."""
    if not os.path.exists(DATABASE_PATH):
        print("Database not found, skipping migration")
        return
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        try:
            # Check if columns exist
            cursor = conn.execute("PRAGMA table_info(generation_jobs)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'html_content' not in columns:
                conn.execute("ALTER TABLE generation_jobs ADD COLUMN html_content TEXT")
                print("Added html_content column")
            
            if 'markdown_content' not in columns:
                conn.execute("ALTER TABLE generation_jobs ADD COLUMN markdown_content TEXT")
                print("Added markdown_content column")
            
            conn.commit()
            print("Database migration completed successfully")
            
        except Exception as e:
            print(f"Migration error: {e}")

if __name__ == "__main__":
    migrate_database()