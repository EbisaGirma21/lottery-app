"""
Views for exporting reports and retrieving dashboard analytics.
"""
from django.http import HttpResponse
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.lotteries.models import Lottery
from apps.reports.services import (
    generate_financial_revenue_excel,
    generate_lottery_sales_excel,
    generate_lottery_summary_pdf,
    get_dashboard_analytics,
)


class DashboardAnalyticsView(APIView):
    """Real-time system-wide analytics, revenue breakdowns, and KPIs."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Reports'],
        summary='Get executive dashboard analytics and KPIs',
        responses={200: dict},
    )
    def get(self, request):
        data = get_dashboard_analytics()
        return Response(data, status=status.HTTP_200_OK)


class LotterySalesReportExcelView(APIView):
    """Export comprehensive lottery sales and ticket ledger to Excel."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Reports'],
        summary='Export lottery ticket sales ledger as Excel (.xlsx)',
    )
    def get(self, request, pk):
        try:
            lottery = Lottery.objects.get(pk=pk)
        except Lottery.DoesNotExist:
            return Response({'detail': 'Lottery not found.'}, status=status.HTTP_404_NOT_FOUND)

        buffer = generate_lottery_sales_excel(lottery)
        filename = f'lottery_{lottery.slug}_sales.xlsx'

        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class FinancialReportExcelView(APIView):
    """Export financial reconciliation report across payment channels to Excel."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Reports'],
        summary='Export financial reconciliation report as Excel (.xlsx)',
    )
    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        buffer = generate_financial_revenue_excel(start_date=start_date, end_date=end_date)
        filename = 'financial_revenue_report.xlsx'

        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class LotterySummaryPdfView(APIView):
    """Export executive performance report for a lottery as PDF."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Reports'],
        summary='Export executive lottery summary report as PDF (.pdf)',
    )
    def get(self, request, pk):
        try:
            lottery = Lottery.objects.get(pk=pk)
        except Lottery.DoesNotExist:
            return Response({'detail': 'Lottery not found.'}, status=status.HTTP_404_NOT_FOUND)

        buffer = generate_lottery_summary_pdf(lottery)
        filename = f'lottery_{lottery.slug}_summary.pdf'

        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/pdf',
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
