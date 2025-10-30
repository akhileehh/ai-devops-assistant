# metrics_helper.py
from prometheus_client import Counter, Histogram, start_http_server
import threading
import time


#  Define Prometheus Metrics


# Counts how many times each slash command was used
command_counter = Counter(
    'bot_commands_total',
    'Total number of executed slash commands',
    ['command']
)

# Measures how long each command takes to complete
command_duration = Histogram(
    'bot_command_duration_seconds',
    'Command execution time in seconds',
    ['command']
)

# Counts failed command executions
error_counter = Counter(
    'bot_command_errors_total',
    'Total number of failed slash commands',
    ['command']
)

#  Start Prometheus Metrics Server

def start_metrics_server():
    """Runs a Prometheus metrics HTTP server on port 8000 in a background thread."""
    threading.Thread(target=start_http_server, args=(8000,), daemon=True).start()



#  Helper Decorator (Optional)

def track_command(command_name):
    """Decorator to automatically track command usage, duration, and errors."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            command_counter.labels(command=command_name).inc()
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                command_duration.labels(command=command_name).observe(time.time() - start_time)
                return result
            except Exception:
                error_counter.labels(command=command_name).inc()
                raise
        return wrapper
    return decorator
