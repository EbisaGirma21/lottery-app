import React, { createContext, useContext, useEffect, useState } from 'react';
import { authApi } from '../api/auth';
import { User, UserRole } from '../api/types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  hasRole: (roles: UserRole[]) => boolean;
  isSuperAdmin: boolean;
  isLotteryManager: boolean;
  isPaymentVerifier: boolean;
  isDrawOfficer: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('auth_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('access_token'));
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('access_token');
      if (storedToken) {
        try {
          const profile = await authApi.getProfile();
          setUser(profile);
          localStorage.setItem('auth_user', JSON.stringify(profile));
        } catch {
          // Token invalid
          setUser(null);
          setToken(null);
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('auth_user');
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    const data = await authApi.login(email, password);
    setToken(data.access);
    setUser(data.user);
    localStorage.setItem('access_token', data.access);
    localStorage.setItem('refresh_token', data.refresh);
    localStorage.setItem('auth_user', JSON.stringify(data.user));
  };

  const logout = () => {
    authApi.logout();
    setUser(null);
    setToken(null);
  };

  const hasRole = (roles: UserRole[]): boolean => {
    if (!user) return false;
    if (user.role === 'super_admin') return true;
    return roles.includes(user.role);
  };

  const isSuperAdmin = user?.role === 'super_admin';
  const isLotteryManager = isSuperAdmin || user?.role === 'lottery_manager';
  const isPaymentVerifier =
    isSuperAdmin || user?.role === 'lottery_manager' || user?.role === 'payment_officer';
  const isDrawOfficer = isSuperAdmin || user?.role === 'draw_officer';

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        hasRole,
        isSuperAdmin,
        isLotteryManager,
        isPaymentVerifier,
        isDrawOfficer,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
