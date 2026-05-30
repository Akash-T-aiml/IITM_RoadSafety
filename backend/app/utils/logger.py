"""
SmartRescue AI — Structured Logging
JSON-formatted logs with correlation IDs and audit trail support.
"""

import logging
import json
import sys
from datetime import datetime, timezone
from typing import Optional

from app.config.settings import get_settings


class JSONFormatter(logging.Formatter):
    """Format log records as JSON for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Include extra fields if present
        if hasattr(record, "uid"):
            log_data["uid"] = record.uid
        if hasattr(record, "case_id"):
            log_data["case_id"] = record.case_id
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id

        # Include any additional extra fields
        for key, value in record.__dict__.items():
            if key not in logging.LogRecord(
                "", 0, "", 0, "", (), None
            ).__dict__ and key not in log_data:
                log_data[key] = value

        if record.exc_info and record.exc_info[1]:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, default=str)


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger with JSON formatting."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        try:
            settings = get_settings()
            level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
        except Exception:
            level = logging.INFO

        logger.setLevel(level)

        # Console handler with JSON formatting
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

        logger.propagate = False

    return logger


class AuditLogger:
    """Write audit log entries to Firestore for compliance tracking."""

    def __init__(self):
        self.logger = get_logger("audit")

    async def log(
        self,
        action: str,
        actor_id: str,
        resource_type: str,
        resource_id: str,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
    ):
        """Log an auditable action."""
        from app.firebase.firestore_db import FirestoreDB

        entry = {
            "action": action,
            "actor_id": actor_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
            "ip_address": ip_address,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Log to stdout
        self.logger.info(
            f"AUDIT: {action} on {resource_type}/{resource_id} by {actor_id}"
        )

        # Persist to Firestore
        try:
            await FirestoreDB.create_document(FirestoreDB.AUDIT_LOG, entry)
        except Exception as e:
            self.logger.error(f"Failed to write audit log to Firestore: {e}")


audit_logger = AuditLogger()
