#!/usr/bin/env python3

import sys
import os
sys.path.append(os.getcwd())

try:
    from packages.gen.content_generator import ContentGenerator
    
    print("Imported ContentGenerator successfully")
    gen = ContentGenerator()
    print(f"Created ContentGenerator instance: {gen}")
    print(f"Methods available: {[m for m in dir(gen) if not m.startswith('_')]}")
    
    # Test if the safe_print_str method exists
    if hasattr(gen, 'safe_print_str'):
        print("safe_print_str method exists")
        result = gen.safe_print_str("test")
        print(f"safe_print_str('test') = {result}")
    else:
        print("safe_print_str method does NOT exist")
        
    # Try to call get_job_result with a fake job ID to see where the error occurs
    try:
        gen.get_job_result("fake-job-id")
    except Exception as e:
        print(f"Error calling get_job_result: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
except Exception as e:
    print(f"Error importing or testing: {e}")
    import traceback
    print(f"Traceback: {traceback.format_exc()}")