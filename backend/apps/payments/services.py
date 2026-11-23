"""
Business logic services for payment submission, staff verification, approval, and rejection.
"""
from decimal import Decimal
import logging
from typing import List, Optional

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.audit_logs.services import log_action
from apps.lotteries.models import Customer, CustomerStatus, Lottery, LotteryStatus
from apps.payments.models import Payment, PaymentMethod, PaymentStatus
from apps.payments.receipt_parser import ReceiptParser
from apps.payments.verifier import TransactionVerifier
from apps.reservations.models import Reservation, ReservationStatus
from apps.tickets.models import Ticket, TicketStatus

logger = logging.getLogger(__name__)


def submit_payment(
    customer: Customer,
    lottery: Lottery,
    reservation_ids: List[str],
    payment_method: str,
    transaction_reference: str,
    amount: Decimal,
    payment_proof=None,
    user=None,
    ip_address: Optional[str] = None,
) -> Payment:
    """
    Submit a manual payment for one or more active reservations.

    Validates:
    - Customer is active (not blocked).
    - Lottery is in OPEN status.
    - Transaction reference is unique and clean.
    - All reservations exist, belong to this customer and lottery, and are ACTIVE.
    - None of the reservations already have a PENDING payment.
    - Amount is sufficient for the total ticket price.

    Automatically triggers bank ledger verification (Verify.ET / Check.et REST API)
    for supported payment channels (Telebirr, CBE, etc.). If verified, automatically
    approves the payment, confirms reservations, and marks tickets as SOLD.

    Returns the created Payment instance.
    """
    ref = transaction_reference.strip()
    if not ref:
        raise ValueError('Transaction reference number is required.')

    if Payment.objects.filter(transaction_reference__iexact=ref).exists():
        raise ValueError(f'Transaction reference "{ref}" has already been submitted.')

    if customer.status != CustomerStatus.ACTIVE:
        raise ValueError('Customer is blocked and cannot submit payments.')

    if lottery.status != LotteryStatus.OPEN:
        raise ValueError(
            f'Lottery "{lottery.name}" is not open for payments (current status: {lottery.get_status_display()}).'
        )

    if not reservation_ids:
        raise ValueError('At least one reservation must be selected for payment.')

    # Verify reservations
    reservations = list(
        Reservation.objects.filter(
            id__in=reservation_ids,
            customer=customer,
            lottery=lottery,
            status=ReservationStatus.ACTIVE,
        ).select_related('ticket')
    )

    if len(reservations) != len(reservation_ids):
        raise ValueError(
            'One or more reservations are invalid, expired, cancelled, or belong to another customer.'
        )

    # Check for duplicate pending payment on any of these reservations
    already_pending = Payment.objects.filter(
        reservations__in=reservations,
        status=PaymentStatus.PENDING,
    ).exists()
    if already_pending:
        raise ValueError(
            'One or more of the selected reservations already has a pending payment verification.'
        )

    # Validate amount
    expected_amount = lottery.ticket_price * len(reservations)
    submitted_amount = Decimal(str(amount))
    if submitted_amount < expected_amount:
        raise ValueError(
            f'Submitted amount ({submitted_amount}) is less than the required total ({expected_amount}) '
            f'for {len(reservations)} ticket(s).'
        )

    with transaction.atomic():
        payment = Payment.objects.create(
            customer=customer,
            lottery=lottery,
            payment_method=payment_method,
            transaction_reference=ref,
            amount=submitted_amount,
            payment_proof=payment_proof,
            status=PaymentStatus.PENDING,
        )
        payment.reservations.set(reservations)

    # ── Receipt parsing & cross-validation ──
    receipt_suspicious = False
    if payment_proof:
        try:
            receipt_data = ReceiptParser.extract(
                file_obj=payment_proof,
                payment_method=payment_method,
            )
            validation_result = ReceiptParser.cross_validate(
                user_reference=ref,
                receipt_data=receipt_data,
                expected_amount=submitted_amount,
            )

            payment.receipt_extraction_data = {
                'extraction': receipt_data.to_dict(),
                'validation': validation_result,
            }
            payment.receipt_reference_match = validation_result['reference_match']
            receipt_suspicious = validation_result['is_suspicious']

            payment.save(
                update_fields=[
                    'receipt_extraction_data',
                    'receipt_reference_match',
                    'updated_at',
                ]
            )

            if receipt_suspicious:
                logger.warning(
                    'Payment %s flagged as suspicious: %s',
                    ref, validation_result['reason'],
                )
            else:
                logger.info(
                    'Payment %s receipt validation passed (confidence: %s)',
                    ref, receipt_data.confidence,
                )
        except Exception as exc:
            logger.exception('Receipt parsing failed for payment %s: %s', ref, exc)
            payment.receipt_extraction_data = {'error': str(exc)}
            payment.save(update_fields=['receipt_extraction_data', 'updated_at'])

    log_action(
        user=user,
        action='PAYMENT_SUBMITTED',
        entity_type='Payment',
        entity_id=str(payment.id),
        new_value={
            'customer': str(customer.id),
            'lottery': str(lottery.id),
            'reference': ref,
            'amount': str(submitted_amount),
            'tickets': [r.ticket.ticket_number for r in reservations],
            'receipt_reference_match': payment.receipt_reference_match,
        },
        ip_address=ip_address,
    )

    logger.info(
        'Payment submitted: %s by Customer %s for %d tickets in Lottery %s',
        ref, customer.full_name, len(reservations), lottery.name,
    )

    # Automated bank ledger verification
    # Skip auto-verification if receipt cross-validation flagged it as suspicious
    auto_verify_enabled = getattr(settings, 'PAYMENT_AUTO_VERIFY_ENABLED', True)
    if receipt_suspicious:
        logger.info(
            'Skipping auto-verification for payment %s due to suspicious receipt '
            '(reference mismatch). Queued for staff manual review.',
            ref,
        )
        payment.auto_verification_status = 'SKIPPED_SUSPICIOUS'
        payment.verification_error = (
            'Auto-verification skipped: uploaded receipt does not match '
            'the provided transaction reference. Flagged for staff review.'
        )
        payment.save(
            update_fields=['auto_verification_status', 'verification_error', 'updated_at']
        )
    elif auto_verify_enabled and TransactionVerifier.is_method_supported(payment_method):
        try:
            verify_result = TransactionVerifier.verify(
                payment_method=payment_method,
                reference=ref,
                expected_amount=submitted_amount,
            )
            payment.auto_verification_status = verify_result.status
            payment.verification_data = verify_result.to_dict()
            payment.verification_error = verify_result.error_message

            if verify_result.is_verified:
                payment.is_auto_verified = True
                payment.save(
                    update_fields=['is_auto_verified', 'auto_verification_status', 'verification_data', 'verification_error', 'updated_at']
                )
                payment = approve_payment(
                    payment=payment,
                    staff_user=None,
                    admin_notes=f'[AUTO-VERIFIED via Bank REST API] Confirmed {submitted_amount} ETB via {payment_method.upper()}.',
                    ip_address=ip_address,
                )
                logger.info('Payment %s automatically approved via bank verification API', ref)
            else:
                payment.save(
                    update_fields=['is_auto_verified', 'auto_verification_status', 'verification_data', 'verification_error', 'updated_at']
                )
                logger.info(
                    'Payment %s not auto-verified (%s): %s. Queued for staff review.',
                    ref, verify_result.status, verify_result.error_message,
                )
        except Exception as exc:
            logger.exception('Auto-verification error for payment %s: %s', ref, exc)
            payment.auto_verification_status = 'ERROR'
            payment.verification_error = str(exc)
            payment.save(update_fields=['auto_verification_status', 'verification_error', 'updated_at'])

    return payment


