#!/usr/bin/env python3
"""
Debug job statuses in the database
"""

from database import DatabaseManager

def debug_jobs_status():
    """Debug all jobs and their statuses"""
    
    db = DatabaseManager()
    jobs = db.get_generation_jobs()
    
    print("=== ALL JOBS STATUS DEBUG ===")
    print(f"Total jobs found: {len(jobs)}")
    print()
    
    status_counts = {}
    
    for job in jobs:
        status = job.status
        if status not in status_counts:
            status_counts[status] = 0
        status_counts[status] += 1
        
        print(f"Job ID: {job.job_id}")
        print(f"Provider: {job.provider}")
        print(f"Status: {job.status}")
        print(f"Topic: {repr(job.topic)}")
        print(f"Created: {job.created_at}")
        print(f"Updated: {job.updated_at}")
        print(f"Progress: {job.progress}")
        print(f"Has content: {'Yes' if job.content else 'No'}")
        if job.content:
            print(f"Content length: {len(job.content)}")
        if job.error_message:
            print(f"Error: {job.error_message}")
        print("-" * 50)
    
    print("\n=== STATUS SUMMARY ===")
    for status, count in status_counts.items():
        print(f"{status}: {count} jobs")
    
    # Check for stuck jobs
    print("\n=== CHECKING FOR STUCK JOBS ===")
    from datetime import datetime, timedelta
    now = datetime.now()
    
    for job in jobs:
        if job.status in ['pending', 'in_progress']:
            try:
                created = datetime.fromisoformat(job.created_at.replace('Z', '+00:00').replace('+00:00', ''))
                age = now - created
                if age > timedelta(minutes=10):
                    print(f"STUCK JOB: {job.job_id} - {job.status} for {age}")
            except Exception as e:
                print(f"Could not parse date for job {job.job_id}: {e}")

if __name__ == "__main__":
    debug_jobs_status()