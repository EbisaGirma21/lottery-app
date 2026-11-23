"""
Keyboard generators for Telegram Customer Bot.
Provides both ReplyKeyboardMarkup and InlineKeyboardMarkup.
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from apps.payments.models import PaymentMethod


def main_menu_reply_keyboard() -> ReplyKeyboardMarkup:
    """Persistent bottom reply keyboard for quick navigation."""
    keyboard = [
        ['🎟️ Active Lotteries', '🎫 My Tickets'],
        ['💳 Submit Payment', '🏆 Draw Results'],
        ['ℹ️ Help & Info'],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def contact_request_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard requesting customer's phone number via Telegram."""
    keyboard = [
        [KeyboardButton(text='📱 Share Phone Number', request_contact=True)],
        ['Skip for now'],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


def lotteries_inline_keyboard(lotteries) -> InlineKeyboardMarkup:
    """Inline keyboard listing all active lotteries."""
    keyboard = []
    for lottery in lotteries:
        l_name = getattr(lottery, 'name', getattr(lottery, 'title', 'Lottery'))
        keyboard.append([
            InlineKeyboardButton(
                text=f'🎟️ {l_name} — {lottery.ticket_price} ETB',
                callback_data=f'lottery:{lottery.id}',
            )
        ])
    return InlineKeyboardMarkup(keyboard)


def lottery_detail_keyboard(lottery_id: str) -> InlineKeyboardMarkup:
    """Action buttons for a selected lottery."""
    keyboard = [
        [
            InlineKeyboardButton(
                text='🎫 Pick Specific Numbers',
                callback_data=f'tickets:{lottery_id}:1',
            ),
        ],
        [
            InlineKeyboardButton(
                text='🎲 Quick Pick 1 Ticket',
                callback_data=f'quick_pick:{lottery_id}:1',
            ),
            InlineKeyboardButton(
                text='🎲 Quick Pick 5 Tickets',
                callback_data=f'quick_pick:{lottery_id}:5',
            ),
        ],
        [
            InlineKeyboardButton(
                text='🔙 Back to Lotteries',
                callback_data='list_lotteries',
            ),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def ticket_grid_keyboard(
    lottery_id: str,
    tickets,
    page: int = 1,
    total_pages: int = 1,
    selected_ids: set = None,
) -> InlineKeyboardMarkup:
    """
    Grid keyboard displaying available tickets in 4 columns without pagination.
    Reserved and sold tickets are not shown.
    """
    selected_ids = selected_ids or set()
    keyboard = []

    # 4 tickets per row in grid (four columns down)
    row = []
    for t in tickets:
        is_selected = str(t.id) in selected_ids
        icon = '✅ ' if is_selected else ''
        btn_text = f'{icon}#{t.ticket_number}'
        row.append(
            InlineKeyboardButton(
                text=btn_text,
                callback_data=f'pick:{t.id}',
            )
        )
        if len(row) == 4:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    # Reservation action row (no pagination buttons)
    action_row = []
    if selected_ids:
        action_row.append(
            InlineKeyboardButton(
                text=f'⚡ Confirm Reservation ({len(selected_ids)} tickets)',
                callback_data=f'confirm_reserve:{lottery_id}',
            )
        )
    action_row.append(
        InlineKeyboardButton(
            text='🔙 Back',
            callback_data=f'lottery:{lottery_id}',
        )
    )
    keyboard.append(action_row)

    return InlineKeyboardMarkup(keyboard)


def reservation_confirmed_keyboard(lottery_id: str) -> InlineKeyboardMarkup:
    """Action buttons after confirming ticket reservations."""
    keyboard = [
        [
            InlineKeyboardButton(text='💳 Submit Payment Now', callback_data=f'start_pay:{lottery_id}'),
        ],
        [
            InlineKeyboardButton(text='🎟️ My Tickets', callback_data='my_tickets'),
            InlineKeyboardButton(text='🎲 Browse Lotteries', callback_data='list_lotteries'),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def lottery_payment_selection_keyboard(lottery_map: dict) -> InlineKeyboardMarkup:
    """Inline buttons to choose which lottery's grouped reservations to pay for."""
    keyboard = []
    for lottery_id, res_list in lottery_map.items():
        if not res_list:
            continue
        first_res = res_list[0]
        l_name = getattr(first_res.lottery, 'name', getattr(first_res.lottery, 'title', 'Lottery'))
        total_price = sum(r.lottery.ticket_price for r in res_list)
        count = len(res_list)
        btn_text = f"🎟️ {l_name} ({count} ticket{'s' if count > 1 else ''} — {total_price} ETB)"
        keyboard.append([
            InlineKeyboardButton(
                text=btn_text,
                callback_data=f'pay_lottery:{lottery_id}',
            )
        ])
    keyboard.append([
        InlineKeyboardButton(text='❌ Cancel', callback_data='cancel_flow')
    ])
    return InlineKeyboardMarkup(keyboard)


def reservations_selection_keyboard(reservations) -> InlineKeyboardMarkup:
    """Inline buttons to choose which active reservation/lottery to pay for."""
    if isinstance(reservations, dict):
        return lottery_payment_selection_keyboard(reservations)

    keyboard = []
    for res in reservations:
        l_name = getattr(res.lottery, 'name', getattr(res.lottery, 'title', 'Lottery'))
        t_num = getattr(res.ticket, 'ticket_number', '000')
        price = getattr(res.lottery, 'ticket_price', 0)
        btn_text = f'🎟️ {l_name} — #{t_num} ({price} ETB)'
        keyboard.append([
            InlineKeyboardButton(
                text=btn_text,
                callback_data=f'pay_res:{res.id}',
            )
        ])
    keyboard.append([
        InlineKeyboardButton(text='❌ Cancel', callback_data='cancel_flow')
    ])
    return InlineKeyboardMarkup(keyboard)


def payment_methods_keyboard() -> InlineKeyboardMarkup:
    """Inline buttons to choose payment method channel."""
    keyboard = [
        [
            InlineKeyboardButton(text='📱 Telebirr', callback_data=f'pay_channel:{PaymentMethod.TELEBIRR}'),
            InlineKeyboardButton(text='🏦 CBE (Commercial Bank)', callback_data=f'pay_channel:{PaymentMethod.CBE}'),
        ],
        [
            InlineKeyboardButton(text='📲 CBE Birr', callback_data=f'pay_channel:{PaymentMethod.CBE_BIRR}'),
            InlineKeyboardButton(text='🏦 Awash Bank', callback_data=f'pay_channel:{PaymentMethod.AWASH}'),
        ],
        [
            InlineKeyboardButton(text='🏦 Bank of Abyssinia', callback_data=f'pay_channel:{PaymentMethod.BOA}'),
            InlineKeyboardButton(text='🌐 Other Channel', callback_data=f'pay_channel:{PaymentMethod.OTHER}'),
        ],
        [
            InlineKeyboardButton(text='❌ Cancel Payment', callback_data='cancel_flow')
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def skip_receipt_keyboard() -> InlineKeyboardMarkup:
    """Allows customer to proceed without screenshot proof."""
    keyboard = [
        [
            InlineKeyboardButton(text='⏩ Skip Receipt Photo', callback_data='skip_receipt'),
        ],
        [
            InlineKeyboardButton(text='❌ Cancel Payment', callback_data='cancel_flow'),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def cancel_inline_keyboard() -> InlineKeyboardMarkup:
    """Simple cancel button."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(text='❌ Cancel', callback_data='cancel_flow')]
    ])
