import logging
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
    
    log_level = logging.DEBUG if settings.app.debug else logging.INFO
    root_logger.setLevel(log_level)
    
    # Dampen noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
