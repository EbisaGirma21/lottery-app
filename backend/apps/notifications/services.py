"""
Notification dispatching services for Telegram customer alerts and staff notifications.
"""
import logging
from typing import List, Optional

from django.utils import timezone

from apps.lotteries.models import Customer, Lottery
from apps.notifications.models import (
    Notification,
    NotificationChannel,
    NotificationStatus,
    NotificationType,
)
from apps.payments.models import Payment
from apps.winners.models import Winner

logger = logging.getLogger(__name__)


def send_telegram_bot_message(chat_id: int, text: str) -> bool:
    """Safely dispatch Telegram message to customer chat if bot token configured."""
    from apps.telegram_bot.config import get_bot_token
    token = get_bot_token()
    if not token or 'ABCdef' in token or 'your-' in token:
        return False

    import json
    import urllib.parse
    import urllib.request

    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "HTML"}).encode('utf-8')
        req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception as e:
        logger.warning("Could not send Telegram message to chat_id=%s: %s", chat_id, str(e))
        return False


def dispatch_notification(
    notification_type: str,
    title: str,
    message: str,
    customer: Optional[Customer] = None,
    user=None,
    channel: str = NotificationChannel.TELEGRAM,
    metadata: Optional[dict] = None,
) -> Notification:
    """
    Persist and dispatch a notification.
    """
    notification = Notification.objects.create(
        customer=customer,
        user=user,
        channel=channel,
        notification_type=notification_type,
        title=title,
        message=message,
        status=NotificationStatus.SENT,  # Ready / Dispatched
        sent_at=timezone.now(),
        metadata=metadata or {},
    )

    if customer and customer.telegram_user_id and channel == NotificationChannel.TELEGRAM:
        full_text = f"🔔 <b>{title}</b>\n\n{message}"
        send_telegram_bot_message(customer.telegram_user_id, full_text)

    recipient = customer.full_name if customer else (user.email if user else 'System')
    logger.info(
        'Dispatched notification [%s] to %s: "%s"',
        notification_type, recipient, title,
    )
    return notification


def notify_reservation_created(
    customer: Customer,
    lottery: Lottery,
    ticket_numbers: List[str],
    expires_at,
) -> Notification:
    """Alert customer via Telegram that tickets have been reserved."""
    deadline_str = expires_at.strftime('%Y-%m-%d %H:%M UTC')
    tickets_str = ', '.join(f'#{t}' for t in ticket_numbers)

    title = f'Tickets Reserved: {lottery.name}'
    message = (
        f'Hello {customer.full_name},\n\n'
        f'You have reserved {len(ticket_numbers)} ticket(s) ({tickets_str}) for "{lottery.name}".\n\n'
        f'Please complete your payment before {deadline_str} and submit your transaction reference number '
        f'to confirm your purchase.'
    )

    return dispatch_notification(
        customer=customer,
        notification_type=NotificationType.RESERVATION_CREATED,
        title=title,
        message=message,
        metadata={
            'lottery_id': str(lottery.id),
            'ticket_numbers': ticket_numbers,
            'expires_at': expires_at.isoformat(),
        },
    )


def notify_payment_approved(payment: Payment) -> Notification:
    """Alert customer via Telegram that manual payment was verified and approved."""
    lottery = payment.lottery
    tickets = [r.ticket.ticket_number for r in payment.reservations.all()]
    tickets_str = ', '.join(f'#{t}' for t in tickets)

    title = f'Payment Approved! Tickets Confirmed'
    message = (
        f'Great news, {payment.customer.full_name}!\n\n'
        f'Your payment (Ref: {payment.transaction_reference}) for {len(tickets)} ticket(s) '
        f'({tickets_str}) in "{lottery.name}" has been verified and APPROVED.\n\n'
        f'These tickets are now officially registered under your name. Good luck in the upcoming draw!'
    )

    return dispatch_notification(
        customer=payment.customer,
        notification_type=NotificationType.PAYMENT_APPROVED,
        title=title,
        message=message,
        metadata={
            'payment_id': str(payment.id),
            'lottery_id': str(lottery.id),
            'tickets': tickets,
            'reference': payment.transaction_reference,
        },
    )


def notify_payment_rejected(payment: Payment, reason: str) -> Notification:
    """Alert customer via Telegram that manual payment was rejected with reason."""
    lottery = payment.lottery

    title = f'Payment Verification Failed'
    message = (
        f'Notice for {payment.customer.full_name}:\n\n'
        f'Your payment submission (Ref: {payment.transaction_reference}) for "{lottery.name}" '
        f'could not be verified and was REJECTED.\n\n'
        f'Reason: {reason}\n\n'
        f'Your ticket reservations have been released. If you believe this is an error, '
        f'please contact support with your payment receipt.'
    )

    return dispatch_notification(
        customer=payment.customer,
        notification_type=NotificationType.PAYMENT_REJECTED,
        title=title,
        message=message,
        metadata={
            'payment_id': str(payment.id),
            'lottery_id': str(lottery.id),
            'reference': payment.transaction_reference,
            'reason': reason,
        },
    )


def notify_winner_announced(winner: Winner) -> Notification:
    """Alert a winning customer that their ticket won a prize!"""
    customer = winner.customer
    lottery = winner.lottery

    title = f'CONGRATULATIONS! You Won {winner.get_position_display()}!'
    message = (
        f'🎉 AMAZING NEWS, {customer.full_name}! 🎉\n\n'
        f'Your ticket #{winner.ticket.ticket_number} won the {winner.get_position_display()} '
        f'in "{lottery.name}"!\n\n'
        f'Prize: {winner.prize_name} (Value: ETB {winner.prize_value:,.2f})\n\n'
        f'Our support team will contact you shortly to coordinate your prize handover. '
        f'You can also visit our office with your identification to claim your prize.'
    )

    return dispatch_notification(
        customer=customer,
        notification_type=NotificationType.WINNER_ANNOUNCED,
        title=title,
        message=message,
        metadata={
            'winner_id': str(winner.id),
            'lottery_id': str(lottery.id),
            'ticket_number': winner.ticket.ticket_number,
            'position': winner.position,
            'prize_name': winner.prize_name,
            'prize_value': str(winner.prize_value),
        },
    )
