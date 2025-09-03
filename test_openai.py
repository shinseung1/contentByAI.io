#!/usr/bin/env python3
"""Test OpenAI API directly."""

import asyncio
import os
from packages.ai_clients import AIClientFactory, AIProvider, AIRequest, AIMessage, AIClientConfig

async def test_openai():
    """Test OpenAI API directly."""
    
    # Load environment variables
    from packages.core.config import get_settings
    settings = get_settings()
    
    print(f"OpenAI API Key: {settings.OPENAI_API_KEY[:10]}..." if settings.OPENAI_API_KEY else "No OpenAI API Key")
    print(f"OpenAI Model: {settings.OPENAI_MODEL}")
    
    if not settings.OPENAI_API_KEY:
        print("ERROR: No OpenAI API key found")
        return
    
    try:
        # Create config
        config = AIClientConfig(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            max_tokens=1000,
            temperature=0.7
        )
        
        # Create client
        client = AIClientFactory.create_client(AIProvider.OPENAI, config)
        
        # Create test request
        request = AIRequest(
            messages=[
                AIMessage(role="system", content="You are a helpful assistant."),
                AIMessage(role="user", content="Write a short paragraph about AI in Korean.")
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        print("Testing OpenAI API...")
        
        async with client:
            response = await client.generate(request)
            
        print(f"Success! Response: {response.content[:100]}...")
        print(f"Model: {response.model}")
        print(f"Tokens used: {response.tokens_used}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_openai())