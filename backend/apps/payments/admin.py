"""
Django admin configuration for payments app.
"""
from django.contrib import admin
from django.utils.html import format_html

from apps.payments.models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_reference',
        'customer',
        'lottery',
        'payment_method',
        'amount',
        'status_badge',
        'ticket_count_display',
        'submitted_at',
        'reviewed_by',
    )
    list_filter = ('status', 'payment_method', 'lottery', 'submitted_at')
    search_fields = (
        'transaction_reference',
        'customer__full_name',
        'customer__phone_number',
        'customer__telegram_username',
    )
    readonly_fields = ('id', 'submitted_at', 'updated_at', 'reviewed_at', 'proof_preview')
    raw_id_fields = ('customer', 'lottery', 'reviewed_by')
    filter_horizontal = ('reservations',)

    fieldsets = (
        ('Submission Info', {
            'fields': (
                'id',
                'customer',
                'lottery',
                'payment_method',
                'transaction_reference',
                'amount',
                'payment_proof',
                'proof_preview',
                'reservations',
                'submitted_at',
            )
        }),
        ('Verification & Review', {
            'fields': (
                'status',
                'rejection_reason',
                'admin_notes',
                'reviewed_by',
                'reviewed_at',
                'updated_at',
            )
        }),
    )

    def status_badge(self, obj):
        colors = {
            'pending': '#f59e0b',
            'approved': '#10b981',
            'rejected': '#ef4444',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display(),
        )
    status_badge.short_description = 'Status'

    def ticket_count_display(self, obj):
        return obj.ticket_count
    ticket_count_display.short_description = 'Tickets'

    def proof_preview(self, obj):
        if obj.payment_proof:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="max-height: 200px; max-width: 300px; border-radius: 4px;" /></a>',
                obj.payment_proof.url,
                obj.payment_proof.url,
            )
        return 'No screenshot attached.'
    proof_preview.short_description = 'Payment Proof Preview'
