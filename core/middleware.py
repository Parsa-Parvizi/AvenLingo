import time
import logging
import re
from django.db import connection
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponseRedirect

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

class URLSecurityMiddleware(MiddlewareMixin):
    """Middleware for URL security and validation"""
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.config = getattr(settings, 'URL_SECURITY', {})
        self.enable_https_redirect = self.config.get('ENABLE_HTTPS_REDIRECT', False)
        self.enable_hsts = self.config.get('ENABLE_HSTS', False)
        self.hsts_seconds = self.config.get('HSTS_SECONDS', 31536000)
        self.enable_csp = self.config.get('ENABLE_CONTENT_SECURITY_POLICY', False)
        self.skip_security_in_debug = self.config.get('SKIP_SECURITY_IN_DEBUG', True)
        self.allow_localhost_in_debug = self.config.get('ALLOW_LOCALHOST_IN_DEBUG', True)
        self.debug_logging = self.config.get('DEBUG_LOGGING', True)
    
    def process_request(self, request):
        """Process incoming request for security checks"""
        # Skip security checks in development mode if configured
        if getattr(settings, 'DEBUG', False) and self.skip_security_in_debug:
            if self.debug_logging:
                logger.debug(f'Development mode: Skipping security checks for {request.path}')
            return None
        
        # Check for suspicious URL patterns
        if self._is_suspicious_request(request):
            logger.warning(f'Suspicious request detected: {request.path}')
            return HttpResponseForbidden('Suspicious request detected')
        
        # Check for blocked domains in referer
        if self._is_blocked_referer(request):
            logger.warning(f'Request from blocked referer: {request.META.get("HTTP_REFERER", "")}')
            return HttpResponseForbidden('Request from blocked domain')
        
        return None
    
    def process_response(self, request, response):
        """Process outgoing response for security headers"""
        # Add HTTPS redirect header if enabled
        if self.enable_https_redirect and not request.is_secure():
            response['Location'] = request.build_absolute_uri().replace('http://', 'https://')
            response.status_code = 301
            return response
        
        # Add HSTS header if enabled
        if self.enable_hsts and request.is_secure():
            response['Strict-Transport-Security'] = f'max-age={self.hsts_seconds}; includeSubDomains'
        
        # Add Content Security Policy if enabled
        if self.enable_csp:
            csp_policy = self._build_csp_policy()
            response['Content-Security-Policy'] = csp_policy
        
        # Add other security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'SAMEORIGIN'
        response['X-XSS-Protection'] = '1; mode=block'
        
        return response
    
    def _is_suspicious_request(self, request):
        """Check if request contains suspicious patterns"""
        suspicious_patterns = [
            r'\.\./',  # Directory traversal
            r'<script',  # Script injection
            r'javascript:',  # JavaScript protocol
            r'data:',  # Data URI
            r'vbscript:',  # VBScript protocol
            r'file:',  # File protocol
            r'ftp:',  # FTP protocol
            r'\\',  # Windows path separator
        ]
        
        path = request.path.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, path, re.IGNORECASE):
                return True
        
        return False
    
    def _is_blocked_referer(self, request):
        """Check if request comes from blocked domain"""
        referer = request.META.get('HTTP_REFERER', '')
        if not referer:
            return False
        
        # Allow localhost in development mode
        if getattr(settings, 'DEBUG', False) and self.allow_localhost_in_debug:
            if 'localhost' in referer or '127.0.0.1' in referer:
                return False
        
        blocked_domains = getattr(settings, 'URL_VALIDATION', {}).get('BLOCKED_DOMAINS', [])
        for domain in blocked_domains:
            if domain in referer:
                return True
        
        return False
    
    def _build_csp_policy(self):
        """Build Content Security Policy header"""
        csp_config = getattr(settings, 'URL_SECURITY', {})
        
        policies = []
        
        # Default source
        if 'CSP_DEFAULT_SRC' in csp_config:
            policies.append(f"default-src {' '.join(csp_config['CSP_DEFAULT_SRC'])}")
        
        # Script source
        if 'CSP_SCRIPT_SRC' in csp_config:
            policies.append(f"script-src {' '.join(csp_config['CSP_SCRIPT_SRC'])}")
        
        # Style source
        if 'CSP_STYLE_SRC' in csp_config:
            policies.append(f"style-src {' '.join(csp_config['CSP_STYLE_SRC'])}")
        
        # Font source
        if 'CSP_FONT_SRC' in csp_config:
            policies.append(f"font-src {' '.join(csp_config['CSP_FONT_SRC'])}")
        
        # Image source
        if 'CSP_IMG_SRC' in csp_config:
            policies.append(f"img-src {' '.join(csp_config['CSP_IMG_SRC'])}")
        
        return '; '.join(policies)

