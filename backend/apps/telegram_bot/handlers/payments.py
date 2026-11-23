"""
ConversationHandler for manual payment submission and proof upload.
Enforces that customers submit manual references for human staff verification.
"""
from decimal import Decimal, InvalidOperation
import logging
from asgiref.sync import sync_to_async
from django.core.files.base import ContentFile
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from apps.lotteries.models import Customer, Lottery
from apps.payments.models import Payment, PaymentMethod, PaymentStatus
from apps.payments.services import submit_payment
from apps.reservations.models import Reservation, ReservationStatus
from apps.telegram_bot.config import (
    PAY_ENTER_AMOUNT,
    PAY_ENTER_REFERENCE,
    PAY_SELECT_METHOD,
    PAY_SELECT_RESERVATION,
    PAY_UPLOAD_PROOF,
)
from apps.telegram_bot.formatters import format_payment_submitted
from apps.telegram_bot.keyboards import (
    lottery_payment_selection_keyboard,
    main_menu_reply_keyboard,
    payment_methods_keyboard,
    reservations_selection_keyboard,
    skip_receipt_keyboard,
)

logger = logging.getLogger(__name__)


def sync_get_unpaid_reservations(telegram_user_id: int):
    """Retrieve customer and their active reservations that are not yet pending review."""
    customer = Customer.objects.filter(telegram_user_id=telegram_user_id).first()
    if not customer:
        return None, []

    # Active reservations that do NOT already have a PENDING payment
    active_res = list(
        Reservation.objects.filter(
            customer=customer,
            status=ReservationStatus.ACTIVE,
        )
        .exclude(payments__status=PaymentStatus.PENDING)
        .select_related('lottery', 'ticket', 'ticket__lottery')
        .order_by('-reserved_at')
    )
    return customer, active_res


def sync_is_reference_duplicate(reference: str) -> bool:
    """Check if transaction reference has already been submitted."""
    return Payment.objects.filter(transaction_reference__iexact=reference.strip()).exists()


def sync_process_payment_submission(
    telegram_user_id: int,
    lottery_id: str,
    reservation_ids: list,
    payment_method: str,
    reference: str,
    amount: Decimal,
    proof_bytes: bytes = None,
    proof_name: str = None,
):
    """Call backend submit_payment service."""
    customer = Customer.objects.get(telegram_user_id=telegram_user_id)
    lottery = Lottery.objects.get(pk=lottery_id)

    file_obj = None
    if proof_bytes and proof_name:
        file_obj = ContentFile(proof_bytes, name=proof_name)

    payment = submit_payment(
        customer=customer,
        lottery=lottery,
        reservation_ids=reservation_ids,
        payment_method=payment_method,
        transaction_reference=reference,
        amount=amount,
        payment_proof=file_obj,
    )
    payment.refresh_from_db()
    return payment


