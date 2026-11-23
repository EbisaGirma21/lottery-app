"""
URL routing for lotteries app.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.lotteries.views import CustomerViewSet, LotteryViewSet

router = DefaultRouter()
router.register(r'lotteries', LotteryViewSet, basename='lottery')
router.register(r'customers', CustomerViewSet, basename='customer')

urlpatterns = [
    path('', include(router.urls)),
]
