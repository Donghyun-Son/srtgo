import React, { createContext, useContext, useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useSnackbar } from 'notistack';
import { authAPI } from '../services/api';
import { User, LoginRequest, RegisterRequest } from '../types';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  railType: string | null;
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

  // For SRT/KTX login, we don't have a traditional user endpoint
  // So we'll store user info differently
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [railType, setRailType] = useState<string | null>(null);
  
  // Function to decode JWT token and extract rail_type
  const extractRailTypeFromToken = (token: string) => {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      const payload = JSON.parse(jsonPayload);
      return payload.rail_type || null;
    } catch (e) {
      console.error('Failed to decode token:', e);
      return null;
    }
  };
  
  // Check if user info exists in localStorage on mount
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const userInfo = localStorage.getItem('user_info');
    const storedRailType = localStorage.getItem('rail_type');
    
    if (token && userInfo) {
      try {
        const parsedUser = JSON.parse(userInfo);
        
        // Check if user has valid ID, if not extract from token
        if (parsedUser.id === 0) {
          try {
            const base64Url = token.split('.')[1];
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            const jsonPayload = decodeURIComponent(
              atob(base64)
                .split('')
                .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
                .join('')
            );
            const payload = JSON.parse(jsonPayload);
            if (payload.user_id) {
              parsedUser.id = payload.user_id;
              localStorage.setItem('user_info', JSON.stringify(parsedUser));
            }
          } catch (e) {
            console.error('Failed to extract user_id from existing token:', e);
          }
        }
        
        setUser(parsedUser);
        setIsAuthenticated(true);
        
        // First try to get rail_type from localStorage, then from token
        if (storedRailType) {
          setRailType(storedRailType);
        } else {
          // Extract rail_type from token as fallback
          const extractedRailType = extractRailTypeFromToken(token);
          setRailType(extractedRailType);
          if (extractedRailType) {
            localStorage.setItem('rail_type', extractedRailType);
          }
        }
      } catch (e) {
        console.error('Failed to parse user info:', e);
      }
    }
  }, []);

  // Login mutation
  const loginMutation = useMutation(
    (data: LoginRequest) => authAPI.login(data),
    {
      onSuccess: (response, variables) => {
        console.log('Login API success:', response.data);
        const { access_token } = response.data;
        localStorage.setItem('access_token', access_token);
        
        // Extract rail_type from token
        const extractedRailType = extractRailTypeFromToken(access_token);
        setRailType(extractedRailType);
        
        // Store rail_type separately for easy access
        if (extractedRailType) {
          localStorage.setItem('rail_type', extractedRailType);
        }
        
        // Extract user_id from token
        const extractedUserId = (() => {
          try {
            const base64Url = access_token.split('.')[1];
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            const jsonPayload = decodeURIComponent(
              atob(base64)
                .split('')
                .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
                .join('')
            );
            const payload = JSON.parse(jsonPayload);
            return payload.user_id || 0;
          } catch (e) {
            console.error('Failed to extract user_id from token:', e);
            return 0;
          }
        })();

        // Create a simple user object from login data
        const simpleUser: User = {
          id: extractedUserId,
          username: variables.username,
          email: `${variables.username}@${variables.rail_type.toLowerCase()}.com`,
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
        setUser(simpleUser);
        
        // Store user info in localStorage
        localStorage.setItem('user_info', JSON.stringify(simpleUser));
        
        console.log('Setting isAuthenticated to true...');
        setIsAuthenticated(true);
        queryClient.invalidateQueries(['auth', 'me']);
        enqueueSnackbar('로그인되었습니다.', { variant: 'success' });
      },
      onError: (error: any) => {
        console.log('Login API error:', error);
        const message = error.response?.data?.detail || '로그인에 실패했습니다.';
        console.log('Showing error message:', message);
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
    console.log('useAuth login called with:', data);
    try {
      console.log('Calling loginMutation.mutateAsync...');
      await loginMutation.mutateAsync(data);
      console.log('loginMutation.mutateAsync completed');
    } catch (error) {
      console.log('loginMutation.mutateAsync error:', error);
      throw error; // Re-throw to let the caller handle it
    }
  };

  const register = async (data: RegisterRequest) => {
    await registerMutation.mutateAsync(data);
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_info');
    localStorage.removeItem('rail_type');
    setIsAuthenticated(false);
    setUser(null);
    setRailType(null);
    queryClient.clear();
    enqueueSnackbar('로그아웃되었습니다.', { variant: 'info' });
  };

  const value: AuthContextType = {
    user: user || null,
    isAuthenticated,
    isLoading,
    railType,
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};