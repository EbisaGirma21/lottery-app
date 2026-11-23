"""
Views for user management and authentication.
"""
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.models import User
from apps.accounts.permissions import IsSuperAdmin
from apps.accounts.serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    ProfileSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)


@extend_schema(tags=['Auth'])
class LoginView(generics.GenericAPIView):
    """
    Authenticate a user and return JWT access and refresh tokens.
    """
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)

        # Log the login action
        from apps.audit_logs.services import log_action
        log_action(
            user=user,
            action='LOGIN',
            entity_type='User',
            entity_id=str(user.id),
            ip_address=self._get_client_ip(request),
        )

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
        }, status=status.HTTP_200_OK)

    @staticmethod
    def _get_client_ip(request) -> str:
        """Extract client IP from request headers."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')


@extend_schema(tags=['Auth'])
class CustomTokenRefreshView(TokenRefreshView):
    """Refresh an expired access token using a valid refresh token."""
    pass


@extend_schema(tags=['Auth'])
class ChangePasswordView(generics.GenericAPIView):
    """Change the authenticated user's password."""
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        from apps.audit_logs.services import log_action
        log_action(
            user=user,
            action='PASSWORD_CHANGED',
            entity_type='User',
            entity_id=str(user.id),
            ip_address=LoginView._get_client_ip(request),
        )

        return Response(
            {'detail': 'Password updated successfully.'},
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=['Users'])
class ProfileView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update the authenticated user's profile.

    GET: Returns the current user's profile.
    PATCH/PUT: Updates allowed profile fields (full_name, phone_number).
    """
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


@extend_schema_view(
    list=extend_schema(tags=['Users'], summary='List all users'),
    retrieve=extend_schema(tags=['Users'], summary='Get user details'),
    create=extend_schema(tags=['Users'], summary='Create a new user'),
    update=extend_schema(tags=['Users'], summary='Update a user'),
    partial_update=extend_schema(tags=['Users'], summary='Partially update a user'),
    destroy=extend_schema(tags=['Users'], summary='Deactivate a user'),
)
class UserViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for user management.

    - Super Admin: Full access (create, read, update, deactivate).
    - Other roles: Can only view users (list/retrieve).

    Deletion is soft — it deactivates the user instead of removing them.
    """
    queryset = User.objects.all()
    filterset_fields = ['role', 'is_active']
    search_fields = ['email', 'full_name', 'phone_number']
    ordering_fields = ['date_joined', 'full_name', 'email']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsSuperAdmin()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ('update', 'partial_update'):
            return UserUpdateSerializer
        return UserSerializer

    def perform_create(self, serializer):
        user = serializer.save()

        from apps.audit_logs.services import log_action
        log_action(
            user=self.request.user,
            action='USER_CREATED',
            entity_type='User',
            entity_id=str(user.id),
            new_value={
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
            },
            ip_address=LoginView._get_client_ip(self.request),
        )

    def perform_update(self, serializer):
        old_data = UserSerializer(self.get_object()).data
        user = serializer.save()

        from apps.audit_logs.services import log_action
        log_action(
            user=self.request.user,
            action='USER_UPDATED',
            entity_type='User',
            entity_id=str(user.id),
            old_value={k: str(v) for k, v in old_data.items()},
            new_value={
                'full_name': user.full_name,
                'role': user.role,
                'is_active': user.is_active,
            },
            ip_address=LoginView._get_client_ip(self.request),
        )

    def destroy(self, request, *args, **kwargs):
        """Soft-delete: deactivate the user instead of removing them."""
        user = self.get_object()

        if user == request.user:
            return Response(
                {'detail': 'You cannot deactivate your own account.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.is_active = False
        user.save()

        from apps.audit_logs.services import log_action
        log_action(
            user=request.user,
            action='USER_DEACTIVATED',
            entity_type='User',
            entity_id=str(user.id),
            new_value={'is_active': False},
            ip_address=LoginView._get_client_ip(request),
        )

        return Response(
            {'detail': 'User has been deactivated.'},
            status=status.HTTP_200_OK,
        )
