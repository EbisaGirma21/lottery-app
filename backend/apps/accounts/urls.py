"""
URL routing for accounts app.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounts.views import (
    ChangePasswordView,
    CustomTokenRefreshView,
    LoginView,
    ProfileView,
    UserViewSet,
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    # Authentication
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/refresh/', CustomTokenRefreshView.as_view(), name='auth-refresh'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='auth-change-password'),

    # Profile (current user)
    path('users/me/', ProfileView.as_view(), name='user-profile'),
    path('auth/profile/', ProfileView.as_view(), name='auth-profile'),

    # User management (CRUD)
    path('', include(router.urls)),
]
