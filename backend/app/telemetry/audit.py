"""Operational and Security Audit Logging Service.

Maintains auditable events for authentication, fleet assignments, safety rejections, and disruptions.
"""
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from app.schemas.telemetry import AuditEvent


class AuditLogService:
    """In-memory and persistent audit logger for municipal operational oversight."""

    def __init__(self, max_buffer_size: int = 500):
        self.max_buffer_size = max_buffer_size
        self._logs: List[AuditEvent] = []

    def log_event(
        self,
        actor: str,
        role: str,
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        reason: Optional[str] = None,
        result: str = "SUCCESS",
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """Record an operational or security audit log entry."""
        event = AuditEvent(
            event_id=f"AUD-{uuid.uuid4().hex[:8].upper()}",
            timestamp=datetime.utcnow(),
            actor=actor,
            role=role,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            reason=reason,
            result=result,
            details=details or {},
        )
        self._logs.append(event)
        if len(self._logs) > self.max_buffer_size:
            self._logs.pop(0)

        return event

    def get_events(
        self,
        limit: int = 50,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
    ) -> List[AuditEvent]:
        """Query audit log entries with optional filters."""
        results = self._logs
        if action:
            results = [e for e in results if e.action == action]
        if entity_type:
            results = [e for e in results if e.entity_type == entity_type]
        return list(reversed(results[-limit:]))


# Global singleton audit service
audit_service = AuditLogService()
