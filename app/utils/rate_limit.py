import time
import logging
from collections import defaultdict
from fastapi import Request, HTTPException
from app.config import settings

logger = logging.getLogger(__name__)

# In-memory store for rate limiting: { "IP_ADDRESS": [timestamp1, timestamp2, ...] }
rate_limit_records = defaultdict(list)

async def check_rate_limit(request: Request):
    """
    FastAPI Dependency for IP-based rate limiting.
    Raises a 429 HTTPException if the limit is exceeded.
    """
    client_ip = request.client.host if request.client else "unknown"
    current_time = time.time()
    
    # Get timestamps for this IP
    timestamps = rate_limit_records[client_ip]
    
    # Remove timestamps older than the window
    window_start = current_time - settings.rate_limit_window_seconds
    valid_timestamps = [t for t in timestamps if t > window_start]
    
    # Check limit
    if len(valid_timestamps) >= settings.rate_limit_requests:
        logger.warning("Rate limit exceeded for IP: %s (%d requests in %ds)", 
                       client_ip, len(valid_timestamps), settings.rate_limit_window_seconds)
        raise HTTPException(
            status_code=429,
            detail=f"Too Many Requests. Limit is {settings.rate_limit_requests} per {settings.rate_limit_window_seconds} seconds."
        )
    
    # Record the new request
    valid_timestamps.append(current_time)
    rate_limit_records[client_ip] = valid_timestamps
    
    return True
