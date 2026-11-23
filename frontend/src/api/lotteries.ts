import { apiClient } from './client';
import { Lottery, LotteryParticipantsResponse, LotteryStatus, Ticket } from './types';

export const lotteriesApi = {
  getLotteries: async (params?: Record<string, any>): Promise<{ count: number; results: Lottery[] }> => {
    const response = await apiClient.get('/lotteries/', { params });
    // Handles paginated or raw list response
    if (Array.isArray(response.data)) {
      return { count: response.data.length, results: response.data };
    }
    return response.data;
  },

  getLottery: async (id: string): Promise<Lottery> => {
    const response = await apiClient.get<Lottery>(`/lotteries/${id}/`);
    return response.data;
  },

  createLottery: async (data: Partial<Lottery>): Promise<Lottery> => {
    const response = await apiClient.post<Lottery>('/lotteries/', data);
    return response.data;
  },

  updateLottery: async (id: string, data: Partial<Lottery>): Promise<Lottery> => {
    const response = await apiClient.patch<Lottery>(`/lotteries/${id}/`, data);
    return response.data;
  },

  changeStatus: async (id: string, newStatus: LotteryStatus): Promise<Lottery> => {
    const response = await apiClient.post<Lottery>(`/lotteries/${id}/change-status/`, {
      status: newStatus,
    });
    return response.data;
  },

  getLotteryStats: async (id: string): Promise<Record<string, any>> => {
    const response = await apiClient.get(`/lotteries/${id}/stats/`);
    return response.data;
  },

  getTickets: async (lotteryId: string, params?: Record<string, any>): Promise<{ count: number; results: Ticket[] }> => {
    const response = await apiClient.get('/tickets/', {
      params: { lottery: lotteryId, ...params },
    });
    if (Array.isArray(response.data)) {
      return { count: response.data.length, results: response.data };
    }
    return response.data;
  },

  getParticipants: async (lotteryId: string): Promise<LotteryParticipantsResponse> => {
    const response = await apiClient.get<LotteryParticipantsResponse>(`/lotteries/${lotteryId}/participants/`);
    return response.data;
  },
};