def approve_payment(
    payment: Payment,
    staff_user,
    admin_notes: str = '',
    ip_address: Optional[str] = None,
) -> Payment:
    """
    Approve a pending payment.

    Atomically:
    1. Locks Payment, linked Reservations, and linked Tickets.
    2. Verifies payment is PENDING.
    3. Verifies all reservations are ACTIVE and tickets are RESERVED.
    4. Sets Payment status -> APPROVED, reviewed_by, reviewed_at.
    5. Sets Reservations status -> CONFIRMED.
    6. Sets Tickets status -> SOLD, customer = payment.customer, sold_at = now.
    7. Records audit log.

    Returns the updated Payment.
    """
    now = timezone.now()

    with transaction.atomic():
        locked_payment = Payment.objects.select_for_update().get(id=payment.id)

        if locked_payment.status != PaymentStatus.PENDING:
            raise ValueError(
                f'Cannot approve payment with status "{locked_payment.get_status_display()}". '
                'Only pending payments can be approved.'
            )

        reservations = list(locked_payment.reservations.select_for_update().all())
        if not reservations:
            raise ValueError('Payment has no associated reservations.')

        # Validate reservations status
        for res in reservations:
            if res.status != ReservationStatus.ACTIVE:
                raise ValueError(
                    f'Reservation {res.id} is no longer active (status: {res.get_status_display()}).'
                )

        # Lock and validate tickets
        ticket_ids = [r.ticket_id for r in reservations]
        tickets = list(Ticket.objects.select_for_update().filter(id__in=ticket_ids))

        for ticket in tickets:
            if ticket.status != TicketStatus.RESERVED:
                raise ValueError(
                    f'Ticket {ticket.ticket_number} is not reserved (status: {ticket.get_status_display()}).'
                )

        # 1. Update Payment
        locked_payment.status = PaymentStatus.APPROVED
        locked_payment.reviewed_by = staff_user
        locked_payment.reviewed_at = now
        if admin_notes:
            locked_payment.admin_notes = admin_notes
        locked_payment.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'admin_notes', 'updated_at'])

        # 2. Update Reservations -> CONFIRMED
        for res in reservations:
            res.status = ReservationStatus.CONFIRMED
            res.save(update_fields=['status'])

        # 3. Update Tickets -> SOLD
        for ticket in tickets:
            ticket.status = TicketStatus.SOLD
            ticket.customer = locked_payment.customer
            ticket.save(update_fields=['status', 'customer', 'updated_at'])

    approver_label = staff_user.email if staff_user else 'System (Auto-Verifier)'
    log_action(
        user=staff_user,
        action='PAYMENT_APPROVED',
        entity_type='Payment',
        entity_id=str(locked_payment.id),
        old_value={'status': PaymentStatus.PENDING},
        new_value={
            'status': PaymentStatus.APPROVED,
            'approved_by': approver_label,
            'sold_tickets': [t.ticket_number for t in tickets],
        },
        ip_address=ip_address,
    )

    logger.info(
        'Payment %s APPROVED by %s. %d tickets marked SOLD.',
        locked_payment.transaction_reference, approver_label, len(tickets),
    )

    try:
        from apps.notifications.services import notify_payment_approved
        notify_payment_approved(locked_payment)
    except Exception as e:
        logger.warning('Failed to dispatch payment approved notification: %s', e)

    return locked_payment


