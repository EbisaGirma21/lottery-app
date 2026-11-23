from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),

    # API endpoints
    path('api/', include('apps.accounts.urls')),
    path('api/', include('apps.audit_logs.urls')),
    path('api/', include('apps.lotteries.urls')),
    path('api/', include('apps.tickets.urls')),
    path('api/', include('apps.reservations.urls')),
    path('api/', include('apps.payments.urls')),
    path('api/', include('apps.draws.urls')),
    path('api/', include('apps.winners.urls')),
    path('api/', include('apps.reports.urls')),
    path('api/', include('apps.notifications.urls')),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

