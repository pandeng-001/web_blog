# middleware/rate_limit.py
import time
import logging
from datetime import datetime
from django.core.cache import cache
from django.http import JsonResponse
from django.conf import settings

# 配置访问日志
access_logger = logging.getLogger('access')

class RateLimitMiddleware:
    """IP级别的流量控制中间件"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limit_enabled = getattr(settings, 'RATE_LIMIT_ENABLED', True)
        self.rate_limit_requests = getattr(settings, 'RATE_LIMIT_REQUESTS', 100)
        self.rate_limit_window = getattr(settings, 'RATE_LIMIT_WINDOW', 60)
        self.login_rate_limit = getattr(settings, 'LOGIN_RATE_LIMIT', 5)
        self.login_rate_window = getattr(settings, 'LOGIN_RATE_WINDOW', 300)
        self.whitelist_ips = getattr(settings, 'RATE_LIMIT_WHITELIST', ['127.0.0.1'])

    def __call__(self, request):
        if not self.rate_limit_enabled:
            return self.get_response(request)
        
        client_ip = self.get_client_ip(request)
        
        if client_ip in self.whitelist_ips:
            return self.get_response(request)
        
        if self.is_rate_limited(client_ip):
            return JsonResponse({
                'error': '请求过于频繁，请稍后再试',
                'code': 429
            }, status=429)
        
        if self.is_login_request(request):
            if self.is_login_rate_limited(client_ip):
                return JsonResponse({
                    'error': f'登录尝试次数过多，请{self.login_rate_window // 60}分钟后再试',
                    'code': 429
                }, status=429)
            self.record_login_attempt(client_ip)
        
        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        """获取客户端真实IP"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('HTTP_X_REAL_IP')
            if not ip:
                ip = request.META.get('REMOTE_ADDR')
        return ip

    def is_login_request(self, request):
        """判断是否为登录请求 - 根据你的 URL 配置修改"""
        path = request.path
        return (
            path.startswith('/login/') and  # 修改为你的登录路径
            request.method == 'POST'
        )

    def is_rate_limited(self, ip):
        """检查IP是否超过通用限流"""
        cache_key = f'rate_limit:{ip}'
        request_count = cache.get(cache_key, 0)
        
        if request_count >= self.rate_limit_requests:
            return True
        
        cache.set(cache_key, request_count + 1, self.rate_limit_window)
        return False

    def is_login_rate_limited(self, ip):
        """检查登录尝试是否超限"""
        cache_key = f'login_attempt:{ip}'
        attempt_count = cache.get(cache_key, 0)
        return attempt_count >= self.login_rate_limit

    def record_login_attempt(self, ip):
        """记录登录尝试"""
        cache_key = f'login_attempt:{ip}'
        attempt_count = cache.get(cache_key, 0)
        cache.set(cache_key, attempt_count + 1, self.login_rate_window)


class SecurityHeadersMiddleware:
    """安全响应头中间件"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        if request.is_secure():
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response


class AccessLogMiddleware:
    """访问日志中间件 - 记录游客访问信息"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        # 不记录日志的路径（静态文件等）
        self.exclude_paths = [
            '/static/',
            '/media/',
            '/favicon.ico',
            '/robots.txt',
        ]

    def __call__(self, request):
        start_time = time.time()
        
        # 处理请求
        response = self.get_response(request)
        
        # 计算响应时间
        duration = time.time() - start_time
        
        # 判断是否需要记录日志
        if self.should_log(request):
            self.log_request(request, response, duration)
        
        return response

    def should_log(self, request):
        """判断是否需要记录日志"""
        # 排除静态文件等路径
        for path in self.exclude_paths:
            if request.path.startswith(path):
                return False
        return True

    def get_client_ip(self, request):
        """获取客户端真实IP"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')

    def get_user_agent(self, request):
        """获取用户代理"""
        return request.META.get('HTTP_USER_AGENT', 'unknown')

    def get_referer(self, request):
        """获取来源页面"""
        return request.META.get('HTTP_REFERER', 'direct')

    def get_device_info(self, user_agent):
        """简单的设备识别"""
        user_agent_lower = user_agent.lower()
        
        if 'mobile' in user_agent_lower or 'android' in user_agent_lower:
            device_type = 'Mobile'
        elif 'tablet' in user_agent_lower or 'ipad' in user_agent_lower:
            device_type = 'Tablet'
        else:
            device_type = 'Desktop'
        
        # 识别操作系统
        if 'windows' in user_agent_lower:
            os_name = 'Windows'
        elif 'mac' in user_agent_lower:
            os_name = 'macOS'
        elif 'linux' in user_agent_lower:
            os_name = 'Linux'
        elif 'android' in user_agent_lower:
            os_name = 'Android'
        elif 'iphone' in user_agent_lower or 'ipad' in user_agent_lower:
            os_name = 'iOS'
        else:
            os_name = 'Unknown'
        
        # 识别浏览器
        if 'chrome' in user_agent_lower and 'edg' not in user_agent_lower:
            browser = 'Chrome'
        elif 'edg' in user_agent_lower:
            browser = 'Edge'
        elif 'firefox' in user_agent_lower:
            browser = 'Firefox'
        elif 'safari' in user_agent_lower and 'chrome' not in user_agent_lower:
            browser = 'Safari'
        else:
            browser = 'Unknown'
        
        return device_type, os_name, browser

    def log_request(self, request, response, duration):
        """记录访问日志"""
        client_ip = self.get_client_ip(request)
        user_agent = self.get_user_agent(request)
        referer = self.get_referer(request)
        device_type, os_name, browser = self.get_device_info(user_agent)
        
        # 获取用户信息
        if request.user.is_authenticated:
            username = request.user.username
            user_type = 'User'
        else:
            username = 'Anonymous'
            user_type = 'Guest'
        
        # 构建日志信息
        log_data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'ip': client_ip,
            'user': username,
            'user_type': user_type,
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'duration': f'{duration:.3f}s',
            'device': device_type,
            'os': os_name,
            'browser': browser,
            'referer': referer,
            'user_agent': user_agent,
        }
        
        # 格式化日志输出
        log_message = (
            f"[{log_data['timestamp']}] "
            f"{log_data['ip']} | {log_data['user_type']}: {log_data['user']} | "
            f"{log_data['method']} {log_data['path']} | "
            f"Status: {log_data['status']} | "
            f"Time: {log_data['duration']} | "
            f"{log_data['device']}/{log_data['os']}/{log_data['browser']} | "
            f"Referer: {log_data['referer']}"
        )
        
        # 记录到日志文件
        if response.status_code >= 400:
            access_logger.warning(log_message)
        else:
            access_logger.info(log_message)


