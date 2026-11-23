"""
Django admin configuration for winners app.
"""
from django.contrib import admin
from django.utils.html import format_html

from apps.winners.models import Winner


@admin.register(Winner)
class WinnerAdmin(admin.ModelAdmin):
    list_display = (
        'position_badge',
        'lottery',
        'ticket',
        'customer',
        'prize_name',
        'prize_value',
        'claim_status_badge',
        'claimed_at',
        'verified_by',
    )
    list_filter = ('position', 'claim_status', 'lottery')
    search_fields = (
        'ticket__ticket_number',
        'customer__full_name',
        'customer__phone_number',
        'payout_reference',
    )
    readonly_fields = (
        'id',
        'draw',
        'lottery',
        'ticket',
        'customer',
        'position',
        'prize_name',
        'prize_description',
        'prize_value',
        'created_at',
        'updated_at',
    )

    def position_badge(self, obj):
        colors = {
            1: '#f59e0b',  # Gold
            2: '#94a3b8',  # Silver
            3: '#b45309',  # Bronze
        }
        color = colors.get(obj.position, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;">{}</span>',
            color,
            obj.get_position_display(),
        )
    position_badge.short_description = 'Position'

    def claim_status_badge(self, obj):
        colors = {
            'pending': '#f59e0b',
            'claimed': '#10b981',
            'expired': '#ef4444',
        }
        color = colors.get(obj.claim_status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;">{}</span>',
            color,
            obj.get_claim_status_display(),
        )
    claim_status_badge.short_description = 'Claim Status'

    def has_add_permission(self, request):
        return False
