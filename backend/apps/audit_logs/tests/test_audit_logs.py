"""
Tests for audit log model and service.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.tests.factories import SuperAdminFactory, ViewerFactory, LotteryManagerFactory
from apps.audit_logs.models import AuditLog
from apps.audit_logs.services import log_action


@pytest.mark.django_db
class TestAuditLogService:
    """Tests for the log_action() service function."""

    def test_create_audit_log(self):
        user = SuperAdminFactory()
        log = log_action(
            user=user,
            action='TEST_ACTION',
            entity_type='TestEntity',
            entity_id='123',
            new_value={'key': 'value'},
            ip_address='127.0.0.1',
        )
        assert log is not None
        assert log.action == 'TEST_ACTION'
        assert log.entity_type == 'TestEntity'
        assert log.entity_id == '123'
        assert log.new_value == {'key': 'value'}
        assert log.ip_address == '127.0.0.1'
        assert log.user == user

    def test_create_audit_log_without_user(self):
        """System actions can have no user."""
        log = log_action(
            action='SYSTEM_TASK',
            entity_type='System',
            entity_id='0',
        )
        assert log is not None
        assert log.user is None

    def test_create_audit_log_with_old_and_new_values(self):
        user = SuperAdminFactory()
        log = log_action(
            user=user,
            action='UPDATE',
            entity_type='User',
            entity_id='456',
            old_value={'name': 'Old'},
            new_value={'name': 'New'},
        )
        assert log.old_value == {'name': 'Old'}
        assert log.new_value == {'name': 'New'}

    def test_audit_log_str(self):
        user = SuperAdminFactory(email='test@log.com')
        log = log_action(
            user=user,
            action='LOGIN',
            entity_type='User',
            entity_id='789',
        )
        assert 'test@log.com' in str(log)
        assert 'LOGIN' in str(log)


@pytest.mark.django_db
class TestAuditLogAPI:
    """Tests for audit log API endpoints."""

    def setup_method(self):
        self.client = APIClient()
        self.url = reverse('audit-log-list')

    def test_super_admin_can_list_audit_logs(self):
        admin = SuperAdminFactory()
        log_action(user=admin, action='TEST', entity_type='X', entity_id='1')

        self.client.force_authenticate(user=admin)
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['count'] >= 1

    def test_lottery_manager_cannot_access_audit_logs(self):
        manager = LotteryManagerFactory()
        self.client.force_authenticate(user=manager)
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_cannot_access_audit_logs(self):
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_audit_logs_are_read_only(self):
        """POST/PUT/DELETE should not be allowed."""
        admin = SuperAdminFactory()
        self.client.force_authenticate(user=admin)

        response = self.client.post(self.url, {'action': 'HACK'})
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_login_creates_audit_log(self):
        """Successful login should create an audit log entry."""
        admin = SuperAdminFactory(email='audit@test.com', password='TestPass123!')

        login_url = reverse('auth-login')
        self.client.post(login_url, {
            'email': 'audit@test.com',
            'password': 'TestPass123!',
        })

        logs = AuditLog.objects.filter(action='LOGIN', user=admin)
        assert logs.count() == 1
