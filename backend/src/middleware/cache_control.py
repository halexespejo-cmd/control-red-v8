"""
Cache Control Middleware
Author: Héctor Alejandro Pérez (@halexespejo-cmd)
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)


class CacheControlMiddleware(BaseHTTPMiddleware):
    """
    Add Cache-Control headers for static assets
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        path = request.url.path
        
        # Static assets - cache for 1 year
        if any(path.endswith(ext) for ext in ['.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.woff', '.woff2', '.ttf', '.svg']):
            response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
            response.headers['Vary'] = 'Accept-Encoding'
        
        # HTML pages - no cache (always fresh)
        elif path.endswith('.html') or path in ['/', '/login', '/dashboard']:
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        
        # API responses - short cache
        elif path.startswith('/api/'):
            if request.method == 'GET':
                # GET methods cacheable por 30s
                response.headers['Cache-Control'] = 'public, max-age=30'
            else:
                # POST/PUT/DELETE no cacheable
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        
        return response
