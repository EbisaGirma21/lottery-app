"""
URL configuration for reports app.
"""
from django.urls import path

from apps.reports.views import (
    DashboardAnalyticsView,
    FinancialReportExcelView,
    LotterySalesReportExcelView,
    LotterySummaryPdfView,
)

urlpatterns = [
    path('reports/dashboard/', DashboardAnalyticsView.as_view(), name='reports-dashboard'),
    path('reports/financial/export-excel/', FinancialReportExcelView.as_view(), name='reports-financial-excel'),
    path('reports/lotteries/<uuid:pk>/export-excel/', LotterySalesReportExcelView.as_view(), name='reports-lottery-excel'),
    path('reports/lotteries/<uuid:pk>/export-pdf/', LotterySummaryPdfView.as_view(), name='reports-lottery-pdf'),
]
