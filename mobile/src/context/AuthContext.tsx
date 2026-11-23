import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { User } from '../types/api';
import { api } from '../api/endpoints';
import { STORAGE_KEYS, getBaseUrl, setBaseUrl } from '../api/client';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isPaymentVerifier: boolean;
  isDrawOfficer: boolean;
  isSuperAdmin: boolean;
  serverUrl: string;
  login: (email: string, pass: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  updateServerUrl: (url: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [serverUrl, setServerUrlState] = useState<string>('http://localhost:8000');

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const savedUrl = await getBaseUrl();
        setServerUrlState(savedUrl);

        const token = await AsyncStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
        const storedUser = await AsyncStorage.getItem(STORAGE_KEYS.USER_DATA);

        if (token && storedUser) {
          try {
            setUser(JSON.parse(storedUser));
            // Fetch fresh user profile in background
            const freshUser = await api.auth.getCurrentUser();
            setUser(freshUser);
            await AsyncStorage.setItem(STORAGE_KEYS.USER_DATA, JSON.stringify(freshUser));
          } catch (e) {
            // Token might be valid or will refresh on next request
          }
        }
      } catch (err) {
        console.error('Failed to initialize auth state', err);
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, []);

  const login = async (email: string, pass: string) => {
    setIsLoading(true);
    try {
      const data = await api.auth.login({ email, password: pass });
      await AsyncStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, data.access);
      await AsyncStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, data.refresh);
      await AsyncStorage.setItem(STORAGE_KEYS.USER_DATA, JSON.stringify(data.user));
      setUser(data.user);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      await AsyncStorage.multiRemove([
        STORAGE_KEYS.ACCESS_TOKEN,
        STORAGE_KEYS.REFRESH_TOKEN,
        STORAGE_KEYS.USER_DATA,
      ]);
      setUser(null);
    } catch (e) {
      console.error('Logout error', e);
    }
  };

  const refreshUser = async () => {
    try {
      const freshUser = await api.auth.getCurrentUser();
      setUser(freshUser);
      await AsyncStorage.setItem(STORAGE_KEYS.USER_DATA, JSON.stringify(freshUser));
    } catch (e) {
      console.error('Failed to refresh user', e);
    }
  };

  const updateServerUrl = async (url: string) => {
    await setBaseUrl(url);
    setServerUrlState(url);
  };

  const role = user?.role;
  const isSuperAdmin = role === 'super_admin';
  const isPaymentVerifier = role === 'payment_verifier' || isSuperAdmin;
  const isDrawOfficer = role === 'draw_officer' || isSuperAdmin;

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        isPaymentVerifier,
        isDrawOfficer,
        isSuperAdmin,
        serverUrl,
        login,
        logout,
        refreshUser,
        updateServerUrl,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
