"""
Models for manual payment submission and staff verification.
"""
from decimal import Decimal
import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class PaymentMethod(models.TextChoices):
    """Supported manual payment methods in Ethiopia."""
    TELEBIRR = 'telebirr', 'Telebirr'
    CBE = 'cbe', 'Commercial Bank of Ethiopia (CBE)'
    CBE_BIRR = 'cbe_birr', 'CBE Birr'
    AWASH = 'awash', 'Awash Bank'
    BOA = 'boa', 'Bank of Abyssinia'
    OTHER = 'other', 'Other'


class PaymentStatus(models.TextChoices):
    """Lifecycle status for manual payment verification."""
    PENDING = 'pending', 'Pending Verification'
    APPROVED = 'approved', 'Approved'
    REJECTED = 'rejected', 'Rejected'


class Payment(models.Model):
    """
    Record of a manual payment submitted by a customer for lottery ticket reservation(s).

    Staff must manually review the payment proof / reference number against bank records
    and either approve or reject the payment.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        'lotteries.Customer',
        on_delete=models.CASCADE,
        related_name='payments',
        help_text='Customer who submitted this payment.',
    )
    lottery = models.ForeignKey(
        'lotteries.Lottery',
        on_delete=models.PROTECT,
        related_name='payments',
        help_text='Lottery this payment is for.',
    )
    reservations = models.ManyToManyField(
        'reservations.Reservation',
        related_name='payments',
        help_text='Active reservations covered by this payment.',
    )
    payment_method = models.CharField(
        max_length=50,
        choices=PaymentMethod.choices,
        help_text='Payment method used by the customer.',
    )
    transaction_reference = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text='Bank or Telebirr transaction confirmation/reference number.',
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Amount paid in ETB.',
    )
    payment_proof = models.FileField(
        upload_to='payment_proofs/%Y/%m/',
        null=True,
        blank=True,
        help_text='Screenshot image or PDF receipt of the payment.',
    )
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True,
    )
    rejection_reason = models.TextField(
        blank=True,
        default='',
        help_text='Explanation provided to customer if rejected.',
    )
    admin_notes = models.TextField(
        blank=True,
        default='',
        help_text='Internal staff remarks / notes.',
    )
    is_auto_verified = models.BooleanField(
        default=False,
        help_text='Whether this payment was confirmed automatically via bank verification API.',
    )
    auto_verification_status = models.CharField(
        max_length=30,
        blank=True,
        default='',
        help_text='Status from the automated verification API (e.g., SUCCESS, FAILED, SKIPPED).',
    )
    verification_data = models.JSONField(
        default=dict,
        blank=True,
        help_text='Structured payload or receipt data returned by the verification API.',
    )
    verification_error = models.TextField(
        blank=True,
        default='',
        help_text='Error message if automated verification was unsuccessful.',
    )
    receipt_extraction_data = models.JSONField(
        default=dict,
        blank=True,
        help_text='Structured data extracted from the uploaded receipt (references, amount, confidence).',
    )
    receipt_reference_match = models.BooleanField(
        null=True,
        blank=True,
        default=None,
        help_text='Whether the user-provided reference matched the one extracted from the receipt. '
                  'None = no receipt uploaded or extraction not attempted.',
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_payments',
        help_text='Staff member who reviewed and approved/rejected this payment.',
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when payment was reviewed.',
    )
    submitted_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['status', 'submitted_at']),
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['lottery', 'status']),
        ]

    def save(self, *args, **kwargs):
        if self.transaction_reference:
            self.transaction_reference = self.transaction_reference.strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Payment {self.transaction_reference} ({self.get_status_display()}) — {self.customer}'

    @property
    def ticket_count(self) -> int:
        return self.reservations.count()
