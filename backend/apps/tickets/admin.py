"""
Django admin configuration for tickets app.
"""
from django.contrib import admin

from apps.tickets.models import Ticket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_number', 'lottery', 'status', 'customer', 'updated_at')
    list_filter = ('status', 'lottery')
    search_fields = ('ticket_number', 'customer__full_name', 'customer__phone_number')
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('lottery', 'customer')