async def pay_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for /pay command, '💳 Submit Payment', or 'Pay Now' button."""
    query = update.callback_query
    if query:
        await query.answer()

    user = update.effective_user
    customer, reservations = await sync_to_async(sync_get_unpaid_reservations)(user.id)

    if not customer:
        msg = "Please start the bot first with /start to register your profile."
        if query:
            await update.effective_chat.send_message(msg, reply_markup=main_menu_reply_keyboard())
        else:
            await update.effective_message.reply_text(msg, reply_markup=main_menu_reply_keyboard())
        return ConversationHandler.END

    if not reservations:
        msg = (
            "ℹ️ <b>No Pending Reservations Found</b>\n\n"
            "You do not currently have any unpaid active reservations.\n\n"
            "Please tap /lotteries to browse active lotteries and pick your tickets first!"
        )
        if query:
            await update.effective_chat.send_message(
                msg,
                parse_mode=ParseMode.HTML,
                reply_markup=main_menu_reply_keyboard(),
            )
        else:
            await update.effective_message.reply_text(
                msg,
                parse_mode=ParseMode.HTML,
                reply_markup=main_menu_reply_keyboard(),
            )
        return ConversationHandler.END

    # Group reservations by lottery
    lottery_map = {}
    for r in reservations:
        lottery_map.setdefault(r.lottery_id, []).append(r)

    # Check if a specific lottery was requested (via callback query start_pay:<lottery_id>)
    specific_lottery_id = None
    if query and query.data and query.data.startswith('start_pay:'):
        target_id = query.data.split(':', 1)[1]
        for lid in lottery_map:
            if str(lid) == target_id:
                specific_lottery_id = lid
                break

    # If all reservations belong to a single lottery (or specific lottery requested), bundle them together!
    if specific_lottery_id or len(lottery_map) == 1:
        lottery_id = specific_lottery_id or list(lottery_map.keys())[0]
        lottery_res = lottery_map[lottery_id]
        total_amount = sum(r.lottery.ticket_price for r in lottery_res)
        numbers_str = ", ".join(f"#{r.ticket.ticket_number}" for r in lottery_res)

        context.user_data['pay_lottery_id'] = str(lottery_id)
        context.user_data['pay_reservation_ids'] = [str(r.id) for r in lottery_res]
        context.user_data['pay_expected_amount'] = str(total_amount)
        context.user_data['pay_numbers_str'] = numbers_str
        context.user_data['pay_ticket_count'] = len(lottery_res)

        l_name = getattr(lottery_res[0].lottery, 'name', getattr(lottery_res[0].lottery, 'title', 'Lottery'))

        prompt = (
            f"💳 <b>Payment for:</b> {l_name}\n"
            f"🎫 <b>Reserved Tickets:</b> {numbers_str} ({len(lottery_res)} tickets)\n"
            f"💵 <b>Total Amount Due:</b> <b>{total_amount} ETB</b>\n\n"
            "Please select the <b>Payment Method</b> you used to transfer the money:"
        )
        if query:
            await update.effective_chat.send_message(
                prompt,
                parse_mode=ParseMode.HTML,
                reply_markup=payment_methods_keyboard(),
            )
        else:
            await update.effective_message.reply_text(
                prompt,
                parse_mode=ParseMode.HTML,
                reply_markup=payment_methods_keyboard(),
            )
        return PAY_SELECT_METHOD

    # Multiple lotteries reserved — let customer select which lottery to pay for
    msg_multi = (
        "You have tickets reserved across multiple lotteries.\n"
        "Please select which lottery you wish to pay for (all reserved tickets in that lottery will be paid together):"
    )
    if query:
        await update.effective_chat.send_message(
            msg_multi,
            reply_markup=lottery_payment_selection_keyboard(lottery_map),
        )
    else:
        await update.effective_message.reply_text(
            msg_multi,
            reply_markup=lottery_payment_selection_keyboard(lottery_map),
        )
    return PAY_SELECT_RESERVATION


async def pay_select_reservation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles lottery selection when customer has reservations across multiple lotteries."""
    query = update.callback_query
    await query.answer()

    if query.data == 'cancel_flow':
        await query.edit_message_text("Payment submission cancelled.")
        return ConversationHandler.END

    lottery_id = None
    if query.data.startswith('pay_lottery:'):
        lottery_id = query.data.split(':', 1)[1]
    elif query.data.startswith('pay_res:'):
        # Fallback if old callback is triggered
        res_id = query.data.split(':', 1)[1]
        try:
            r = await sync_to_async(lambda: Reservation.objects.select_related('lottery').get(id=res_id))()
            lottery_id = str(r.lottery_id)
        except Exception:
            pass

    if not lottery_id:
        await query.edit_message_text("Selection not recognized. Please tap /pay to restart.")
        return ConversationHandler.END

    user = update.effective_user

    def get_user_lottery_reservations():
        return list(
            Reservation.objects.filter(
                customer__telegram_user_id=user.id,
                lottery_id=lottery_id,
                status=ReservationStatus.ACTIVE,
            )
            .exclude(payments__status=PaymentStatus.PENDING)
            .select_related('lottery', 'ticket')
            .order_by('reserved_at')
        )

    lottery_res = await sync_to_async(get_user_lottery_reservations)()
    if not lottery_res:
        await query.edit_message_text("No active unpaid reservations found for this lottery.")
        return ConversationHandler.END

    total_amount = sum(r.lottery.ticket_price for r in lottery_res)
    numbers_str = ", ".join(f"#{r.ticket.ticket_number}" for r in lottery_res)

    context.user_data['pay_lottery_id'] = str(lottery_id)
    context.user_data['pay_reservation_ids'] = [str(r.id) for r in lottery_res]
    context.user_data['pay_expected_amount'] = str(total_amount)
    context.user_data['pay_numbers_str'] = numbers_str
    context.user_data['pay_ticket_count'] = len(lottery_res)

    l_name = getattr(lottery_res[0].lottery, 'name', getattr(lottery_res[0].lottery, 'title', 'Lottery'))
    prompt = (
        f"💳 <b>Payment for:</b> {l_name}\n"
        f"🎫 <b>Reserved Tickets:</b> {numbers_str} ({len(lottery_res)} tickets)\n"
        f"💵 <b>Total Amount Due:</b> <b>{total_amount} ETB</b>\n\n"
        "Please select the <b>Payment Method</b> you used to transfer the money:"
    )
    await query.edit_message_text(
        prompt,
        parse_mode=ParseMode.HTML,
        reply_markup=payment_methods_keyboard(),
    )
    return PAY_SELECT_METHOD


