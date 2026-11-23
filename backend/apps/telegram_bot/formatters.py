"""
HTML Message formatters for Telegram Customer Bot.
Provides rich, responsive typography with emojis and clear information hierarchy.
"""
from datetime import datetime
from django.utils import timezone


def format_welcome(first_name: str, has_phone: bool = False) -> str:
    """Format welcome message on /start."""
    phone_prompt = (
        "\n\n📱 <i>Tip: Tap below to share your phone number so our prize dispatch "
        "team can reach you if you win!</i>"
        if not has_phone
        else ""
    )
    return (
        f"👋 <b>Welcome to the National Lottery Platform, {first_name}!</b>\n\n"
        "Here you can browse active lotteries, reserve dynamic ticket numbers, "
        "and securely submit your payment reference for staff verification.\n\n"
        "🎯 <b>How It Works:</b>\n"
        "1. <b>Browse Lotteries</b> — choose an active lottery and pick your lucky numbers.\n"
        "2. <b>Reserve</b> — tickets are held for you for <b>48 hours</b>.\n"
        "3. <b>Pay Manually</b> — transfer via Telebirr, CBE, or other bank channels.\n"
        "4. <b>Submit Reference</b> — send us your transaction reference code.\n"
        "5. <b>Staff Verification</b> — authorized staff manually verifies your deposit.\n"
        "6. <b>Win Big</b> — watch the live cryptographic draw for 1st, 2nd & 3rd prizes!"
        f"{phone_prompt}\n\n"
        "👇 <i>Use the menu buttons below to get started:</i>"
    )


def format_help() -> str:
    """Format /help guide."""
    return (
        "ℹ️ <b>Lottery System Help & Guide</b>\n\n"
        "<b>Available Commands:</b>\n"
        "• /lotteries — Browse active lotteries & prize pools\n"
        "• /my_tickets — View your reservations & confirmed tickets\n"
        "• /pay — Submit your payment reference for verification\n"
        "• /winners — View past draw results & winning numbers\n"
        "• /help — Show this help guide\n\n"
        "🔒 <b>Manual Payment & Verification Security:</b>\n"
        "We do NOT use automated online credit card processing. "
        "You pay directly using official Ethiopian financial services:\n"
        "• <b>Telebirr</b>\n"
        "• <b>Commercial Bank of Ethiopia (CBE)</b>\n"
        "• <b>CBE Birr</b>\n"
        "• <b>Awash Bank</b>\n"
        "• <b>Bank of Abyssinia</b>\n\n"
        "Once you submit your reference number, our verification officers confirm "
        "the deposit on our bank ledger before issuing your final tickets. "
        "This ensures 100% transparency and security.\n\n"
        "📞 <b>Customer Support:</b> @LotterySupportBot"
    )


def format_lottery_card(lottery) -> str:
    """Format detailed information for a single lottery."""
    title = getattr(lottery, 'name', getattr(lottery, 'title', 'Lottery'))
    total = getattr(lottery, 'total_numbers', 0)
    
    # Compute counts if not already annotated
    if hasattr(lottery, 'available_tickets_count'):
        available = lottery.available_tickets_count
        sold = lottery.sold_tickets_count
        reserved = lottery.reserved_tickets_count
    else:
        from apps.tickets.models import Ticket, TicketStatus
        available = Ticket.objects.filter(lottery=lottery, status=TicketStatus.AVAILABLE).count()
        sold = Ticket.objects.filter(lottery=lottery, status__in=[TicketStatus.SOLD, TicketStatus.WINNER]).count()
        reserved = Ticket.objects.filter(lottery=lottery, status=TicketStatus.RESERVED).count()

    pct_sold = round((sold / total) * 100, 1) if total > 0 else 0

    draw_date_str = (
        lottery.draw_date.strftime("%B %d, %Y at %I:%M %p")
        if lottery.draw_date
        else "TBA"
    )

    def _fmt_prize(medal, name, desc, val):
        try:
            v = float(val or 0)
        except (ValueError, TypeError):
            v = 0
        desc_str = f" <i>({desc})</i>" if desc else ""
        if v > 0:
            return f"  {medal} <b>{name}:</b>{desc_str} {v:,.2f} ETB"
        return f"  {medal} <b>{name}:</b>{desc_str} 🎁 Physical Prize"

    first_val = getattr(lottery, 'first_prize_value', getattr(lottery, 'first_prize', 0))
    second_val = getattr(lottery, 'second_prize_value', getattr(lottery, 'second_prize', 0))
    third_val = getattr(lottery, 'third_prize_value', getattr(lottery, 'third_prize', 0))
    first_name = getattr(lottery, 'first_prize_name', '1st Prize')
    second_name = getattr(lottery, 'second_prize_name', '2nd Prize')
    third_name = getattr(lottery, 'third_prize_name', '3rd Prize')
    first_desc = getattr(lottery, 'first_prize_description', '')
    second_desc = getattr(lottery, 'second_prize_description', '')
    third_desc = getattr(lottery, 'third_prize_description', '')

    p1_text = _fmt_prize("🥇", first_name, first_desc, first_val)
    p2_text = _fmt_prize("🥈", second_name, second_desc, second_val)
    p3_text = _fmt_prize("🥉", third_name, third_desc, third_val)

    return (
        f"🎟️ <b>{title}</b>\n\n"
        f"📝 <i>{lottery.description or 'Official national lottery draw.'}</i>\n\n"
        f"💰 <b>Price Per Ticket:</b> {lottery.ticket_price} ETB\n"
        f"📅 <b>Draw Date:</b> {draw_date_str}\n\n"
        f"🏆 <b>Prize Pool (Three Winning Positions):</b>\n"
        f"{p1_text}\n"
        f"{p2_text}\n"
        f"{p3_text}\n\n"
        f"📊 <b>Ticket Availability:</b>\n"
        f"  • Total Capacity: <b>{total:,}</b> tickets\n"
        f"  • Available: <b>{available:,}</b>\n"
        f"  • Sold: <b>{sold:,}</b> ({pct_sold}%)\n"
        f"  • In Reservation: <b>{reserved:,}</b>\n\n"
        f"⏱️ <i>Reservations are held for {lottery.reservation_hours} hours.</i>"
    )


