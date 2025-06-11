import React, { createContext, useContext, useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useSnackbar } from 'notistack';
import { authAPI } from '../services/api';
import { User, LoginRequest, RegisterRequest } from '../types';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(
    !!localStorage.getItem('access_token')
  );
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();

  // Get current user
  const { data: user, isLoading } = useQuery<User>(
    ['auth', 'me'],
    () => authAPI.getMe().then(res => res.data),
    {
      enabled: isAuthenticated,
      retry: false,
      onError: () => {
        setIsAuthenticated(false);
        localStorage.removeItem('access_token');
      },
    }
  );

  // Login mutation
  const loginMutation = useMutation(
    (data: LoginRequest) => authAPI.login(data),
    {
      onSuccess: (response) => {
        const { access_token } = response.data;
        localStorage.setItem('access_token', access_token);
        setIsAuthenticated(true);
        queryClient.invalidateQueries(['auth', 'me']);
        enqueueSnackbar('로그인되었습니다.', { variant: 'success' });
      },
      onError: (error: any) => {
        const message = error.response?.data?.detail || '로그인에 실패했습니다.';
        enqueueSnackbar(message, { variant: 'error' });
      },
    }
  );

  // Register mutation
  const registerMutation = useMutation(
    (data: RegisterRequest) => authAPI.register(data),
    {
      onSuccess: () => {
        enqueueSnackbar('회원가입이 완료되었습니다. 로그인해주세요.', { variant: 'success' });
      },
      onError: (error: any) => {
        const message = error.response?.data?.detail || '회원가입에 실패했습니다.';
        enqueueSnackbar(message, { variant: 'error' });
      },
    }
  );

  const login = async (data: LoginRequest) => {
    await loginMutation.mutateAsync(data);
  };

  const register = async (data: RegisterRequest) => {
    await registerMutation.mutateAsync(data);
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    setIsAuthenticated(false);
    queryClient.clear();
    enqueueSnackbar('로그아웃되었습니다.', { variant: 'info' });
  };

  const value: AuthContextType = {
    user: user || null,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};