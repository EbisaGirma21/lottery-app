"""
URL routing for audit logs app.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.audit_logs.views import AuditLogViewSet

router = DefaultRouter()
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')

urlpatterns = [
    path('', include(router.urls)),
]
