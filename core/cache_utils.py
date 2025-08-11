from django.core.cache import cache
from django.conf import settings
import hashlib
import json

def get_cache_key(prefix, *args, **kwargs):
    """Generate a consistent cache key"""
    key_parts = [prefix] + [str(arg) for arg in args]
    if kwargs:
        # Sort kwargs for consistent key generation
        sorted_kwargs = sorted(kwargs.items())
        key_parts.extend([f"{k}:{v}" for k, v in sorted_kwargs])
    
    key_string = "|".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()

def cache_function_result(timeout=None, key_prefix=None):
    """Decorator to cache function results"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not key_prefix:
                func_name = func.__name__
            else:
                func_name = key_prefix
            
            cache_key = get_cache_key(func_name, *args, **kwargs)
            result = cache.get(cache_key)
            
            if result is None:
                result = func(*args, **kwargs)
                if timeout is None:
                    timeout = getattr(settings, 'CACHE_TIMEOUTS', {}).get('default', 1800)
                cache.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator

def clear_model_cache(model_name, instance_id=None):
    """Clear cache for a specific model"""
    if instance_id:
        cache_key = f"model_{model_name}_{instance_id}"
        cache.delete(cache_key)
    else:
        # Clear all cache keys for this model
        cache.delete_pattern(f"model_{model_name}_*")

def get_or_cache(key, func, timeout=None, *args, **kwargs):
    """Get value from cache or execute function and cache result"""
    result = cache.get(key)
    if result is None:
        result = func(*args, **kwargs)
        if timeout is None:
            timeout = getattr(settings, 'CACHE_TIMEOUTS', {}).get('default', 1800)
        cache.set(key, result, timeout)
    return result 