import { apiClient } from './client';
import { Draw, Winner } from './types';

export const drawsApi = {
  getDraws: async (params?: Record<string, any>): Promise<{ count: number; results: Draw[] }> => {
    const response = await apiClient.get('/draws/', { params });
    if (Array.isArray(response.data)) {
      return { count: response.data.length, results: response.data };
    }
    return response.data;
  },

  getDraw: async (id: string): Promise<Draw> => {
    const response = await apiClient.get<Draw>(`/draws/${id}/`);
    return response.data;
  },

  executeDraw: async (lotteryId: string): Promise<Draw> => {
    const response = await apiClient.post<Draw>('/draws/execute/', {
      lottery_id: lotteryId,
    });
    return response.data;
  },

  getWinners: async (params?: Record<string, any>): Promise<{ count: number; results: Winner[] }> => {
    const response = await apiClient.get('/winners/', { params });
    if (Array.isArray(response.data)) {
      return { count: response.data.length, results: response.data };
    }
    return response.data;
  },

  claimPrize: async (winnerId: string, payoutReference: string, notes?: string): Promise<Winner> => {
    const response = await apiClient.post<Winner>(`/winners/${winnerId}/claim/`, {
      payout_reference: payoutReference,
      notes: notes || '',
    });
    return response.data;
  },
};
