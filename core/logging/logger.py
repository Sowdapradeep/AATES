import logging
import time
import platform
from contextvars import ContextVar
from typing import Any
from pythonjsonlogger import jsonlogger
from core.config import settings

# Thread/Task-local log context fields
log_context: ContextVar[dict[str, Any]] = ContextVar("log_context", default={})

class StructuredJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record: dict[str, Any], record: logging.LogRecord, message_dict: dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)
        
        # Core structured logs format
        log_record["timestamp"] = self.formatTime(record, self.datefmt)
        log_record["level"] = record.levelname
        log_record["service"] = settings.app.name
        
        # Inject runtime context properties
        ctx = log_context.get()
        for key, val in ctx.items():
            if val is not None:
                log_record[key] = val


class CloudWatchLogsHandler(logging.Handler):
    """Resilient AWS CloudWatch logging handler with silent console fallbacks."""
    
    def __init__(self, log_group: str, log_stream: str, region: str) -> None:
        super().__init__()
        self.log_group = log_group
        self.log_stream = log_stream
        self.region = region
        self.client = None
        self.sequence_token = None
        self._initialized = False

    def _init_client(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        try:
            import boto3
            self.client = boto3.client("logs", region_name=self.region)
            try:
                self.client.create_log_group(logGroupName=self.log_group)
            except Exception:
                pass
            try:
                self.client.create_log_stream(logGroupName=self.log_group, logStreamName=self.log_stream)
            except Exception:
                pass
        except Exception:
            self.client = None

    def emit(self, record: logging.LogRecord) -> None:
        self._init_client()
        if not self.client:
            return
            
        try:
            log_message = self.format(record)
            timestamp = int(record.created * 1000)
            
            kwargs = {
                "logGroupName": self.log_group,
                "logStreamName": self.log_stream,
                "logEvents": [
                    {
                        "timestamp": timestamp,
                        "message": log_message
                    }
                ]
            }
            if self.sequence_token:
                kwargs["sequenceToken"] = self.sequence_token
                
            resp = self.client.put_log_events(**kwargs)
            self.sequence_token = resp.get("nextSequenceToken")
        except Exception:
            pass


def setup_logging() -> None:
    root_logger = logging.getLogger()
    
    # Remove existing default handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    handler = logging.StreamHandler()
    formatter = StructuredJsonFormatter(
        "%(timestamp)s %(level)s %(message)s %(service)s"
    )
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    
    # Add CloudWatch Logs Handler if configured and enabled
    if settings.aws.cloudwatch_logs_enabled:
        stream_name = f"instance-{platform.node()}-{int(time.time())}"
        cw_handler = CloudWatchLogsHandler(
            log_group=settings.aws.cloudwatch_log_group,
            log_stream=stream_name,
            region=settings.aws.region
        )
        cw_handler.setFormatter(formatter)
        root_logger.addHandler(cw_handler)
    
    log_level = logging.DEBUG if settings.app.debug else logging.INFO
    root_logger.setLevel(log_level)
    
    # Dampen noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
