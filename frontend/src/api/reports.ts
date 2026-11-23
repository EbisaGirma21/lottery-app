import { apiClient } from './client';
import { DashboardAnalytics } from './types';

export const reportsApi = {
  getDashboardAnalytics: async (): Promise<DashboardAnalytics> => {
    const response = await apiClient.get<DashboardAnalytics>('/reports/dashboard/');
    return response.data;
  },

  downloadLotterySalesExcel: async (lotteryId: string, filename = 'lottery_sales.xlsx') => {
    const response = await apiClient.get(`/reports/lotteries/${lotteryId}/export-excel/`, {
      responseType: 'blob',
    });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  downloadFinancialExcel: async (filename = 'financial_revenue.xlsx') => {
    const response = await apiClient.get('/reports/financial/export-excel/', {
      responseType: 'blob',
    });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  downloadLotterySummaryPdf: async (lotteryId: string, filename = 'lottery_summary.pdf') => {
    const response = await apiClient.get(`/reports/lotteries/${lotteryId}/export-pdf/`, {
      responseType: 'blob',
    });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};
