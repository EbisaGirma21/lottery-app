"""
Django admin configuration for draws app.
"""
from django.contrib import admin

from apps.draws.models import Draw


@admin.register(Draw)
class DrawAdmin(admin.ModelAdmin):
    list_display = ('lottery', 'executed_by', 'total_eligible_tickets', 'executed_at')
    list_filter = ('executed_at',)
    search_fields = ('lottery__name', 'executed_by__full_name', 'randomness_hash')
    readonly_fields = (
        'id',
        'lottery',
        'executed_by',
        'total_eligible_tickets',
        'randomness_hash',
        'executed_at',
    )

    def has_add_permission(self, request):
        # Draws must only be executed via the API or official workflow
        return False

    def has_delete_permission(self, request, obj=None):
        # Draws are permanent legal records and cannot be deleted
        return False
