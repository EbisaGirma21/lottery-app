"""
AuditLog model — immutable record of every important system action.
"""
import uuid

from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """
    Stores an immutable record of important actions performed in the system.

    Entries are append-only and should never be modified or deleted.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        help_text='The user who performed the action. NULL for system actions.',
    )
    action = models.CharField(
        max_length=100,
        db_index=True,
        help_text='Type of action performed (e.g., LOGIN, USER_CREATED, PAYMENT_APPROVED).',
    )
    entity_type = models.CharField(
        max_length=100,
        db_index=True,
        help_text='The type of entity affected (e.g., User, Lottery, Payment).',
    )
    entity_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text='The ID of the entity affected.',
    )
    old_value = models.JSONField(
        null=True,
        blank=True,
        help_text='The previous state (for updates).',
    )
    new_value = models.JSONField(
        null=True,
        blank=True,
        help_text='The new state (for creates/updates).',
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address of the client that triggered the action.',
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        indexes = [
            models.Index(fields=['action', 'entity_type'], name='idx_audit_action_entity'),
            models.Index(fields=['user', 'created_at'], name='idx_audit_user_date'),
        ]

    def __str__(self) -> str:
        user_str = self.user.email if self.user else 'System'
        return f'[{self.created_at:%Y-%m-%d %H:%M}] {user_str} — {self.action} on {self.entity_type}#{self.entity_id}'