def verify_payment_now(
    payment: Payment,
    staff_user=None,
    ip_address: Optional[str] = None,
) -> Payment:
    """
    Manually trigger bank ledger verification via REST API for a pending payment.
    If confirmed, atomically approves the payment.
    Returns the updated Payment instance.
    """
    if payment.status != PaymentStatus.PENDING:
        raise ValueError(
            f'Only pending payments can be verified against bank records '
            f'(current status: "{payment.get_status_display()}").'
        )

    verify_result = TransactionVerifier.verify(
        payment_method=payment.payment_method,
        reference=payment.transaction_reference,
        expected_amount=payment.amount,
    )

    payment.auto_verification_status = verify_result.status
    payment.verification_data = verify_result.to_dict()
    payment.verification_error = verify_result.error_message

    if verify_result.is_verified:
        payment.is_auto_verified = True
        payment.save(
            update_fields=['is_auto_verified', 'auto_verification_status', 'verification_data', 'verification_error', 'updated_at']
        )
        approved_by_label = staff_user.email if staff_user else 'System'
        return approve_payment(
            payment=payment,
            staff_user=staff_user,
            admin_notes=f'[AUTO-VERIFIED via Bank REST API] Confirmed by {approved_by_label}.',
            ip_address=ip_address,
        )
    else:
        payment.save(
            update_fields=['is_auto_verified', 'auto_verification_status', 'verification_data', 'verification_error', 'updated_at']
        )
        return payment


