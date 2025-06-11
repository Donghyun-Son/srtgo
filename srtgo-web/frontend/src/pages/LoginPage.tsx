import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Box,
  Typography,
  TextField,
  Button,
  Tab,
  Tabs,
  CircularProgress,
} from '@mui/material';
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { useAuth } from '../hooks/useAuth';
import { LoginRequest, RegisterRequest } from '../types';

const loginSchema = yup.object({
  username: yup.string().required('사용자명을 입력해주세요'),
  password: yup.string().required('비밀번호를 입력해주세요'),
});

const registerSchema = yup.object({
  username: yup.string().required('사용자명을 입력해주세요').min(3, '사용자명은 3자 이상이어야 합니다'),
  email: yup.string().email('올바른 이메일을 입력해주세요'),
  password: yup.string().required('비밀번호를 입력해주세요').min(6, '비밀번호는 6자 이상이어야 합니다'),
  confirmPassword: yup.string()
    .required('비밀번호 확인을 입력해주세요')
    .oneOf([yup.ref('password')], '비밀번호가 일치하지 않습니다'),
});

const LoginPage: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login, register, isAuthenticated } = useAuth();

  const loginForm = useForm<LoginRequest>({
    resolver: yupResolver(loginSchema),
    defaultValues: {
      username: '',
      password: '',
    },
  });

  const registerForm = useForm<RegisterRequest & { confirmPassword: string }>({
    resolver: yupResolver(registerSchema),
    defaultValues: {
      username: '',
      email: '',
      password: '',
      confirmPassword: '',
    },
  });

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);

  const handleLogin = async (data: LoginRequest) => {
    setLoading(true);
    try {
      await login(data);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (data: RegisterRequest & { confirmPassword: string }) => {
    setLoading(true);
    try {
      const { confirmPassword, ...registerData } = data;
      await register(registerData);
      setTabValue(0); // Switch to login tab after successful registration
      registerForm.reset();
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
    loginForm.reset();
    registerForm.reset();
  };

  return (
    <Container component="main" maxWidth="sm">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Paper elevation={3} sx={{ padding: 4, width: '100%' }}>
          <Typography component="h1" variant="h4" align="center" gutterBottom>
            SRTgo Web
          </Typography>
          <Typography variant="body2" align="center" color="text.secondary" gutterBottom>
            기차표 예매 시스템
          </Typography>

          <Box sx={{ borderBottom: 1, borderColor: 'divider', mt: 3 }}>
            <Tabs value={tabValue} onChange={handleTabChange} aria-label="auth tabs">
              <Tab label="로그인" />
              <Tab label="회원가입" />
            </Tabs>
          </Box>

          {/* Login Tab */}
          {tabValue === 0 && (
            <Box component="form" onSubmit={loginForm.handleSubmit(handleLogin)} sx={{ mt: 2 }}>
              <TextField
                margin="normal"
                required
                fullWidth
                id="login-username"
                label="사용자명"
                autoComplete="username"
                autoFocus
                {...loginForm.register('username')}
                error={!!loginForm.formState.errors.username}
                helperText={loginForm.formState.errors.username?.message}
              />
              <TextField
                margin="normal"
                required
                fullWidth
                label="비밀번호"
                type="password"
                id="login-password"
                autoComplete="current-password"
                {...loginForm.register('password')}
                error={!!loginForm.formState.errors.password}
                helperText={loginForm.formState.errors.password?.message}
              />
              <Button
                type="submit"
                fullWidth
                variant="contained"
                sx={{ mt: 3, mb: 2 }}
                disabled={loading}
              >
                {loading ? <CircularProgress size={24} /> : '로그인'}
              </Button>
            </Box>
          )}

          {/* Register Tab */}
          {tabValue === 1 && (
            <Box component="form" onSubmit={registerForm.handleSubmit(handleRegister)} sx={{ mt: 2 }}>
              <TextField
                margin="normal"
                required
                fullWidth
                id="register-username"
                label="사용자명"
                autoComplete="username"
                autoFocus
                {...registerForm.register('username')}
                error={!!registerForm.formState.errors.username}
                helperText={registerForm.formState.errors.username?.message}
              />
              <TextField
                margin="normal"
                fullWidth
                id="register-email"
                label="이메일 (선택사항)"
                type="email"
                autoComplete="email"
                {...registerForm.register('email')}
                error={!!registerForm.formState.errors.email}
                helperText={registerForm.formState.errors.email?.message}
              />
              <TextField
                margin="normal"
                required
                fullWidth
                label="비밀번호"
                type="password"
                id="register-password"
                autoComplete="new-password"
                {...registerForm.register('password')}
                error={!!registerForm.formState.errors.password}
                helperText={registerForm.formState.errors.password?.message}
              />
              <TextField
                margin="normal"
                required
                fullWidth
                label="비밀번호 확인"
                type="password"
                id="register-confirm-password"
                {...registerForm.register('confirmPassword')}
                error={!!registerForm.formState.errors.confirmPassword}
                helperText={registerForm.formState.errors.confirmPassword?.message}
              />
              <Button
                type="submit"
                fullWidth
                variant="contained"
                sx={{ mt: 3, mb: 2 }}
                disabled={loading}
              >
                {loading ? <CircularProgress size={24} /> : '회원가입'}
              </Button>
            </Box>
          )}
        </Paper>
      </Box>
    </Container>
  );
};

export default LoginPage;