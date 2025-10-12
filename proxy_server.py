"""Simple proxy server to forward port 3000 to 3005."""

import asyncio
import aiohttp
from aiohttp import web
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TARGET_URL = "http://127.0.0.1:3005"

async def proxy_handler(request):
    """Forward requests to target server."""
    try:
        # Build the target URL
        target_url = f"{TARGET_URL}{request.path_qs}"
        
        # Copy headers, excluding hop-by-hop headers
        headers = {}
        for name, value in request.headers.items():
            if name.lower() not in ['host', 'connection', 'upgrade']:
                headers[name] = value
        
        # Add CORS headers to response
        async def make_request():
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=request.method,
                    url=target_url,
                    headers=headers,
                    data=await request.read() if request.can_read_body else None
                ) as resp:
                    # Copy response headers
                    response_headers = {}
                    for name, value in resp.headers.items():
                        if name.lower() not in ['content-encoding', 'transfer-encoding']:
                            response_headers[name] = value
                    
                    # Add CORS headers
                    response_headers['Access-Control-Allow-Origin'] = '*'
                    response_headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
                    response_headers['Access-Control-Allow-Headers'] = '*'
                    response_headers['Access-Control-Allow-Credentials'] = 'true'
                    
                    # Create response
                    response = web.Response(
                        body=await resp.read(),
                        status=resp.status,
                        headers=response_headers
                    )
                    return response
        
        return await make_request()
        
    except Exception as e:
        logger.error(f"Proxy error: {e}")
        return web.Response(
            text=f"Proxy error: {str(e)}",
            status=500,
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Credentials': 'true'
            }
        )

async def options_handler(request):
    """Handle CORS preflight requests."""
    return web.Response(
        text="OK",
        headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Max-Age': '3600'
        }
    )

def create_app():
    """Create the proxy application."""
    app = web.Application()
    
    # Handle OPTIONS requests for CORS
    app.router.add_route('OPTIONS', '/{path:.*}', options_handler)
    
    # Handle all other requests
    app.router.add_route('*', '/{path:.*}', proxy_handler)
    
    return app

if __name__ == '__main__':
    app = create_app()
    logger.info("Starting proxy server on port 3000, forwarding to port 3005")
    web.run_app(app, host='0.0.0.0', port=3000)