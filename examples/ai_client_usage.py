"""Example usage of AI clients."""

import asyncio
import os
from packages.ai_clients import (
    AIClientFactory,
    MultiAIClient,
    AIProvider,
    AIRequest,
    AIMessage,
    AIClientConfig
)


async def example_single_client():
    """Example using a single AI client."""
    
    # Create Claude client
    config = AIClientConfig(
        api_key=os.getenv("CLAUDE_API_KEY", "your-api-key"),
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        temperature=0.7
    )
    
    client = AIClientFactory.create_client(AIProvider.CLAUDE, config)
    
    # Create request
    request = AIRequest(
        messages=[
            AIMessage(role="system", content="You are a helpful assistant."),
            AIMessage(role="user", content="Write a short poem about AI.")
        ]
    )
    
    # Generate response
    async with client:
        response = await client.generate(request)
        print(f"Provider: {response.provider}")
        print(f"Model: {response.model}")
        print(f"Content: {response.content}")
        print(f"Tokens used: {response.tokens_used}")


async def example_multi_client():
    """Example using multiple AI clients with fallback."""
    
    # Create multiple clients
    clients = {}
    
    # Claude client
    if os.getenv("CLAUDE_API_KEY"):
        claude_config = AIClientConfig(
            api_key=os.getenv("CLAUDE_API_KEY"),
            model="claude-3-sonnet-20240229"
        )
        clients[AIProvider.CLAUDE] = AIClientFactory.create_client(
            AIProvider.CLAUDE, claude_config
        )
    
    # OpenAI client
    if os.getenv("OPENAI_API_KEY"):
        openai_config = AIClientConfig(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o"
        )
        clients[AIProvider.OPENAI] = AIClientFactory.create_client(
            AIProvider.OPENAI, openai_config
        )
    
    # Create multi-client
    multi_client = MultiAIClient(clients)
    multi_client.set_primary_provider(AIProvider.CLAUDE)
    
    # Create request
    request = AIRequest(
        messages=[
            AIMessage(role="user", content="Explain machine learning in simple terms.")
        ]
    )
    
    # Generate with fallback
    try:
        response = await multi_client.generate(request, fallback=True)
        print(f"Successfully got response from: {response.provider}")
        print(f"Content: {response.content[:200]}...")
    except Exception as e:
        print(f"All providers failed: {e}")


async def example_all_providers():
    """Example testing all AI providers."""
    
    providers_config = {
        AIProvider.CLAUDE: {
            "api_key": os.getenv("CLAUDE_API_KEY"),
            "model": "claude-3-sonnet-20240229"
        },
        AIProvider.OPENAI: {
            "api_key": os.getenv("OPENAI_API_KEY"),
            "model": "gpt-4o"
        },
        AIProvider.GEMINI: {
            "api_key": os.getenv("GEMINI_API_KEY"),
            "model": "gemini-1.5-pro"
        },
        AIProvider.GROK: {
            "api_key": os.getenv("GROK_API_KEY"),
            "model": "grok-beta"
        }
    }
    
    request = AIRequest(
        messages=[
            AIMessage(role="user", content="What is 2+2?")
        ],
        max_tokens=100
    )
    
    for provider, config_data in providers_config.items():
        if not config_data["api_key"]:
            print(f"Skipping {provider} - no API key")
            continue
            
        try:
            config = AIClientConfig(**config_data)
            client = AIClientFactory.create_client(provider, config)
            
            async with client:
                response = await client.generate(request)
                print(f"\n{provider.upper()}:")
                print(f"Model: {response.model}")
                print(f"Response: {response.content}")
                print(f"Tokens: {response.tokens_used}")
                
        except Exception as e:
            print(f"{provider} failed: {e}")


if __name__ == "__main__":
    print("=== Single Client Example ===")
    asyncio.run(example_single_client())
    
    print("\n=== Multi Client Example ===")
    asyncio.run(example_multi_client())
    
    print("\n=== All Providers Example ===")
    asyncio.run(example_all_providers())