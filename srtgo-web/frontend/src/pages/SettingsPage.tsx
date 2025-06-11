import React from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Alert,
} from '@mui/material';

const SettingsPage: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        설정
      </Typography>

      <Alert severity="info" sx={{ mb: 3 }}>
        설정 페이지는 현재 개발 중입니다.
      </Alert>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            구현 예정 설정
          </Typography>
          <ul>
            <li>SRT/KTX 로그인 정보 관리</li>
            <li>텔레그램 알림 설정</li>
            <li>카드 결제 정보 설정</li>
            <li>자주 사용하는 역 설정</li>
            <li>승객 기본값 설정</li>
          </ul>
        </CardContent>
      </Card>
    </Box>
  );
};

export default SettingsPage;