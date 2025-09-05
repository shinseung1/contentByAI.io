#!/usr/bin/env python3
"""Test improved template generation."""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_improved_template():
    """Test generation with improved template-based prompt."""
    from packages.gen.content_generator import ContentGenerator
    from packages.gen.models import GenerationRequest
    
    print("Testing improved template generation...")
    
    generator = ContentGenerator()
    
    request = GenerationRequest(
        topic="대한항공 스카이패스 마일리지 적립과 사용방법",
        provider="openai",
        tone="professional", 
        word_count=2000,  # Increased for better template match
        include_images=True,
        target_language="ko"
    )
    
    job_id = generator.create_job_id()
    print(f"Created job ID: {job_id}")
    
    try:
        print("Starting content generation with improved prompt...")
        await generator.generate_content_async(job_id, request)
        
        print("Content generation completed, analyzing result...")
        
        # Get the result
        response = generator.get_job_result(job_id)
        print(f"Status: {response.status}")
        
        if response.status.value == 'completed':
            print("✅ Generation successful!")
            print(f"Title: {response.content.title if response.content else 'No title'}")
            print(f"Content length: {len(response.content.content) if response.content else 0}")
            print(f"Images: {len(response.content.images) if response.content else 0}")
            
            return job_id
        else:
            print(f"❌ Generation failed: {response.error}")
            return None
            
    except Exception as e:
        print(f"Exception during generation: {e}")
        import traceback
        traceback.print_exc()
        return None

async def analyze_improved_content(job_id):
    """Analyze the improved content."""
    if not job_id:
        return
    
    print("\n=== ANALYZING IMPROVED CONTENT ===")
    
    # Extract and analyze content
    extract_script = f"""
import json
import re
from database import DatabaseManager

db = DatabaseManager()
job = db.get_generation_job('{job_id}')

if job:
    try:
        content_data = json.loads(job.content)
        html_content = content_data.get('html_content', '')
        
        # Save improved content
        with open('improved_content.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Analyze structure
        h1_count = len(re.findall(r'<h1[^>]*>', html_content, re.IGNORECASE))
        h2_count = len(re.findall(r'<h2[^>]*>', html_content, re.IGNORECASE))
        h3_count = len(re.findall(r'<h3[^>]*>', html_content, re.IGNORECASE))
        table_count = len(re.findall(r'<table[^>]*>', html_content, re.IGNORECASE))
        img_count = len(re.findall(r'<img[^>]*>', html_content, re.IGNORECASE))
        hr_count = len(re.findall(r'<hr[^>]*>', html_content, re.IGNORECASE))
        
        # Check for Em dash in title
        em_dash_present = '—' in html_content
        
        with open('improved_analysis.txt', 'w', encoding='utf-8') as f:
            f.write("=== IMPROVED TEMPLATE ANALYSIS ===\\n")
            f.write(f"Title: {{content_data.get('title', 'No title')}}\\n")
            f.write(f"Content length: {{len(html_content)}} characters\\n")
            f.write(f"Word count (approx): {{len(html_content.split())}} words\\n")
            f.write(f"Summary exists: {{bool(content_data.get('summary'))}}\\n")
            f.write(f"Tags count: {{len(content_data.get('tags', []))}}\\n")
            f.write(f"Images count (JSON): {{len(content_data.get('images', []))}}\\n")
            
            f.write("\\n=== STRUCTURE ANALYSIS ===\\n")
            f.write(f"H1 headings: {{h1_count}}\\n")
            f.write(f"H2 headings: {{h2_count}}\\n") 
            f.write(f"H3 headings: {{h3_count}}\\n")
            f.write(f"Tables: {{table_count}}\\n")
            f.write(f"Images in HTML: {{img_count}}\\n")
            f.write(f"Horizontal rules: {{hr_count}}\\n")
            f.write(f"Em dash in title: {{em_dash_present}}\\n")
            
            # Extract H2 headings
            h2_headings = re.findall(r'<h2[^>]*>(.*?)</h2>', html_content, re.IGNORECASE | re.DOTALL)
            if h2_headings:
                f.write("\\n=== H2 SECTION STRUCTURE ===\\n")
                for i, heading in enumerate(h2_headings, 1):
                    clean_heading = re.sub(r'<[^>]+>', '', heading).strip()
                    f.write(f"{{i}}. {{clean_heading}}\\n")
                    
            # Template compliance check
            f.write("\\n=== TEMPLATE COMPLIANCE ===\\n")
            template_checks = [
                ('Em dash in title', em_dash_present),
                ('Multiple sections (8+)', h2_count >= 8),
                ('Tables present', table_count >= 1),
                ('Images in HTML', img_count > 0),
                ('Horizontal rules', hr_count > 0),
                ('Long content (1500+ chars)', len(html_content) > 1500)
            ]
            
            for check_name, passed in template_checks:
                status = "✅ PASS" if passed else "❌ FAIL"
                f.write(f"{{check_name}}: {{status}}\\n")
        
        print("Improved content saved to improved_content.html")
        print("Analysis saved to improved_analysis.txt")
        
    except Exception as e:
        with open('improved_error.txt', 'w', encoding='utf-8') as f:
            f.write(f"Analysis Error: {{e}}\\n")
            import traceback
            f.write(traceback.format_exc())
        print("Error occurred - check improved_error.txt")
else:
    print("Job not found in database")
"""
    
    with open('analyze_improved.py', 'w', encoding='utf-8') as f:
        f.write(extract_script)
    
    # Run analysis
    os.system('python analyze_improved.py')

if __name__ == "__main__":
    job_id = asyncio.run(test_improved_template())
    if job_id:
        asyncio.run(analyze_improved_content(job_id))
        print(f"\n🎯 Improved test completed! Job ID: {job_id}")
        print("📄 Check improved_content.html for generated content")  
        print("📊 Check improved_analysis.txt for detailed analysis")
    else:
        print("\n❌ Improved test failed!")