import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react';
import api from '@/lib/api';
import type { User, LoginRequest, TokenResponse } from '@/types';

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

interface AuthContextValue extends AuthState {
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: localStorage.getItem('access_token'),
    isLoading: true,
    isAuthenticated: false,
  });

  const fetchUser = useCallback(async (token: string) => {
    try {
      const res = await api.get<User>('/auth/me', {
        headers: { Authorization: `Bearer ${token}` },
      });
      setState({
        user: res.data,
        token,
        isLoading: false,
        isAuthenticated: true,
      });
    } catch {
      localStorage.removeItem('access_token');
      setState({
        user: null,
        token: null,
        isLoading: false,
        isAuthenticated: false,
      });
    }
  }, []);

  // On mount: validate stored token
  useEffect(() => {
    const stored = localStorage.getItem('access_token');
    if (stored) {
      fetchUser(stored);
    } else {
      setState((s) => ({ ...s, isLoading: false }));
    }
  }, [fetchUser]);

  const login = useCallback(async (credentials: LoginRequest) => {
    const res = await api.post<TokenResponse>('/auth/login', credentials);
    const { access_token } = res.data;
    localStorage.setItem('access_token', access_token);
    await fetchUser(access_token);
  }, [fetchUser]);

  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    setState({
      user: null,
      token: null,
      isLoading: false,
      isAuthenticated: false,
    });
  }, []);

  const refreshUser = useCallback(async () => {
    if (state.token) {
      await fetchUser(state.token);
    }
  }, [state.token, fetchUser]);

  return (
    <AuthContext.Provider value={{ ...state, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}