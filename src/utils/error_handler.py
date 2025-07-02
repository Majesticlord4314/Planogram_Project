import traceback
from functools import wraps
from typing import Callable, Any, Optional

class PlanogramError(Exception):
    """Base exception for planogram system"""
    pass

class DataLoadError(PlanogramError):
    """Error loading data"""
    pass

class ValidationError(PlanogramError):
    """Data validation error"""
    pass

class OptimizationError(PlanogramError):
    """Optimization algorithm error"""
    pass

class ConfigurationError(PlanogramError):
    """Configuration error"""
    pass

def handle_errors(default_return=None, raise_on_error=True):
    """Decorator for error handling"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except PlanogramError:
                if raise_on_error:
                    raise
                return default_return
            except Exception as e:
                if raise_on_error:
                    raise PlanogramError(f"Unexpected error in {func.__name__}: {str(e)}")
                return default_return
        return wrapper
    return decorator