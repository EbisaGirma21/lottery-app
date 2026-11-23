"""
Django admin configuration for reservations app.
"""
from django.contrib import admin

from apps.reservations.models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'customer', 'lottery', 'status', 'reserved_at', 'expires_at')
    list_filter = ('status', 'lottery')
    search_fields = (
        'ticket__ticket_number',
        'customer__full_name',
        'customer__phone_number',
    )
    readonly_fields = ('id', 'reserved_at')
    raw_id_fields = ('customer', 'lottery', 'ticket')