class URLValidationMiddleware(MiddlewareMixin):
    """Middleware for validating external URLs in requests"""
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.config = getattr(settings, 'URL_VALIDATION', {})
        self.enable_validation = self.config.get('ENABLE_EXTERNAL_URL_VALIDATION', True)
        self.skip_validation_in_debug = self.config.get('SKIP_VALIDATION_IN_DEBUG', True)
        self.allow_localhost_in_debug = self.config.get('ALLOW_LOCALHOST_IN_DEBUG', True)
        self.debug_logging = self.config.get('DEBUG_LOGGING', True)
    
    def process_request(self, request):
        """Validate URLs in request parameters"""
        if not self.enable_validation:
            return None
        
        # Skip strict validation in development mode if configured
        if getattr(settings, 'DEBUG', False) and self.skip_validation_in_debug:
            if self.debug_logging:
                logger.debug(f'Development mode: Skipping URL validation for {request.path}')
            return None
        
        # Check GET parameters
        for key, value in request.GET.items():
            if self._is_url_parameter(key) and value:
                if not self._validate_url(value):
                    logger.warning(f'Invalid URL in GET parameter {key}: {value}')
                    return HttpResponseForbidden('Invalid URL parameter')
        
        # Check POST parameters
        if request.method == 'POST':
            for key, value in request.POST.items():
                if self._is_url_parameter(key) and value:
                    if not self._validate_url(value):
                        logger.warning(f'Invalid URL in POST parameter {key}: {value}')
                        return HttpResponseForbidden('Invalid URL parameter')
        
        return None
    
    def _is_url_parameter(self, key):
        """Check if parameter key suggests URL content"""
        url_indicators = ['url', 'link', 'href', 'src', 'redirect', 'callback']
        return any(indicator in key.lower() for indicator in url_indicators)
    
    def _validate_url(self, url):
        """Validate a single URL"""
        if not url:
            return True
        
        # Sanitize URL first
        sanitized_url = sanitize_url(url)
        if not sanitized_url:
            return False
        
        # Use URL validator
        result = url_validator.validate_url(sanitized_url)
        return result['valid']

class BrokenURLMiddleware(MiddlewareMixin):
    """Middleware for handling broken URLs and redirects"""
    
    def process_response(self, request, response):
        """Handle 404 responses and broken URLs"""
        if response.status_code == 404:
            # Log broken URL
            logger.warning(f'Broken URL accessed: {request.path}')
            
            # Check if this is a known URL pattern that might have changed
            suggested_url = self._suggest_alternative_url(request.path)
            if suggested_url:
                # Redirect to suggested URL
                return HttpResponseRedirect(suggested_url)
        
        return response
    
    def _suggest_alternative_url(self, path):
        """Suggest alternative URL for broken paths"""
        # Common URL pattern changes
        url_mappings = {
            'course/': 'courses/',
            'teacher/': 'teachers/',
            'aboutus/': 'contact/about-us/',
            'contactus/': 'contact/contact-us/',
            'allteacher': 'teachers/all-teachers/',
            'allcourse': 'courses/',
            'student_enrollments': 'enrollment/my-enrollments/',
            'enrollment_detail': 'enrollment/enrollment-detail/',
            'course_enroll': 'enrollment/enroll/',
            'cancel_enrollment': 'enrollment/cancel-enrollment/',
            'enrollment_certificate': 'enrollment/certificate/',
            'available_courses': 'enrollment/available-courses/',
        }
        
        # Check for exact matches first
        if path in url_mappings:
            return url_mappings[path]
        
        # Check for partial matches
        for old_pattern, new_pattern in url_mappings.items():
            if old_pattern in path:
                return path.replace(old_pattern, new_pattern)
        
        return None 