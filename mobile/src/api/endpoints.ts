import { apiClient } from './client';
import {
  User,
  Lottery,
  Ticket,
  Payment,
  Winner,
  Draw,
  DashboardMetrics,
  NotificationItem,
} from '../types/api';

export const api = {
  // Authentication
  auth: {
    login: async (credentials: { email: string; password: string }) => {
      const response = await apiClient.post<{
        access: string;
        refresh: string;
        user: User;
      }>('/api/auth/login/', credentials);
      return response.data;
    },
    getCurrentUser: async () => {
      const response = await apiClient.get<User>('/api/auth/user/');
      return response.data;
    },
  },

  // Dashboard & Analytics
  dashboard: {
    getMetrics: async () => {
      const response = await apiClient.get<DashboardMetrics>('/api/reports/dashboard/');
      return response.data;
    },
  },

  // Lotteries
  lotteries: {
    list: async (params?: { status?: string; search?: string }) => {
      const response = await apiClient.get<Lottery[] | { results: Lottery[] }>('/api/lotteries/', {
        params,
      });
      return Array.isArray(response.data) ? response.data : response.data.results || [];
    },
    getById: async (id: string) => {
      const response = await apiClient.get<Lottery>(`/api/lotteries/${id}/`);
      return response.data;
    },
    getTickets: async (lotteryId: string, params?: { status?: string; search?: string }) => {
      const response = await apiClient.get<Ticket[] | { results: Ticket[] }>(
        `/api/lotteries/${lotteryId}/available-tickets/`,
        { params }
      );
      return Array.isArray(response.data) ? response.data : response.data.results || [];
    },
  },

  // Payments (Staff Verification Queue)
  payments: {
    list: async (params?: { status?: string; search?: string; payment_method?: string }) => {
      const response = await apiClient.get<Payment[] | { results: Payment[] }>('/api/payments/', {
        params,
      });
      return Array.isArray(response.data) ? response.data : response.data.results || [];
    },
    getById: async (id: string) => {
      const response = await apiClient.get<Payment>(`/api/payments/${id}/`);
      return response.data;
    },
    approve: async (id: string) => {
      const response = await apiClient.post<Payment>(`/api/payments/${id}/approve/`);
      return response.data;
    },
    reject: async (id: string, reason: string) => {
      const response = await apiClient.post<Payment>(`/api/payments/${id}/reject/`, { reason });
      return response.data;
    },
  },

  // Tickets
  tickets: {
    list: async (params?: { search?: string; status?: string; lottery?: string }) => {
      const response = await apiClient.get<Ticket[] | { results: Ticket[] }>('/api/tickets/', {
        params,
      });
      return Array.isArray(response.data) ? response.data : response.data.results || [];
    },
    getById: async (id: string) => {
      const response = await apiClient.get<Ticket>(`/api/tickets/${id}/`);
      return response.data;
    },
  },

  // Winners & Draws
  winners: {
    list: async (params?: { lottery?: string; claimed?: boolean }) => {
      const response = await apiClient.get<Winner[] | { results: Winner[] }>('/api/winners/', {
        params,
      });
      return Array.isArray(response.data) ? response.data : response.data.results || [];
    },
    claim: async (id: string) => {
      const response = await apiClient.post<Winner>(`/api/winners/${id}/claim/`);
      return response.data;
    },
  },

  draws: {
    list: async () => {
      const response = await apiClient.get<Draw[] | { results: Draw[] }>('/api/draws/');
      return Array.isArray(response.data) ? response.data : response.data.results || [];
    },
    getById: async (id: string) => {
      const response = await apiClient.get<Draw>(`/api/draws/${id}/`);
      return response.data;
    },
  },

  // Notifications
  notifications: {
    list: async () => {
      const response = await apiClient.get<
        NotificationItem[] | { results: NotificationItem[] }
      >('/api/notifications/');
      return Array.isArray(response.data) ? response.data : response.data.results || [];
    },
    markRead: async (id: string) => {
      const response = await apiClient.post(`/api/notifications/${id}/mark-read/`);
      return response.data;
    },
    markAllRead: async () => {
      const response = await apiClient.post('/api/notifications/mark-all-read/');
      return response.data;
    },
  },
};
