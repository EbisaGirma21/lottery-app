"""
Tests for authentication endpoints (login, token refresh, password change).
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import UserRole
from apps.accounts.tests.factories import SuperAdminFactory, ViewerFactory


@pytest.mark.django_db
class TestLogin:
    """Tests for the login endpoint."""

    def setup_method(self):
        self.client = APIClient()
        self.url = reverse('auth-login')

    def test_login_success(self):
        """Valid credentials return access and refresh tokens."""
        user = SuperAdminFactory(email='admin@test.com', password='TestPass123!')
        response = self.client.post(self.url, {
            'email': 'admin@test.com',
            'password': 'TestPass123!',
        })
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'access' in data
        assert 'refresh' in data
        assert 'user' in data
        assert data['user']['email'] == 'admin@test.com'
        assert data['user']['role'] == UserRole.SUPER_ADMIN

    def test_login_wrong_password(self):
        """Wrong password returns 400."""
        SuperAdminFactory(email='admin@test.com', password='TestPass123!')
        response = self.client.post(self.url, {
            'email': 'admin@test.com',
            'password': 'WrongPassword!',
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_nonexistent_user(self):
        """Login with non-existent email returns 400."""
        response = self.client.post(self.url, {
            'email': 'nobody@test.com',
            'password': 'TestPass123!',
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_inactive_user(self):
        """Inactive user cannot login."""
        SuperAdminFactory(
            email='inactive@test.com',
            password='TestPass123!',
            is_active=False,
        )
        response = self.client.post(self.url, {
            'email': 'inactive@test.com',
            'password': 'TestPass123!',
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_case_insensitive_email(self):
        """Email should be case-insensitive on login."""
        SuperAdminFactory(email='admin@test.com', password='TestPass123!')
        response = self.client.post(self.url, {
            'email': 'ADMIN@test.com',
            'password': 'TestPass123!',
        })
        # Should work because serializer normalizes email
        assert response.status_code == status.HTTP_200_OK

    def test_login_missing_fields(self):
        """Missing email or password returns 400."""
        response = self.client.post(self.url, {'email': 'admin@test.com'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        response = self.client.post(self.url, {'password': 'TestPass123!'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestTokenRefresh:
    """Tests for the token refresh endpoint."""

    def setup_method(self):
        self.client = APIClient()
        self.login_url = reverse('auth-login')
        self.refresh_url = reverse('auth-refresh')

    def test_refresh_token_success(self):
        """Valid refresh token returns a new access token."""
        SuperAdminFactory(email='admin@test.com', password='TestPass123!')
        login_resp = self.client.post(self.login_url, {
            'email': 'admin@test.com',
            'password': 'TestPass123!',
        })
        refresh_token = login_resp.json()['refresh']

        response = self.client.post(self.refresh_url, {'refresh': refresh_token})
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.json()

    def test_refresh_token_invalid(self):
        """Invalid refresh token returns 401."""
        response = self.client.post(self.refresh_url, {'refresh': 'invalid-token'})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestChangePassword:
    """Tests for the change password endpoint."""

    def setup_method(self):
        self.client = APIClient()
        self.url = reverse('auth-change-password')

    def test_change_password_success(self):
        """Valid current password and matching new passwords succeeds."""
        user = ViewerFactory(email='user@test.com', password='OldPass123!')
        self.client.force_authenticate(user=user)

        response = self.client.post(self.url, {
            'current_password': 'OldPass123!',
            'new_password': 'NewPass456!',
            'confirm_new_password': 'NewPass456!',
        })
        assert response.status_code == status.HTTP_200_OK

        # Verify new password works
        user.refresh_from_db()
        assert user.check_password('NewPass456!')

    def test_change_password_wrong_current(self):
        """Wrong current password returns 400."""
        user = ViewerFactory(email='user@test.com', password='OldPass123!')
        self.client.force_authenticate(user=user)

        response = self.client.post(self.url, {
            'current_password': 'WrongPass!',
            'new_password': 'NewPass456!',
            'confirm_new_password': 'NewPass456!',
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_change_password_mismatch(self):
        """Non-matching new passwords returns 400."""
        user = ViewerFactory(email='user@test.com', password='OldPass123!')
        self.client.force_authenticate(user=user)

        response = self.client.post(self.url, {
            'current_password': 'OldPass123!',
            'new_password': 'NewPass456!',
            'confirm_new_password': 'DifferentPass!',
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_change_password_unauthenticated(self):
        """Unauthenticated request returns 401."""
        response = self.client.post(self.url, {
            'current_password': 'OldPass123!',
            'new_password': 'NewPass456!',
            'confirm_new_password': 'NewPass456!',
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
