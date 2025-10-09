#!/usr/bin/env python3

import sys
import os
sys.path.append(os.getcwd())

from fastapi import FastAPI, HTTPException
import uvicorn

app = FastAPI()

@app.get("/debug/test-contentgen/{job_id}")
async def test_contentgen(job_id: str):
    try:
        from packages.gen.content_generator import ContentGenerator
        
        print(f"DEBUG: Imported ContentGenerator")
        gen = ContentGenerator()
        print(f"DEBUG: Created ContentGenerator instance: {gen}")
        print(f"DEBUG: Methods: {[m for m in dir(gen) if not m.startswith('_')]}")
        
        if hasattr(gen, 'safe_print_str'):
            print("DEBUG: safe_print_str method exists")
        else:
            print("DEBUG: safe_print_str method does NOT exist")
            
        result = gen.get_job_result(job_id)
        print(f"DEBUG: Got result: {result.job_id}")
        
        return {"success": True, "job_id": result.job_id, "status": result.status.value}
        
    except Exception as e:
        import traceback
        print(f"DEBUG ERROR: {e}")
        print(f"DEBUG TRACEBACK: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3001)