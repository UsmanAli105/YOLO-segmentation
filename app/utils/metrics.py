from prometheus_client import Counter, Histogram, Gauge

# Request Metrics
REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total count of HTTP requests",
    ["method", "endpoint", "status_code"]
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "Duration of HTTP requests in seconds",
    ["method", "endpoint"]
)

# Application/Inference Metrics
INFERENCE_DURATION = Histogram(
    "yolo_inference_duration_seconds",
    "Duration of YOLOv8 inference execution in seconds"
)

ACTIVE_REQUESTS = Gauge(
    "active_requests",
    "Number of currently active HTTP requests"
)

ACTIVE_INFERENCES = Gauge(
    "active_inferences",
    "Number of currently active YOLOv8 inferences"
)

QUEUED_INFERENCES = Gauge(
    "queued_inferences",
    "Number of requests waiting in the inference queue"
)

# Resilience Metrics
REJECTED_REQUESTS = Counter(
    "http_requests_rejected_total",
    "Total count of requests rejected due to queue capacity (503)"
)

RATE_LIMIT_VIOLATIONS = Counter(
    "http_rate_limit_violations_total",
    "Total count of requests rejected due to rate limits (429)"
)
