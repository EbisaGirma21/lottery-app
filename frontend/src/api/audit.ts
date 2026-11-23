import { apiClient } from './client';
import { AuditLog } from './types';

export const auditApi = {
  getAuditLogs: async (params?: Record<string, any>): Promise<{ count: number; results: AuditLog[] }> => {
    const response = await apiClient.get('/audit-logs/', { params });
    if (Array.isArray(response.data)) {
      return { count: response.data.length, results: response.data };
    }
    return response.data;
  },
};
