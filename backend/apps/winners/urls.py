"""
URL configuration for winners app.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.winners.views import WinnerViewSet

router = DefaultRouter()
router.register(r'winners', WinnerViewSet, basename='winner')

urlpatterns = [
    path('', include(router.urls)),
]
