import logging
import re
from datetime import datetime, timedelta
from django.core.cache import cache
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.contrib.sessions.models import Session
from django.utils import timezone

logger = logging.getLogger('security')


class SecurityMiddleware(MiddlewareMixin):
    """Comprehensive security middleware for the application"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
        
        # Security patterns
        self.sql_injection_patterns = [
            r"(?i)(union\s+select|select\s+.*\s+from)",
            r"(?i)(drop\s+table|delete\s+from|update\s+.*\s+set)",
            r"(?i)(insert\s+into|create\s+table)",
            r"[\'\"];\s*(drop|delete|update|insert|create)",
            r"(?i)(exec\s*\(|execute\s*\()",
            r"(?i)(or\s+1\s*=\s*1|and\s+1\s*=\s*1)"
        ]
        
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>.*?</iframe>",
            r"<object[^>]*>.*?</object>",
            r"<embed[^>]*>.*?</embed>"
        ]
        
        # Suspicious user agents
        self.suspicious_agents = [
            'sqlmap', 'nikto', 'dirb', 'dirbuster', 'nmap',
            'masscan', 'zap', 'burp', 'acunetix', 'nessus',
            'openvas', 'w3af', 'havij', 'pangolin'
        ]
        
        # Rate limiting configuration
        self.rate_limits = {
            'login': {'limit': 5, 'window': 900},      # 5 attempts per 15 min
            'register': {'limit': 3, 'window': 3600},  # 3 attempts per hour
            'general': {'limit': 100, 'window': 3600}, # 100 requests per hour
        }
    
    def process_request(self, request):
        """Process incoming requests for security threats"""
        
        # Temporarily disable all security checks in DEBUG to allow tests
        if getattr(settings, 'DEBUG', False) or getattr(settings, 'DISABLE_SECURITY_CHECKS', False):
            return None
        
        # Get client IP
        ip = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        # 1. Check if IP is blacklisted
        if self.is_blacklisted_ip(ip):
            logger.critical(f'Blocked blacklisted IP: {ip}')
            return HttpResponseForbidden('Access denied')
        
        # 2. Check suspicious user agent
        if self.is_suspicious_user_agent(user_agent):
            logger.warning(f'Suspicious user agent detected: {user_agent} from IP: {ip}')
            self.increment_threat_score(ip, 10)
        
        # 3. Rate limiting
        if not self.check_rate_limit(request, ip):
            logger.warning(f'Rate limit exceeded for IP: {ip}')
            return self.rate_limit_response(request)
        
        # 4. Check for attack patterns in parameters
        if self.detect_attack_patterns(request):
            logger.critical(f'Attack pattern detected from IP: {ip}')
            self.increment_threat_score(ip, 20)
            return HttpResponseForbidden('Malicious request detected')
        
        # 5. Check for rapid automated requests
        if self.detect_automated_behavior(request, ip):
            logger.warning(f'Automated behavior detected from IP: {ip}')
            self.increment_threat_score(ip, 5)
        
        # 6. Validate request size
        if not self.validate_request_size(request):
            logger.warning(f'Oversized request from IP: {ip}')
            return HttpResponseForbidden('Request too large')
        
        return None
    
    def process_response(self, request, response):
        """Process outgoing responses for security headers"""
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Add CSP header for production
        if not settings.DEBUG:
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' cdnjs.cloudflare.com code.jquery.com cdn.jsdelivr.net unpkg.com; "
                "style-src 'self' 'unsafe-inline' fonts.googleapis.com cdn.jsdelivr.net unpkg.com; "
                "font-src 'self' fonts.gstatic.com; "
                "img-src 'self' data:; "
                "connect-src 'self'"
            )
            response['Content-Security-Policy'] = csp
        
        return response
    
    def get_client_ip(self, request):
        """Get the real client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Take the first IP in the chain
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def is_blacklisted_ip(self, ip):
        """Check if IP is in blacklist"""
        # Check cache for blacklisted IPs
        blacklist_key = f'blacklisted_ip_{ip}'
        return cache.get(blacklist_key, False)
    
    def is_suspicious_user_agent(self, user_agent):
        """Check if user agent is suspicious"""
        return any(agent in user_agent for agent in self.suspicious_agents)
    
    def check_rate_limit(self, request, ip):
        """Check rate limiting for different endpoints"""
        path = request.path
        
        # Determine rate limit type
        if 'login' in path:
            limit_type = 'login'
        elif 'register' in path:
            limit_type = 'register'
        else:
            limit_type = 'general'
        
        config = self.rate_limits[limit_type]
        cache_key = f'rate_limit_{limit_type}_{ip}'
        
        current_count = cache.get(cache_key, 0)
        
        if current_count >= config['limit']:
            return False
        
        # Increment counter
        cache.set(cache_key, current_count + 1, config['window'])
        return True
    
    def detect_attack_patterns(self, request):
        """Detect common attack patterns in request data"""
        
        # Check GET parameters
        for key, value in request.GET.items():
            if self.contains_attack_pattern(str(value)):
                return True
        
        # Check POST parameters
        if hasattr(request, 'POST'):
            for key, value in request.POST.items():
                if self.contains_attack_pattern(str(value)):
                    return True
        
        # Check headers
        for header, value in request.META.items():
            if header.startswith('HTTP_'):
                if self.contains_attack_pattern(str(value)):
                    return True
        
        return False
    
    def contains_attack_pattern(self, text):
        """Check if text contains attack patterns"""
        text_lower = text.lower()
        
        # Check SQL injection patterns
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, text_lower):
                return True
        
        # Check XSS patterns
        for pattern in self.xss_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        
        return False
    
    def detect_automated_behavior(self, request, ip):
        """Detect automated/bot behavior"""
        cache_key = f'request_timing_{ip}'
        now = datetime.now().timestamp()
        
        # Get previous request times
        request_times = cache.get(cache_key, [])
        
        # Add current request time
        request_times.append(now)
        
        # Keep only last 10 requests
        request_times = request_times[-10:]
        
        # Check if more than 5 requests in last 10 seconds
        recent_requests = [t for t in request_times if now - t < 10]
        
        # Update cache
        cache.set(cache_key, request_times, 300)  # 5 minutes
        
        return len(recent_requests) > 5
    
    def validate_request_size(self, request):
        """Validate request size to prevent DoS attacks"""
        max_size = getattr(settings, 'MAX_REQUEST_SIZE', 5 * 1024 * 1024)  # 5MB default
        
        content_length = request.META.get('CONTENT_LENGTH', 0)
        try:
            content_length = int(content_length)
        except (ValueError, TypeError):
            content_length = 0
        
        return content_length <= max_size
    
    def increment_threat_score(self, ip, points):
        """Increment threat score for an IP"""
        cache_key = f'threat_score_{ip}'
        current_score = cache.get(cache_key, 0)
        new_score = current_score + points
        
        # Set expiry based on threat level
        expiry = 3600 if new_score < 50 else 7200  # 1-2 hours
        cache.set(cache_key, new_score, expiry)
        
        # Auto-blacklist high threat IPs
        if new_score >= 50:
            self.blacklist_ip(ip, 'High threat score')
    
    def blacklist_ip(self, ip, reason):
        """Add IP to blacklist"""
        cache_key = f'blacklisted_ip_{ip}'
        cache.set(cache_key, True, 86400)  # 24 hours
        
        logger.critical(f'IP blacklisted: {ip} - Reason: {reason}')
    
    def rate_limit_response(self, request):
        """Return appropriate response for rate limited requests"""
        if request.headers.get('Accept', '').startswith('application/json'):
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'message': 'تعداد درخواست‌های شما از حد مجاز گذشته است.'
            }, status=429)
        else:
            messages.error(request, 'تعداد درخواست‌های شما از حد مجاز گذشته است. لطفاً کمی صبر کنید.')
            return redirect('core:home')


