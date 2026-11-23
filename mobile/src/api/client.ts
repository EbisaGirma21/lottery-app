import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

export const STORAGE_KEYS = {
  ACCESS_TOKEN: '@lottery_access_token',
  REFRESH_TOKEN: '@lottery_refresh_token',
  USER_DATA: '@lottery_user_data',
  API_BASE_URL: '@lottery_api_base_url',
};

// Default backend host (supports web, iOS simulator, Android localhost port mapping)
export const DEFAULT_BASE_URL = 'http://localhost:8000';

let currentBaseUrl = DEFAULT_BASE_URL;

export const getBaseUrl = async (): Promise<string> => {
  try {
    const savedUrl = await AsyncStorage.getItem(STORAGE_KEYS.API_BASE_URL);
    if (savedUrl) {
      currentBaseUrl = savedUrl;
      return savedUrl;
    }
  } catch (e) {
    // Fallback
  }
  return currentBaseUrl;
};

export const setBaseUrl = async (url: string): Promise<void> => {
  const trimmed = url.replace(/\/+$/, '');
  currentBaseUrl = trimmed;
  await AsyncStorage.setItem(STORAGE_KEYS.API_BASE_URL, trimmed);
  apiClient.defaults.baseURL = trimmed;
};

export const apiClient = axios.create({
  baseURL: DEFAULT_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

// Initialize base URL from storage
getBaseUrl().then((url) => {
  apiClient.defaults.baseURL = url;
});

// Request Interceptor: Attach JWT Bearer Token
apiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    // Ensure current base URL is applied
    if (!config.baseURL || config.baseURL === DEFAULT_BASE_URL) {
      config.baseURL = currentBaseUrl;
    }

    const token = await AsyncStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Auto-refresh JWT token on 401 Unauthorized
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (err: any) => void;
}> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token!);
    }
  });
  failedQueue = [];
};

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (!originalRequest) {
      return Promise.reject(error);
    }

    // If 401 and not already retried
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (originalRequest.url?.includes('/api/auth/login/') || originalRequest.url?.includes('/api/auth/token/refresh/')) {
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return apiClient(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const refreshToken = await AsyncStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
        if (!refreshToken) {
          throw new Error('No refresh token available');
        }

        const response = await axios.post(`${currentBaseUrl}/api/auth/token/refresh/`, {
          refresh: refreshToken,
        });

        const newAccessToken = response.data.access;
        await AsyncStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, newAccessToken);
        if (response.data.refresh) {
          await AsyncStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, response.data.refresh);
        }

        apiClient.defaults.headers.common.Authorization = `Bearer ${newAccessToken}`;
        processQueue(null, newAccessToken);

        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return apiClient(originalRequest);
      } catch (refreshErr) {
        processQueue(refreshErr, null);
        await AsyncStorage.multiRemove([
          STORAGE_KEYS.ACCESS_TOKEN,
          STORAGE_KEYS.REFRESH_TOKEN,
          STORAGE_KEYS.USER_DATA,
        ]);
        return Promise.reject(refreshErr);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);
