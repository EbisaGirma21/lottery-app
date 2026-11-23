"""
Service layer for creating audit log entries.

This module provides a simple interface for logging actions from anywhere
in the application. All other apps should use log_action() instead of
directly creating AuditLog instances.
"""
import logging
from typing import Optional

from apps.audit_logs.models import AuditLog

logger = logging.getLogger(__name__)


def log_action(
    user=None,
    action: str = '',
    entity_type: str = '',
    entity_id: str = '',
    old_value: Optional[dict] = None,
    new_value: Optional[dict] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    """
    Create an audit log entry.

    Args:
        user: The user who performed the action (None for system actions).
        action: The action type (e.g., 'LOGIN', 'USER_CREATED').
        entity_type: The type of entity affected (e.g., 'User', 'Lottery').
        entity_id: The ID of the entity affected.
        old_value: The previous state as a dict (for updates).
        new_value: The new state as a dict (for creates/updates).
        ip_address: Client IP address.

    Returns:
        The created AuditLog instance.
    """
    try:
        audit_log = AuditLog.objects.create(
            user=user,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
        )
        logger.info(
            'Audit: %s performed %s on %s#%s',
            user.email if user else 'System',
            action,
            entity_type,
            entity_id,
        )
        return audit_log
    except Exception as e:
        # Audit logging should never break the main operation
        logger.error('Failed to create audit log: %s', str(e))
        return None
