import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from core.logging.logger import log_context, get_logger

logger = get_logger("http_middleware")

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()
        
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Build context metadata mapping
        ctx = {
            "correlation_id": correlation_id,
            "request_id": request_id,
            "workflow_id": request.headers.get("X-Workflow-ID"),
            "episode_id": request.headers.get("X-Episode-ID"),
            "universe_id": request.headers.get("X-Universe-ID"),
            "user_id": request.headers.get("X-User-ID"),
            "service_name": "api",
        }
        
        token = log_context.set(ctx)
        try:
            response = await call_next(request)
            
            execution_time = time.perf_counter() - start_time
            ctx["execution_time"] = f"{execution_time:.4f}s"
            log_context.set(ctx)
            
            logger.info(
                f"HTTP {request.method} {request.url.path} completed with status {response.status_code}",
                extra={"status_code": response.status_code}
            )
            
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Request-ID"] = request_id
            return response
            
        except Exception as exc:
            execution_time = time.perf_counter() - start_time
            ctx["execution_time"] = f"{execution_time:.4f}s"
            log_context.set(ctx)
            
            logger.error(
                f"HTTP {request.method} {request.url.path} failed: {str(exc)}",
                exc_info=True
            )
            raise exc
        finally:
            log_context.reset(token)
