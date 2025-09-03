#!/usr/bin/env python3
"""Fresh test that completely bypasses database cache."""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def direct_generation_test():
    """Test content generation directly without any database interaction."""
    from packages.gen.content_generator import ContentGenerator
    from packages.gen.models import GenerationRequest
    
    print("Testing direct content generation...")
    
    generator = ContentGenerator()
    
    request = GenerationRequest(
        topic="test topic for direct generation",
        provider="openai",
        tone="professional", 
        word_count=300,
        include_images=False,  # Explicitly disable images
        target_language="ko"
    )
    
    try:
        # Call the AI generation directly
        ai_config = generator._get_ai_config(request.provider)
        if not ai_config:
            print("No AI configuration found")
            return
            
        provider, config = ai_config
        content = await generator._generate_with_ai(provider, config, request)
        
        print(f"Content generated successfully!")
        print(f"Title: {content.title}")
        print(f"Content length: {len(content.content)}")
        print(f"Images count: {len(content.images)}")
        print(f"Images type: {type(content.images)}")
        if content.images:
            print(f"First image type: {type(content.images[0])}")
        
        return True
        
    except Exception as e:
        print(f"Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(direct_generation_test())
    if success:
        print("✅ Direct generation test passed")
    else:
        print("❌ Direct generation test failed")