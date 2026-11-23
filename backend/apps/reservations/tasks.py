"""
Celery tasks for reservation management.
"""
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name='reservations.expire_stale_reservations')
def expire_stale_reservations_task():
    """
    Periodic task to expire all stale reservations.

    Should be run every 5–15 minutes via Celery Beat.
    """
    from apps.reservations.services import expire_stale_reservations

    count = expire_stale_reservations()
    logger.info('Expired %d stale reservations.', count)
    return count
