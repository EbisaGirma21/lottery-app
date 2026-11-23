"""
Core lottery business models: Lottery, Customer, and PaymentInstruction.
"""
from decimal import Decimal
import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify


class LotteryStatus(models.TextChoices):
    """Status lifecycle for a lottery."""
    DRAFT = 'draft', 'Draft'
    OPEN = 'open', 'Open'
    PAUSED = 'paused', 'Paused'
    CLOSED = 'closed', 'Closed'
    DRAWN = 'drawn', 'Drawn'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'


# Valid state transitions for lottery status
LOTTERY_STATUS_TRANSITIONS = {
    LotteryStatus.DRAFT: [LotteryStatus.OPEN, LotteryStatus.CANCELLED],
    LotteryStatus.OPEN: [LotteryStatus.PAUSED, LotteryStatus.CLOSED, LotteryStatus.CANCELLED],
    LotteryStatus.PAUSED: [LotteryStatus.OPEN, LotteryStatus.CLOSED, LotteryStatus.CANCELLED],
    LotteryStatus.CLOSED: [LotteryStatus.DRAWN],
    LotteryStatus.DRAWN: [LotteryStatus.COMPLETED],
    LotteryStatus.COMPLETED: [],
    LotteryStatus.CANCELLED: [],
}


class Lottery(models.Model):
    """
    Represents a single lottery event with configurable ticket count, pricing,
    and three prize positions.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    description = models.TextField(blank=True, default='')

    # Ticket configuration
    ticket_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Price per ticket in the configured currency.',
    )
    total_numbers = models.PositiveIntegerField(
        validators=[MinValueValidator(3)],
        help_text='Total number of tickets for this lottery (minimum 3 for a draw).',
    )

    # Important dates
    start_date = models.DateTimeField(help_text='When the lottery opens for ticket sales.')
    closing_date = models.DateTimeField(help_text='Deadline for purchasing tickets.')
    draw_date = models.DateTimeField(help_text='When the draw will take place.')

    # 1st Prize
    first_prize_name = models.CharField(max_length=255)
    first_prize_description = models.TextField(blank=True, default='')
    first_prize_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # 2nd Prize
    second_prize_name = models.CharField(max_length=255)
    second_prize_description = models.TextField(blank=True, default='')
    second_prize_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # 3rd Prize
    third_prize_name = models.CharField(max_length=255)
    third_prize_description = models.TextField(blank=True, default='')
    third_prize_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Reservation settings
    reservation_hours = models.PositiveIntegerField(
        default=48,
        help_text='Number of hours a ticket reservation remains active.',
    )
    max_tickets_per_customer = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Maximum tickets one customer can purchase. NULL = unlimited.',
    )

    # Status & tracking
    status = models.CharField(
        max_length=20,
        choices=LotteryStatus.choices,
        default=LotteryStatus.DRAFT,
        db_index=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_lotteries',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lotteries'
        ordering = ['-created_at']
        verbose_name = 'Lottery'
        verbose_name_plural = 'Lotteries'
        indexes = [
            models.Index(fields=['status', 'closing_date'], name='idx_lottery_status_close'),
            models.Index(fields=['draw_date'], name='idx_lottery_draw_date'),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            # Ensure uniqueness
            original_slug = self.slug
            counter = 1
            while Lottery.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f'{original_slug}-{counter}'
                counter += 1
        super().save(*args, **kwargs)

    @property
    def ticket_number_width(self) -> int:
        """Number of digits for zero-padded ticket numbers."""
        return len(str(self.total_numbers))

    def format_ticket_number(self, number: int) -> str:
        """Format a ticket number with proper zero-padding for this lottery."""
        return str(number).zfill(self.ticket_number_width)

    def can_transition_to(self, new_status: str) -> bool:
        """Check if the lottery can transition to the given status."""
        allowed = LOTTERY_STATUS_TRANSITIONS.get(self.status, [])
        return new_status in allowed


class CustomerStatus(models.TextChoices):
    """Customer account status."""
    ACTIVE = 'active', 'Active'
    BLOCKED = 'blocked', 'Blocked'


class Customer(models.Model):
    """
    A lottery customer, identified primarily by their Telegram account.
    Separate from staff Users.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(
        max_length=20,
        db_index=True,
        help_text='Normalized phone number (e.g., +251912345678).',
    )
    telegram_user_id = models.BigIntegerField(
        unique=True,
        db_index=True,
        help_text='Unique Telegram user ID.',
    )
    telegram_username = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='Telegram @username (may change).',
    )
    status = models.CharField(
        max_length=20,
        choices=CustomerStatus.choices,
        default=CustomerStatus.ACTIVE,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'customers'
        ordering = ['-created_at']
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
        indexes = [
            models.Index(fields=['phone_number'], name='idx_customer_phone'),
            models.Index(fields=['telegram_user_id'], name='idx_customer_telegram'),
        ]

    def __str__(self) -> str:
        return f'{self.full_name} ({self.phone_number})'

    @staticmethod
    def normalize_phone(phone: str) -> str:
        """
        Normalize an Ethiopian phone number to international format.
        Handles: 0912345678, +251912345678, 251912345678, 912345678
        """
        phone = phone.strip().replace(' ', '').replace('-', '')
        if phone.startswith('+'):
            return phone
        if phone.startswith('0') and len(phone) == 10:
            return f'+251{phone[1:]}'
        if phone.startswith('251') and len(phone) == 12:
            return f'+{phone}'
        if phone.startswith('9') and len(phone) == 9:
            return f'+251{phone}'
        return phone


class PaymentMethod(models.TextChoices):
    """Supported manual payment channels."""
    TELEBIRR = 'telebirr', 'Telebirr'
    CBE = 'cbe', 'CBE'
    OTHER = 'other', 'Other'


class PaymentInstruction(models.Model):
    """
    Configurable payment instructions for a lottery.
    Displayed to customers so they know where to send payment.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lottery = models.ForeignKey(
        Lottery,
        on_delete=models.CASCADE,
        related_name='payment_instructions',
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
    )
    account_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=100)
    additional_info = models.TextField(
        blank=True,
        default='',
        help_text='Extra instructions for this payment method.',
    )
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'payment_instructions'
        ordering = ['display_order']
        verbose_name = 'Payment Instruction'
        verbose_name_plural = 'Payment Instructions'

    def __str__(self) -> str:
        return f'{self.lottery.name} — {self.get_payment_method_display()}'
