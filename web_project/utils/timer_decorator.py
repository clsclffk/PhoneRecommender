import time
from functools import wraps

def timer(func):
    """함수 실행 시간을 측정하는 데코레이터"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"[TIMER] {func.__name__} 실행 시간: {elapsed_time:.2f}초")
        return result
    return wrapper