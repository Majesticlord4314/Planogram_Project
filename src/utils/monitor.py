import time
from functools import wraps

class PerformanceMonitor:
    """Monitor system performance"""
    
    def __init__(self):
        self.metrics = []
    
    def time_it(self, func):
        """Decorator to time function execution"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start
            print(f"⏱️  {func.__name__} took {duration:.2f}s")
            return result
        return wrapper

monitor = PerformanceMonitor()