def format_reservation_confirmed(reservations, payment_instructions=None) -> str:
    """Format reservation receipt with payment instructions."""
    if not isinstance(reservations, list):
        reservations = [reservations]

    res = reservations[0]
    lottery = res.lottery
    lottery_name = getattr(lottery, 'name', getattr(lottery, 'title', 'Lottery'))
    ticket_numbers = [f"#{r.ticket.ticket_number}" for r in reservations]
    tickets_str = ", ".join(ticket_numbers)
    if len(tickets_str) > 120:
        tickets_str = f"{len(ticket_numbers)} tickets ({', '.join(ticket_numbers[:5])}...)"

    total_price = sum(r.lottery.ticket_price for r in reservations)
    exp_str = res.expires_at.strftime("%a, %d %b %Y %H:%M UTC")

    instructions_text = ""
    if payment_instructions:
        instructions_text = "\n\n💳 <b>How to Pay (Supported Bank Channels):</b>\n"
        for pi in payment_instructions:
            channel_name = pi.get_payment_method_display() if hasattr(pi, 'get_payment_method_display') else pi.payment_method
            instructions_text += (
                f"• <b>{channel_name}:</b> "
                f"Account: <code>{pi.account_number}</code> "
                f"({pi.account_name})\n"
            )
            extra = getattr(pi, 'additional_info', getattr(pi, 'instructions', ''))
            if extra:
                instructions_text += f"  <i>Note: {extra}</i>\n"

    res_ids_str = ", ".join(str(r.id)[:8] for r in reservations)

    return (
        "🎉 <b>Tickets Reserved Successfully!</b>\n\n"
        f"🔖 <b>Reservation ID(s):</b> <code>{res_ids_str}</code>\n"
        f"🎟️ <b>Lottery:</b> {lottery_name}\n"
        f"🎫 <b>Numbers:</b> {tickets_str}\n"
        f"💵 <b>Total Amount:</b> <b>{total_price} ETB</b>\n"
        f"⏳ <b>Payment Deadline:</b> {exp_str}\n"
        f"<i>(Expires in {lottery.reservation_hours} hours if unpaid)</i>"
        f"{instructions_text}\n\n"
        "👉 <b>Next Step:</b> Transfer the total amount via any supported channel above, "
        "then tap <b>'Submit Payment'</b> or type /pay to enter your reference number!"
    )


def format_payment_submitted(payment) -> str:
    """Format notice after customer submits a manual payment reference."""
    created_str = payment.submitted_at.strftime("%B %d, %Y %I:%M %p") if hasattr(payment, 'submitted_at') else payment.created_at.strftime("%B %d, %Y %I:%M %p")

    if getattr(payment, 'status', None) == 'approved' and getattr(payment, 'is_auto_verified', False):
        return (
            "🎉 <b>Payment Automatically Verified & Confirmed!</b>\n\n"
            "⚡ <b>Status:</b> <b>INSTANT APPROVAL (Bank Ledger Confirmed)</b>\n"
            f"🔖 <b>Transaction Reference:</b> <code>{payment.transaction_reference}</code>\n"
            f"💳 <b>Payment Method:</b> {payment.get_payment_method_display()}\n"
            f"💵 <b>Amount Verified:</b> <b>{payment.amount} ETB</b>\n"
            f"📅 <b>Verified At:</b> {created_str}\n\n"
            "🎫 <b>Your Tickets Are Now Officially SOLD & Active!</b>\n"
            "Your transfer was confirmed directly against official bank records in real time. "
            "Your numbers are secured and entered into the draw!\n\n"
            "🍀 Best of luck! Type /mytickets anytime to view your portfolio."
        )

    return (
        "✅ <b>Payment Proof Submitted Successfully!</b>\n\n"
        f"🔖 <b>Transaction Reference:</b> <code>{payment.transaction_reference}</code>\n"
        f"💳 <b>Payment Method:</b> {payment.get_payment_method_display()}\n"
        f"💵 <b>Amount Claimed:</b> <b>{payment.amount} ETB</b>\n"
        f"📅 <b>Submitted At:</b> {created_str}\n\n"
        "⚠️ <b>Verification in Progress:</b>\n"
        "Per security regulations, all manual bank transfers are inspected and verified "
        "by our authorized finance officers against our official bank statement.\n\n"
        "🔔 You will receive an instant notification here once staff approves your payment. "
        "Upon approval, your tickets will be marked <b>SOLD</b> and fully guaranteed in the draw!"
    )


