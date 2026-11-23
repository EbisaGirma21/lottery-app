"""
Django admin configuration for lotteries app.
"""
from django.contrib import admin

from apps.lotteries.models import Customer, Lottery, PaymentInstruction


class PaymentInstructionInline(admin.TabularInline):
    model = PaymentInstruction
    extra = 1


@admin.register(Lottery)
class LotteryAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'ticket_price', 'total_numbers', 'closing_date', 'draw_date')
    list_filter = ('status',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [PaymentInstructionInline]
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone_number', 'telegram_user_id', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('full_name', 'phone_number', 'telegram_username')
    readonly_fields = ('id', 'created_at', 'updated_at')
