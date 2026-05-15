#============================================================
# - subject: exception_logging.py
# - created: 2026-05-14
# - updated: 2026-05-14
# - summary: Centralized error logging utility.
# - caution: Uses inspect to automatically resolve caller info.
#============================================================
from datetime import datetime
import inspect

def log_error(summary: str, exception: Exception = None):
    """
    Logs an error in the format: YY-MM-DD HH:MM [{classname}][{methodname}]{summary}
    """
    frame = inspect.currentframe().f_back
    method_name = frame.f_code.co_name
    class_name = "Module"
    
    if 'self' in frame.f_locals:
        class_name = frame.f_locals['self'].__class__.__name__
    elif 'cls' in frame.f_locals:
        class_name = frame.f_locals['cls'].__name__

    time_str = datetime.now().strftime("%y-%m-%d %H:%M")
    short_summary = str(summary)[:40]
    
    log_msg = f"{time_str} [{class_name}][{method_name}]{short_summary}"
    if exception:
        log_msg += f" - {str(exception)}"
        
    print(log_msg)

def log_info(summary: str):
    """
    Logs an info message in the format: YY-MM-DD HH:MM [{classname}][{methodname}]{summary}
    """
    frame = inspect.currentframe().f_back
    method_name = frame.f_code.co_name
    class_name = "Module"
    
    if 'self' in frame.f_locals:
        class_name = frame.f_locals['self'].__class__.__name__
    elif 'cls' in frame.f_locals:
        class_name = frame.f_locals['cls'].__name__

    time_str = datetime.now().strftime("%y-%m-%d %H:%M")
    
    log_msg = f"{time_str} [{class_name}][{method_name}]{summary}"
    print(log_msg)