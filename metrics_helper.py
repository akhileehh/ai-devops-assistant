# metrics_helper.py
from prometheus_client import Counter, Histogram, start_http_server
import threading
import time
from functools import wraps
from typing import Any, Callable, Coroutine, Dict

# ------------------ Prometheus Metrics ------------------

command_counter = Counter(
    'bot_commands_total',
    'Total number of executed slash commands',
    ['command']
)

command_duration = Histogram(
    'bot_command_duration_seconds',
    'Command execution time in seconds',
    ['command']
)

error_counter = Counter(
    'bot_command_errors_total',
    'Total number of failed slash commands',
    ['command']
)


# ------------------ Metrics Server ------------------

def start_metrics_server() -> None:
    """Run Prometheus metrics HTTP server on port 8000 in a background thread."""
    threading.Thread(target=start_http_server, args=(8000,), daemon=True).start()


# ------------------ Decorator Fix ------------------

def track_command(command_name: str) -> Callable[..., Callable[..., Coroutine[Any, Any, Any]]]:
    """Decorator to automatically track command usage, duration, and errors."""
    def decorator(func: Callable[..., Coroutine[Any, Any, Any]]):
        @wraps(func)
        async def wrapper(interaction: Any, *args: Any, **kwargs: Any) -> Any:
            command_counter.labels(command=command_name).inc()
            start_time = time.time()
            try:
                result = await func(interaction, *args, **kwargs)
                command_duration.labels(command=command_name).observe(time.time() - start_time)
                return result
            except Exception:
                error_counter.labels(command=command_name).inc()
                raise

        # ✅ Tell Discord to use the *original command signature*
        # (Prevents "missing type annotation" TypeError)
        if hasattr(func, "__signature__"):
            wrapper.__signature__ = func.__signature__
        return wrapper
    return decorator
