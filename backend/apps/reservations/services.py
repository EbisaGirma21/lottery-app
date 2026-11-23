"""
Reservation service — atomic ticket reservation with row-level locking.

This is the CRITICAL anti-duplicate reservation mechanism.
Uses PostgreSQL SELECT FOR UPDATE to prevent two customers from
reserving the same ticket simultaneously.
"""
import logging
from datetime import timedelta
from typing import List

from django.db import transaction
from django.utils import timezone

from apps.lotteries.models import Customer, Lottery, LotteryStatus
from apps.reservations.models import Reservation, ReservationStatus
from apps.tickets.models import Ticket, TicketStatus

logger = logging.getLogger(__name__)


class ReservationError(Exception):
    """Raised when a reservation cannot be completed."""
    pass


def reserve_tickets(
    customer: Customer,
    lottery: Lottery,
    ticket_numbers: List[str],
) -> List[Reservation]:
    """
    Atomically reserve one or more tickets for a customer.

    Uses database transactions and row-level locking (SELECT FOR UPDATE)
    to guarantee that two customers can never reserve the same ticket.

    Args:
        customer: The customer making the reservation.
        lottery: The lottery to reserve tickets from.
        ticket_numbers: List of ticket number strings to reserve.

    Returns:
        List of created Reservation instances.

    Raises:
        ReservationError: If reservation cannot be completed.
    """
    # Pre-validation (outside transaction for fast failure)
    if customer.status != 'active':
        raise ReservationError('Your account has been blocked.')

    if lottery.status != LotteryStatus.OPEN:
        raise ReservationError(
            f'This lottery is not accepting reservations (status: {lottery.get_status_display()}).'
        )

    if not ticket_numbers:
        raise ReservationError('No ticket numbers provided.')

    # Check max tickets per customer
    if lottery.max_tickets_per_customer is not None:
        existing_count = Reservation.objects.filter(
            customer=customer,
            lottery=lottery,
            status__in=[ReservationStatus.ACTIVE, ReservationStatus.CONFIRMED],
        ).count()
        remaining_allowed = lottery.max_tickets_per_customer - existing_count
        if len(ticket_numbers) > remaining_allowed:
            raise ReservationError(
                f'You can only reserve {remaining_allowed} more ticket(s) for this lottery. '
                f'Maximum allowed: {lottery.max_tickets_per_customer}.'
            )

    expires_at = timezone.now() + timedelta(hours=lottery.reservation_hours)
    reservations = []

    with transaction.atomic():
        for ticket_number in ticket_numbers:
            # Lock the ticket row — this is the critical section.
            # SELECT ... FOR UPDATE blocks concurrent transactions.
            try:
                ticket = (
                    Ticket.objects
                    .select_for_update()
                    .get(lottery=lottery, ticket_number=ticket_number)
                )
            except Ticket.DoesNotExist:
                raise ReservationError(
                    f'Ticket #{ticket_number} does not exist in this lottery.'
                )

            if ticket.status != TicketStatus.AVAILABLE:
                raise ReservationError(
                    f'Ticket #{ticket_number} is not available '
                    f'(current status: {ticket.get_status_display()}).'
                )

            # Reserve the ticket
            ticket.status = TicketStatus.RESERVED
            ticket.save(update_fields=['status', 'updated_at'])

            reservation = Reservation.objects.create(
                customer=customer,
                lottery=lottery,
                ticket=ticket,
                expires_at=expires_at,
                status=ReservationStatus.ACTIVE,
            )
            reservations.append(reservation)

    logger.info(
        'Customer %s reserved %d ticket(s) for lottery "%s". Expires: %s',
        customer.full_name, len(reservations), lottery.name, expires_at,
    )

    # Audit
    from apps.audit_logs.services import log_action
    log_action(
        action='TICKETS_RESERVED',
        entity_type='Reservation',
        entity_id=','.join(str(r.id) for r in reservations),
        new_value={
            'customer': str(customer.id),
            'lottery': str(lottery.id),
            'tickets': ticket_numbers,
            'expires_at': expires_at.isoformat(),
        },
    )

    return reservations


def cancel_reservation(reservation: Reservation) -> Reservation:
    """
    Cancel an active reservation and release the ticket.

    Args:
        reservation: The Reservation to cancel.

    Returns:
        The updated Reservation instance.

    Raises:
        ReservationError: If the reservation cannot be cancelled.
    """
    if reservation.status != ReservationStatus.ACTIVE:
        raise ReservationError(
            f'Cannot cancel reservation with status: {reservation.get_status_display()}.'
        )

    with transaction.atomic():
        # Lock and release the ticket
        ticket = Ticket.objects.select_for_update().get(pk=reservation.ticket_id)
        ticket.status = TicketStatus.AVAILABLE
        ticket.save(update_fields=['status', 'updated_at'])

        reservation.status = ReservationStatus.CANCELLED
        reservation.save(update_fields=['status'])

    logger.info(
        'Reservation for ticket #%s cancelled (customer: %s)',
        ticket.ticket_number, reservation.customer.full_name,
    )
    return reservation


def expire_stale_reservations() -> int:
    """
    Expire all active reservations whose expiration time has passed.

    Called by the Celery beat task. Releases tickets back to AVAILABLE.
    Does NOT expire reservations that have already been confirmed.

    Returns:
        Number of reservations expired.
    """
    now = timezone.now()
    expired_reservations = Reservation.objects.filter(
        status=ReservationStatus.ACTIVE,
        expires_at__lte=now,
    ).select_related('ticket', 'customer')

    count = 0
    for reservation in expired_reservations:
        try:
            with transaction.atomic():
                ticket = Ticket.objects.select_for_update().get(pk=reservation.ticket_id)

                # Only release if ticket is still RESERVED
                if ticket.status == TicketStatus.RESERVED:
                    ticket.status = TicketStatus.AVAILABLE
                    ticket.customer = None
                    ticket.save(update_fields=['status', 'customer', 'updated_at'])

                reservation.status = ReservationStatus.EXPIRED
                reservation.save(update_fields=['status'])
                count += 1

                logger.info(
                    'Expired reservation: ticket #%s (customer: %s, lottery: %s)',
                    ticket.ticket_number,
                    reservation.customer.full_name,
                    reservation.lottery.name,
                )
        except Exception as e:
            logger.error(
                'Error expiring reservation %s: %s',
                reservation.id, str(e),
            )

    if count > 0:
        from apps.audit_logs.services import log_action
        log_action(
            action='RESERVATIONS_EXPIRED',
            entity_type='Reservation',
            entity_id='batch',
            new_value={'count': count, 'timestamp': now.isoformat()},
        )

    return count