def reject_payment(
    payment: Payment,
    staff_user,
    rejection_reason: str,
    admin_notes: str = '',
    ip_address: Optional[str] = None,
) -> Payment:
    """
    Reject a pending payment.

    Atomically:
    1. Locks Payment, linked Reservations, and linked Tickets.
    2. Verifies payment is PENDING.
    3. Sets Payment status -> REJECTED, rejection_reason, reviewed_by, reviewed_at.
    4. Sets Reservations status -> CANCELLED.
    5. Releases Tickets -> status AVAILABLE, customer = None.
    6. Records audit log.

    Returns the updated Payment.
    """
    reason = rejection_reason.strip()
    if not reason:
        raise ValueError('A rejection reason must be provided.')

    now = timezone.now()

    with transaction.atomic():
        locked_payment = Payment.objects.select_for_update().get(id=payment.id)

        if locked_payment.status != PaymentStatus.PENDING:
            raise ValueError(
                f'Cannot reject payment with status "{locked_payment.get_status_display()}". '
                'Only pending payments can be rejected.'
            )

        reservations = list(locked_payment.reservations.select_for_update().all())
        ticket_ids = [r.ticket_id for r in reservations]
        tickets = list(Ticket.objects.select_for_update().filter(id__in=ticket_ids))

        # 1. Update Payment
        locked_payment.status = PaymentStatus.REJECTED
        locked_payment.rejection_reason = reason
        locked_payment.reviewed_by = staff_user
        locked_payment.reviewed_at = now
        if admin_notes:
            locked_payment.admin_notes = admin_notes
        locked_payment.save(
            update_fields=['status', 'rejection_reason', 'reviewed_by', 'reviewed_at', 'admin_notes', 'updated_at']
        )

        # 2. Update Reservations -> CANCELLED
        for res in reservations:
            if res.status == ReservationStatus.ACTIVE:
                res.status = ReservationStatus.CANCELLED
                res.save(update_fields=['status'])

        # 3. Release Tickets -> AVAILABLE
        for ticket in tickets:
            if ticket.status == TicketStatus.RESERVED:
                ticket.status = TicketStatus.AVAILABLE
                ticket.customer = None
                ticket.save(update_fields=['status', 'customer', 'updated_at'])

    log_action(
        user=staff_user,
        action='PAYMENT_REJECTED',
        entity_type='Payment',
        entity_id=str(locked_payment.id),
        old_value={'status': PaymentStatus.PENDING},
        new_value={
            'status': PaymentStatus.REJECTED,
            'rejection_reason': reason,
            'rejected_by': staff_user.email,
            'released_tickets': [t.ticket_number for t in tickets],
        },
        ip_address=ip_address,
    )

    logger.info(
        'Payment %s REJECTED by %s. Reason: %s. %d tickets released.',
        locked_payment.transaction_reference, staff_user.email, reason, len(tickets),
    )

    try:
        from apps.notifications.services import notify_payment_rejected
        notify_payment_rejected(locked_payment, reason)
    except Exception as e:
        logger.warning('Failed to dispatch payment rejected notification: %s', e)

    return locked_payment


def get_payment_stats(lottery: Optional[Lottery] = None) -> dict:
    """
    Get aggregated payment statistics, optionally filtered by lottery.
    """
    qs = Payment.objects.all()
    if lottery:
        qs = qs.filter(lottery=lottery)

    from django.db.models import Count, Sum

    total_count = qs.count()
    pending_count = qs.filter(status=PaymentStatus.PENDING).count()
    approved_count = qs.filter(status=PaymentStatus.APPROVED).count()
    rejected_count = qs.filter(status=PaymentStatus.REJECTED).count()

    approved_revenue = (
        qs.filter(status=PaymentStatus.APPROVED).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    )
    pending_amount = (
        qs.filter(status=PaymentStatus.PENDING).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    )

    return {
        'total_payments': total_count,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'approved_revenue': str(approved_revenue),
        'pending_amount': str(pending_amount),
    }
