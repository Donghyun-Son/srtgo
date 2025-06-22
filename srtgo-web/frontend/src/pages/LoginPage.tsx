import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Box,
  Typography,
  TextField,
  Button,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { useAuth } from '../hooks/useAuth';
import { LoginRequest, RailType } from '../types';

const loginSchema = yup.object({
  username: yup.string().required('사용자명을 입력해주세요'),
  password: yup.string().required('비밀번호를 입력해주세요'),
  rail_type: yup.string().oneOf(['SRT', 'KTX'], '열차 종류를 선택해주세요').required('열차 종류를 선택해주세요'),
});

const LoginPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login, isAuthenticated } = useAuth();

  const loginForm = useForm<LoginRequest>({
    resolver: yupResolver(loginSchema),
    defaultValues: {
      username: '',
      password: '',
      rail_type: 'SRT' as const,
    },
  });

  useEffect(() => {
    console.log('isAuthenticated changed:', isAuthenticated);
    if (isAuthenticated) {
      console.log('Navigating to dashboard...');
      // Small delay to ensure state is properly updated
      setTimeout(() => {
        navigate('/dashboard');
      }, 100);
    }
  }, [isAuthenticated, navigate]);

  const handleLogin = async (data: LoginRequest) => {
    console.log('handleLogin called with:', data);
    
    // 데이터 검증
    if (!data.username || !data.password || !data.rail_type) {
      console.error('Invalid form data:', data);
      return;
    }
    
    setLoading(true);
    try {
      console.log('Attempting login with:', data);
      await login(data);
      console.log('Login successful');
    } catch (error) {
      console.error('Login error:', error);
      // Error is already handled by useAuth hook with snackbar
    } finally {
      setLoading(false);
    }
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    console.log('Form submit event triggered');
    e.preventDefault(); // 명시적으로 새로고침 방지
    e.stopPropagation(); // 이벤트 전파도 중단
    
    // react-hook-form validation 먼저 실행
    const isValid = loginForm.formState.isValid;
    console.log('Form is valid:', isValid);
    
    if (isValid) {
      const formData = loginForm.getValues();
      handleLogin(formData);
    } else {
      console.log('Form validation failed:', loginForm.formState.errors);
    }
  };

  const handleButtonClick = (e: React.MouseEvent) => {
    console.log('Login button clicked');
    e.preventDefault(); // 버튼 기본 동작 방지
    
    // 수동으로 폼 데이터 가져와서 제출
    const formData = loginForm.getValues();
    console.log('Form data from button click:', formData);
    handleLogin(formData);
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
            KTX/SRT 기차표 예매 시스템
          </Typography>

          <Box component="form" onSubmit={handleFormSubmit} sx={{ mt: 3 }}>
            <FormControl fullWidth margin="normal" required>
              <InputLabel id="rail-type-label">열차 종류</InputLabel>
              <Select
                labelId="rail-type-label"
                id="rail-type"
                label="열차 종류"
                {...loginForm.register('rail_type')}
                error={!!loginForm.formState.errors.rail_type}
                value={loginForm.watch('rail_type')}
                onChange={(e) => loginForm.setValue('rail_type', e.target.value as RailType)}
              >
                <MenuItem value="SRT">SRT (수서고속철도)</MenuItem>
                <MenuItem value="KTX">KTX (한국고속철도)</MenuItem>
              </Select>
              {loginForm.formState.errors.rail_type && (
                <Typography variant="caption" color="error" sx={{ mt: 1, ml: 2 }}>
                  {loginForm.formState.errors.rail_type.message}
                </Typography>
              )}
            </FormControl>
            
            <TextField
              margin="normal"
              required
              fullWidth
              id="login-username"
              label="사용자 ID"
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
              type="button"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={loading}
              onClick={handleButtonClick}
            >
              {loading ? <CircularProgress size={24} /> : '로그인'}
            </Button>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};

export default LoginPage;