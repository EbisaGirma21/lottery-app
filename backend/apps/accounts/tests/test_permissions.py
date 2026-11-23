"""
Tests for role-based permission enforcement.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.tests.factories import (
    DrawOfficerFactory,
    LotteryManagerFactory,
    PaymentOfficerFactory,
    SuperAdminFactory,
    ViewerFactory,
)


@pytest.mark.django_db
class TestUserCRUDPermissions:
    """Test that only Super Admin can create/update/delete users."""

    def setup_method(self):
        self.client = APIClient()
        self.list_url = reverse('user-list')
        self.user_data = {
            'email': 'newuser@test.com',
            'full_name': 'New User',
            'role': 'viewer',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!',
        }

    def test_super_admin_can_create_user(self):
        admin = SuperAdminFactory()
        self.client.force_authenticate(user=admin)
        response = self.client.post(self.list_url, self.user_data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_lottery_manager_cannot_create_user(self):
        manager = LotteryManagerFactory()
        self.client.force_authenticate(user=manager)
        response = self.client.post(self.list_url, self.user_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_payment_officer_cannot_create_user(self):
        officer = PaymentOfficerFactory()
        self.client.force_authenticate(user=officer)
        response = self.client.post(self.list_url, self.user_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_draw_officer_cannot_create_user(self):
        officer = DrawOfficerFactory()
        self.client.force_authenticate(user=officer)
        response = self.client.post(self.list_url, self.user_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_viewer_cannot_create_user(self):
        viewer = ViewerFactory()
        self.client.force_authenticate(user=viewer)
        response = self.client.post(self.list_url, self.user_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_all_roles_can_list_users(self):
        """Every authenticated role should be able to list users."""
        factories = [
            SuperAdminFactory,
            LotteryManagerFactory,
            PaymentOfficerFactory,
            DrawOfficerFactory,
            ViewerFactory,
        ]
        for factory_cls in factories:
            user = factory_cls()
            self.client.force_authenticate(user=user)
            response = self.client.get(self.list_url)
            assert response.status_code == status.HTTP_200_OK, (
                f'{user.role} should be able to list users'
            )

    def test_unauthenticated_cannot_list_users(self):
        """Unauthenticated requests should be rejected."""
        response = self.client.get(self.list_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_super_admin_can_update_user(self):
        admin = SuperAdminFactory()
        target = ViewerFactory()
        self.client.force_authenticate(user=admin)

        url = reverse('user-detail', kwargs={'pk': target.id})
        response = self.client.patch(url, {'full_name': 'Updated Name'})
        assert response.status_code == status.HTTP_200_OK

    def test_non_admin_cannot_update_user(self):
        manager = LotteryManagerFactory()
        target = ViewerFactory()
        self.client.force_authenticate(user=manager)

        url = reverse('user-detail', kwargs={'pk': target.id})
        response = self.client.patch(url, {'full_name': 'Hacked Name'})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_super_admin_can_deactivate_user(self):
        admin = SuperAdminFactory()
        target = ViewerFactory()
        self.client.force_authenticate(user=admin)

        url = reverse('user-detail', kwargs={'pk': target.id})
        response = self.client.delete(url)
        assert response.status_code == status.HTTP_200_OK

        target.refresh_from_db()
        assert target.is_active is False

    def test_cannot_deactivate_self(self):
        admin = SuperAdminFactory()
        self.client.force_authenticate(user=admin)

        url = reverse('user-detail', kwargs={'pk': admin.id})
        response = self.client.delete(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestProfilePermissions:
    """Test that any authenticated user can view/update their own profile."""

    def setup_method(self):
        self.client = APIClient()
        self.url = reverse('user-profile')

    def test_authenticated_user_can_view_profile(self):
        user = ViewerFactory(full_name='My Profile')
        self.client.force_authenticate(user=user)
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['full_name'] == 'My Profile'

    def test_authenticated_user_can_update_profile(self):
        user = ViewerFactory()
        self.client.force_authenticate(user=user)
        response = self.client.patch(self.url, {'full_name': 'Updated Name'})
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['full_name'] == 'Updated Name'

    def test_user_cannot_change_own_role(self):
        """Profile update should not allow role changes."""
        user = ViewerFactory()
        self.client.force_authenticate(user=user)
        response = self.client.patch(self.url, {'role': 'super_admin'})
        # role is read-only in ProfileSerializer, so it should be ignored
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.role == 'viewer'

    def test_unauthenticated_cannot_view_profile(self):
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