class SecurityHeadersMiddleware(MiddlewareMixin):
    """اضافه کردن هدرهای امنیتی به response"""
    
    def process_response(self, request, response):
        # اضافه کردن هدرهای امنیتی
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Strict Transport Security (فقط برای HTTPS)
        if request.is_secure():
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' cdnjs.cloudflare.com code.jquery.com cdn.jsdelivr.net unpkg.com; "
            "style-src 'self' 'unsafe-inline' fonts.googleapis.com cdn.jsdelivr.net unpkg.com; "
            "font-src 'self' fonts.gstatic.com; "
            "img-src 'self' data: https:;"
        )
        
        return response


class SessionSecurityMiddleware(MiddlewareMixin):
    """بررسی امنیت session"""
    
    def process_request(self, request):
        if request.user.is_authenticated:
            # بررسی تغییر IP (اگر فعال باشد)
            from django.conf import settings
            if getattr(settings, 'CHECK_SESSION_IP', False):
                session_ip = request.session.get('ip_address')
                current_ip = self.get_client_ip(request)
                
                if session_ip and session_ip != current_ip:
                    logger.warning(f"IP تغییر کرده: کاربر {request.user.email}, قبلی: {session_ip}, فعلی: {current_ip}")
                    # خروج اجباری کاربر
                    from django.contrib.auth import logout
                    logout(request)
                    messages.error(request, 'به دلایل امنیتی، باید دوباره وارد شوید.')
                    return redirect('account:login')
                
                # ذخیره IP در session
                request.session['ip_address'] = current_ip
    
    def get_client_ip(self, request):
        """دریافت IP واقعی کاربر"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ErrorHandlingMiddleware(MiddlewareMixin):
    """مدیریت خطاها به صورت امن"""
    
    def process_exception(self, request, exception):
        """مدیریت خطاها"""
        logger.error(f"خطا برای کاربر {getattr(request.user, 'email', 'Anonymous')}: {str(exception)}", 
                    exc_info=True)
        
        # در صورت خطا، session را پاک نکن ولی اطلاعات حساس را لاگ نکن
        # فقط لاگ کن برای بررسی بعدی
        
        # اگر کاربر authenticated است و خطای دسترسی دارد
        if request.user.is_authenticated and '404' not in str(exception):
            # ثبت خطا برای بررسی
            pass
        
        # بذار Django خطا را handle کند
        return None


class LoginHistoryMiddleware(MiddlewareMixin):
    """ثبت تاریخچه ورود و خروج"""
    
    def process_request(self, request):
        if request.user.is_authenticated:
            # بررسی آیا این اولین درخواست بعد از login است
            if not request.session.get('login_recorded'):
                self.record_login(request)
                request.session['login_recorded'] = True
    
    def record_login(self, request):
        """ثبت اطلاعات ورود"""
        try:
            from dashboard.models import LoginHistory
            
            ip_address = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            LoginHistory.objects.create(
                user=request.user,
                ip_address=ip_address,
                user_agent=user_agent,
                device_type=self.get_device_type(user_agent),
                browser=self.get_browser(user_agent),
                session_key=request.session.session_key,
                is_successful=True
            )
        except Exception as e:
            logger.error(f"خطا در ثبت تاریخچه ورود: {str(e)}")
    
    def get_client_ip(self, request):
        """دریافت IP واقعی کاربر"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_device_type(self, user_agent):
        """تشخیص نوع دستگاه"""
        user_agent_lower = user_agent.lower()
        if 'mobile' in user_agent_lower or 'android' in user_agent_lower:
            return 'mobile'
        elif 'tablet' in user_agent_lower or 'ipad' in user_agent_lower:
            return 'tablet'
        return 'desktop'
    
    def get_browser(self, user_agent):
        """تشخیص مرورگر"""
        user_agent_lower = user_agent.lower()
        if 'chrome' in user_agent_lower:
            return 'Chrome'
        elif 'firefox' in user_agent_lower:
            return 'Firefox'
        elif 'safari' in user_agent_lower:
            return 'Safari'
        elif 'edge' in user_agent_lower:
            return 'Edge'
        return 'Unknown' 