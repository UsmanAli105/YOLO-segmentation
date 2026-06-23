import contextvars

# Global context variable for the Request ID. Defaults to '-' if not in a request context.
request_id = contextvars.ContextVar("request_id", default="-")
