"""
Custom permissions for role-based access control.

Each permission class checks the user's role field to grant or deny access.
"""
from rest_framework.permissions import BasePermission

from apps.accounts.models import UserRole


class IsSuperAdmin(BasePermission):
    """Allows access only to Super Admin users."""
    message = 'Only super administrators can perform this action.'

    def has_permission(self, request, view) -> bool:
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == UserRole.SUPER_ADMIN
        )


class IsLotteryManager(BasePermission):
    """Allows access only to Lottery Manager users."""
    message = 'Only lottery managers can perform this action.'

    def has_permission(self, request, view) -> bool:
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == UserRole.LOTTERY_MANAGER
        )


class IsPaymentOfficer(BasePermission):
    """Allows access only to Payment Officer users."""
    message = 'Only payment officers can perform this action.'

    def has_permission(self, request, view) -> bool:
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == UserRole.PAYMENT_OFFICER
        )


class IsDrawOfficer(BasePermission):
    """Allows access only to Draw Officer users."""
    message = 'Only draw officers can perform this action.'

    def has_permission(self, request, view) -> bool:
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == UserRole.DRAW_OFFICER
        )


class IsViewer(BasePermission):
    """Allows access only to Viewer users (read-only role)."""
    message = 'Viewer role has read-only access.'

    def has_permission(self, request, view) -> bool:
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == UserRole.VIEWER
        )


class IsAdminOrManager(BasePermission):
    """Allows access to Super Admin or Lottery Manager users."""
    message = 'Only administrators or lottery managers can perform this action.'

    def has_permission(self, request, view) -> bool:
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in (UserRole.SUPER_ADMIN, UserRole.LOTTERY_MANAGER)
        )


class IsAdminOrPaymentOfficer(BasePermission):
    """Allows access to Super Admin or Payment Officer users."""
    message = 'Only administrators or payment officers can perform this action.'

    def has_permission(self, request, view) -> bool:
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in (UserRole.SUPER_ADMIN, UserRole.PAYMENT_OFFICER)
        )


class IsPaymentVerifier(BasePermission):
    """Allows access to Super Admin, Lottery Manager, or Payment Officer users."""
    message = 'Only payment officers, lottery managers, or administrators can verify payments.'

    def has_permission(self, request, view) -> bool:
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in (
                UserRole.SUPER_ADMIN,
                UserRole.LOTTERY_MANAGER,
                UserRole.PAYMENT_OFFICER,
            )
        )


class IsAdminOrDrawOfficer(BasePermission):
    """Allows access to Super Admin or Draw Officer users."""
    message = 'Only administrators or draw officers can perform this action.'

    def has_permission(self, request, view) -> bool:
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in (UserRole.SUPER_ADMIN, UserRole.DRAW_OFFICER)
        )


class IsAnyStaffRole(BasePermission):
    """Allows access to any authenticated staff user (any role)."""
    message = 'You must be an authorized staff member.'

    def has_permission(self, request, view) -> bool:
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in (
                UserRole.SUPER_ADMIN,
                UserRole.LOTTERY_MANAGER,
                UserRole.PAYMENT_OFFICER,
                UserRole.DRAW_OFFICER,
                UserRole.VIEWER,
            )
        )


class ReadOnly(BasePermission):
    """Allows read-only access (GET, HEAD, OPTIONS)."""

    def has_permission(self, request, view) -> bool:
        return request.method in ('GET', 'HEAD', 'OPTIONS')
