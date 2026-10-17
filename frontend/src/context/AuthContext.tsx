import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

import {
  api,
  LoginPayload,
  RegisterPayload,
  UserProfile,
} from '../api/client';

interface AuthContextValue {
  user: UserProfile | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshProfile = useCallback(async () => {
    const me = await api.get<UserProfile>('/users/me');
    setUser(me.data);
  }, []);

  // Восстановление сессии при старте приложения
  useEffect(() => {
    const bootstrap = async () => {
      try {
        const saved = await AsyncStorage.getItem('access_token');
        if (!saved) return;
        setToken(saved);
        const me = await api.get<UserProfile>('/users/me');
        setUser(me.data);
      } catch {
        await AsyncStorage.removeItem('access_token');
        setToken(null);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };
    bootstrap();
  }, []);

  const login = useCallback(async (payload: LoginPayload) => {
    const { data } = await api.post<{ access_token: string }>('/auth/login', payload);
    await AsyncStorage.setItem('access_token', data.access_token);
    setToken(data.access_token);
    await refreshProfile();
  }, [refreshProfile]);

  const register = useCallback(async (payload: RegisterPayload) => {
    await api.post('/auth/register', payload);
  }, []);

  const logout = useCallback(async () => {
    await AsyncStorage.removeItem('access_token');
    setToken(null);
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      token,
      isLoading,
      isAuthenticated: Boolean(token && user),
      login,
      register,
      logout,
      refreshProfile,
    }),
    [user, token, isLoading, login, register, logout, refreshProfile],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return ctx;
}