async def pay_select_method(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles payment channel selection and prompts for receipt photo or PDF."""
    query = update.callback_query
    await query.answer()

    if query.data == 'cancel_flow':
        await query.edit_message_text("Payment submission cancelled.")
        return ConversationHandler.END

    if query.data.startswith('pay_channel:'):
        method = query.data.split(':', 1)[1]
        context.user_data['pay_method'] = method

        expected_amt = context.user_data.get('pay_expected_amount', '0.00')
        numbers_str = context.user_data.get('pay_numbers_str', '')
        count = context.user_data.get('pay_ticket_count', 1)

        channel_name = method.upper()
        if method == 'telebirr':
            channel_name = 'Telebirr 📱'
        elif method == 'cbe':
            channel_name = 'Commercial Bank of Ethiopia (CBE) 🏦'
        elif method == 'cbe_birr':
            channel_name = 'CBE Birr 📲'
        elif method == 'awash':
            channel_name = 'Awash Bank 🏦'
        elif method == 'boa':
            channel_name = 'Bank of Abyssinia 🏦'

        prompt = (
            f"✅ Payment method selected: <b>{channel_name}</b>\n"
            f"🎫 Tickets: <b>{numbers_str}</b> ({count} ticket{'s' if count > 1 else ''})\n"
            f"💵 <b>Total Amount Due:</b> <b>{expected_amt} ETB</b>\n\n"
            "📸 <b>Please send a SCREENSHOT or PDF of your payment receipt:</b>\n\n"
            f"Upload your transaction receipt (photo screenshot or PDF file) from <b>{channel_name}</b> showing the completed transfer.\n\n"
            "<i>(No need to enter amount or reference code — the exact total of <b>{expected_amt} ETB</b> is already recorded. Our finance officer will inspect your receipt directly in the Admin Panel to verify and activate all your tickets at once)</i>\n\n"
            "💬 <i>(Or type your transaction confirmation code if you do not have a receipt file)</i>"
        )
        await query.edit_message_text(prompt, parse_mode=ParseMode.HTML)
        return PAY_ENTER_REFERENCE

    return PAY_SELECT_METHOD


async def pay_upload_proof_direct(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles direct photo or PDF receipt upload right after selecting payment method."""
    msg = update.effective_message
    user = update.effective_user
    caption = (msg.caption or '').strip()

    method = context.user_data.get('pay_method', 'telebirr')
    expected_amount = Decimal(context.user_data.get('pay_expected_amount', '0'))

    prefix = 'TB' if 'telebirr' in method.lower() else ('CBE' if 'cbe' in method.lower() else 'PAY')
    if caption and len(caption) >= 4:
        ref = caption[:60]
    else:
        import uuid
        from django.utils import timezone
        ref = f"{prefix}-{timezone.now().strftime('%m%d%H%M')}-{uuid.uuid4().hex[:4].upper()}"

    proof_bytes = None
    filename = None

    if msg.photo:
        photo = msg.photo[-1]
        file_obj = await photo.get_file()
        photo_bytes = await file_obj.download_as_bytearray()
        proof_bytes = bytes(photo_bytes)
        filename = f"receipt_{ref}.jpg"
    elif msg.document:
        doc = msg.document
        file_obj = await doc.get_file()
        doc_bytes = await file_obj.download_as_bytearray()
        proof_bytes = bytes(doc_bytes)
        ext = doc.file_name.split('.')[-1] if (doc.file_name and '.' in doc.file_name) else 'pdf'
        filename = f"receipt_{ref}.{ext}"

    context.user_data['pay_reference'] = ref
    context.user_data['pay_amount'] = str(expected_amount)

    return await _finalize_submission(
        update, context, user.id, proof_bytes=proof_bytes, proof_name=filename
    )


async def pay_enter_reference(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives transaction reference number from user if typed manually, and auto-applies known amount."""
    ref = update.effective_message.text.strip()

    if len(ref) < 4:
        await update.effective_message.reply_text(
            "⚠️ Transaction reference is too short. Please enter the full reference number:"
        )
        return PAY_ENTER_REFERENCE

    is_duplicate = await sync_to_async(sync_is_reference_duplicate)(ref)
    if is_duplicate:
        await update.effective_message.reply_text(
            f"⚠️ Reference <code>{ref}</code> has already been submitted in our system!\n\n"
            "Please check your receipt and enter the correct reference, "
            "or type /cancel to abort.",
            parse_mode=ParseMode.HTML,
        )
        return PAY_ENTER_REFERENCE

    expected_amount = context.user_data.get('pay_expected_amount', '0.00')
    context.user_data['pay_reference'] = ref
    context.user_data['pay_amount'] = str(expected_amount)

    user = update.effective_user
    # Directly finalize submission since amount is already known!
    return await _finalize_submission(update, context, user.id)


async def pay_enter_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives and validates amount paid."""
    text = update.effective_message.text.strip().replace('ETB', '').replace(',', '').strip()

    try:
        amount = Decimal(text)
        if amount <= 0:
            raise ValueError()
    except (InvalidOperation, ValueError):
        await update.effective_message.reply_text(
            "⚠️ Invalid amount format. Please enter a valid positive number (e.g. 50.00):"
        )
        return PAY_ENTER_AMOUNT

    context.user_data['pay_amount'] = str(amount)

    prompt = (
        f"💵 Amount: <b>{amount} ETB</b> confirmed.\n\n"
        "📸 <b>Step 4 of 4: Proof of Payment (Optional)</b>\n\n"
        "Send a screenshot or photo of your payment receipt to help staff verify faster, "
        "or tap <b>'Skip Receipt Photo'</b> below to complete submission directly:"
    )
    await update.effective_message.reply_text(
        prompt,
        parse_mode=ParseMode.HTML,
        reply_markup=skip_receipt_keyboard(),
    )
    return PAY_UPLOAD_PROOF


async def pay_upload_proof(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles photo receipt upload."""
    photo = update.effective_message.photo[-1]  # Highest resolution
    user = update.effective_user

    file_obj = await photo.get_file()
    photo_bytes = await file_obj.download_as_bytearray()

    ref = context.user_data.get('pay_reference', 'ref')
    filename = f"tg_{ref}.jpg"

    return await _finalize_submission(
        update, context, user.id, proof_bytes=bytes(photo_bytes), proof_name=filename
    )


async def pay_skip_proof(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles skipping photo receipt."""
    query = update.callback_query
    await query.answer()

    if query.data == 'cancel_flow':
        await query.edit_message_text("Payment submission cancelled.")
        return ConversationHandler.END

    user = update.effective_user
    return await _finalize_submission(update, context, user.id)


async def _finalize_submission(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    telegram_user_id: int,
    proof_bytes: bytes = None,
    proof_name: str = None,
) -> int:
    """Internal helper to invoke backend payment submission and send feedback."""
    lottery_id = context.user_data.get('pay_lottery_id')
    reservation_ids = context.user_data.get('pay_reservation_ids', [])
    method = context.user_data.get('pay_method', PaymentMethod.OTHER)
    ref = context.user_data.get('pay_reference')
    amount = Decimal(context.user_data.get('pay_amount', '0'))

    try:
        payment = await sync_to_async(sync_process_payment_submission)(
            telegram_user_id=telegram_user_id,
            lottery_id=lottery_id,
            reservation_ids=reservation_ids,
            payment_method=method,
            reference=ref,
            amount=amount,
            proof_bytes=proof_bytes,
            proof_name=proof_name,
        )

        msg = await sync_to_async(format_payment_submitted)(payment)

        # Clear conversation state
        context.user_data.pop('pay_lottery_id', None)
        context.user_data.pop('pay_reservation_ids', None)
        context.user_data.pop('pay_method', None)
        context.user_data.pop('pay_reference', None)
        context.user_data.pop('pay_amount', None)
        context.user_data.pop('pay_expected_amount', None)

        if update.callback_query:
            await update.callback_query.edit_message_text(msg, parse_mode=ParseMode.HTML)
        else:
            await update.effective_message.reply_text(
                msg,
                parse_mode=ParseMode.HTML,
                reply_markup=main_menu_reply_keyboard(),
            )
    except Exception as exc:
        logger.exception("Error processing payment submission")
        err_msg = f"❌ <b>Error Submitting Payment:</b> {str(exc)}"
        if update.callback_query:
            await update.callback_query.edit_message_text(err_msg, parse_mode=ParseMode.HTML)
        else:
            await update.effective_message.reply_text(err_msg, parse_mode=ParseMode.HTML)

    return ConversationHandler.END


async def pay_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel payment conversation."""
    context.user_data.clear()
    msg = "❌ Payment submission cancelled. You can type /pay anytime before your reservation expires."
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(msg)
    else:
        await update.effective_message.reply_text(msg, reply_markup=main_menu_reply_keyboard())
    return ConversationHandler.END


def get_payment_conversation_handler() -> ConversationHandler:
    """Build and return the payment submission ConversationHandler."""
    return ConversationHandler(
        entry_points=[
            CommandHandler('pay', pay_start),
            MessageHandler(filters.Regex('^💳 Submit Payment$'), pay_start),
            CallbackQueryHandler(pay_start, pattern='^start_pay:'),
        ],
        states={
            PAY_SELECT_RESERVATION: [
                CallbackQueryHandler(pay_select_reservation, pattern='^(pay_lottery:|pay_res:|cancel_flow)'),
            ],
            PAY_SELECT_METHOD: [
                CallbackQueryHandler(pay_select_method, pattern='^(pay_channel:|cancel_flow)'),
            ],
            PAY_ENTER_REFERENCE: [
                MessageHandler(filters.PHOTO | filters.Document.ALL, pay_upload_proof_direct),
                MessageHandler(filters.TEXT & ~filters.COMMAND, pay_enter_reference),
            ],
            PAY_ENTER_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, pay_enter_amount),
            ],
            PAY_UPLOAD_PROOF: [
                MessageHandler(filters.PHOTO, pay_upload_proof),
                CallbackQueryHandler(pay_skip_proof, pattern='^(skip_receipt|cancel_flow)'),
            ],
        },
        fallbacks=[
            CommandHandler('cancel', pay_cancel),
            CallbackQueryHandler(pay_cancel, pattern='^cancel_flow$'),
        ],
        per_message=False,
    )
