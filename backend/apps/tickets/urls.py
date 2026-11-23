"""
URL routing for tickets app.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.tickets.views import AvailableTicketsView, TicketViewSet

router = DefaultRouter()
router.register(r'tickets', TicketViewSet, basename='ticket')

urlpatterns = [
    path('', include(router.urls)),
    path(
        'lotteries/<uuid:lottery_id>/available-tickets/',
        AvailableTicketsView.as_view({'get': 'list'}),
        name='available-tickets',
    ),
]
