"""
URL configuration for draws app.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.draws.views import DrawViewSet

router = DefaultRouter()
router.register(r'draws', DrawViewSet, basename='draw')

urlpatterns = [
    path('', include(router.urls)),
]
