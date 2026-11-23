"""
URL routing for reservations app.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.reservations.views import ReservationViewSet

router = DefaultRouter()
router.register(r'reservations', ReservationViewSet, basename='reservation')

urlpatterns = [
    path('', include(router.urls)),
]
