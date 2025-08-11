import time
import logging
from django.db import connection
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class QueryCountMiddleware(MiddlewareMixin):
    """
    Simple middleware to count database queries and response time
    """
    
    def process_request(self, request):
        request.start_time = time.time()
        request.db_queries_start = len(connection.queries)
        
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            db_queries = len(connection.queries) - getattr(request, 'db_queries_start', 0)
            
            # Log performance metrics
            if duration > 1.0:  # Log slow requests
                logger.warning(
                    f"🐌 Slow: {request.path} took {duration:.2f}s with {db_queries} queries"
                )
            elif duration > 0.5:  # Log medium requests
                logger.info(
                    f"⚡ Medium: {request.path} took {duration:.2f}s with {db_queries} queries"
                )
            else:
                logger.debug(
                    f"🚀 Fast: {request.path} took {duration:.2f}s with {db_queries} queries"
                )
        
        return response 