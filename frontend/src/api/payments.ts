import { apiClient } from './client';
import { Payment } from './types';

export const paymentsApi = {
  getPayments: async (params?: Record<string, any>): Promise<{ count: number; results: Payment[] }> => {
    const response = await apiClient.get('/payments/', { params });
    if (Array.isArray(response.data)) {
      return { count: response.data.length, results: response.data };
    }
    return response.data;
  },

  getPayment: async (id: string): Promise<Payment> => {
    const response = await apiClient.get<Payment>(`/payments/${id}/`);
    return response.data;
  },

  approvePayment: async (id: string, adminNotes?: string): Promise<Payment> => {
    const response = await apiClient.post<Payment>(`/payments/${id}/approve/`, {
      admin_notes: adminNotes || '',
    });
    return response.data;
  },

  rejectPayment: async (id: string, rejectionReason: string): Promise<Payment> => {
    const response = await apiClient.post<Payment>(`/payments/${id}/reject/`, {
      rejection_reason: rejectionReason,
    });
    return response.data;
  },

  verifyPaymentNow: async (id: string): Promise<Payment> => {
    const response = await apiClient.post<Payment>(`/payments/${id}/verify-now/`);
    return response.data;
  },

  getStats: async (): Promise<Record<string, any>> => {
    const response = await apiClient.get('/payments/stats/');
    return response.data;
  },
};