def format_my_tickets(active_res, pending_payments, sold_tickets) -> str:
    """Format customer's portfolio of tickets."""
    sections = []

    # 1. Confirmed / Sold Tickets
    if sold_tickets:
        sold_text = f"🎫 <b>Confirmed Tickets ({len(sold_tickets)}):</b>\n"
        for t in sold_tickets[:15]:
            l_name = getattr(t.lottery, 'name', getattr(t.lottery, 'title', 'Lottery'))
            if getattr(t, 'status', None) == 'winner':
                sold_text += f"  • <b>#{t.ticket_number}</b> — {l_name} 🏆 <b>WINNER!</b>\n"
            elif getattr(t.lottery, 'status', '') in ('drawn', 'completed'):
                sold_text += f"  • <b>#{t.ticket_number}</b> — {l_name} <i>(Drawn)</i>\n"
            else:
                draw_date = t.lottery.draw_date.strftime("%d %b %Y") if t.lottery.draw_date else "TBA"
                sold_text += f"  • <b>#{t.ticket_number}</b> — {l_name} (Draw: {draw_date})\n"
        if len(sold_tickets) > 15:
            sold_text += f"  <i>...and {len(sold_tickets) - 15} more</i>\n"
        sections.append(sold_text)

    # 2. Payments Pending Review
    if pending_payments:
        pend_text = f"⏳ <b>Under Verification Review ({len(pending_payments)}):</b>\n"
        for p in pending_payments:
            pend_text += (
                f"  • Ref: <code>{p.transaction_reference}</code> "
                f"({p.amount} ETB via {p.get_payment_method_display()})\n"
            )
        sections.append(pend_text)

    # 3. Active Unpaid Reservations
    if active_res:
        res_text = f"⏰ <b>Active Reservations ({len(active_res)}):</b>\n"
        for r in active_res:
            l_name = getattr(r.lottery, 'name', getattr(r.lottery, 'title', 'Lottery'))
            res_text += (
                f"  • #{r.ticket.ticket_number} ({l_name}) — {r.ticket.lottery.ticket_price} ETB "
                f"— Expires: {r.expires_at.strftime('%H:%M %d %b')}\n"
            )
        res_text += "\n<i>Tip: Run /pay to submit your transaction reference before expiration!</i>\n"
        sections.append(res_text)

    if not sections:
        return (
            "🎫 <b>My Tickets</b>\n\n"
            "You don't have any tickets or reservations yet.\n\n"
            "Tap /lotteries to pick your lucky numbers and enter the next draw!"
        )

    return "📊 <b>My Tickets & Reservations</b>\n\n" + "\n".join(sections)


def format_winners(draws) -> str:
    """Format winning draw announcements."""
    if not draws:
        return (
            "🏆 <b>Lottery Draw Winners</b>\n\n"
            "No lottery draws have been completed yet. Check back soon after our next live draw!"
        )

    text = "🏆 <b>Recent Lottery Draw Winners</b>\n\n"
    for d in draws[:5]:
        lottery = d.lottery
        l_name = getattr(lottery, 'name', getattr(lottery, 'title', 'Lottery'))
        draw_date_str = d.executed_at.strftime("%B %d, %Y")
        text += f"🎟️ <b>{l_name}</b> (Drawn: {draw_date_str})\n"

        winners = d.winners.all().order_by('position')
        for w in winners:
            medal = "🥇" if w.position == 1 else ("🥈" if w.position == 2 else "🥉")
            masked_name = w.masked_customer_name
            prize_title = w.prize_name or w.get_position_display()
            desc_str = f" - <i>{w.prize_description}</i>" if w.prize_description else ""
            try:
                v = float(w.prize_value or 0)
            except (ValueError, TypeError):
                v = 0
            val_str = f" ({v:,.2f} ETB)" if v > 0 else ""
            text += (
                f"  {medal} <b>{w.get_position_display()}:</b> Ticket #{w.ticket.ticket_number}\n"
                f"      🎁 <b>{prize_title}</b>{val_str}{desc_str} — {masked_name}\n"
            )
        text += "\n"

    return text
