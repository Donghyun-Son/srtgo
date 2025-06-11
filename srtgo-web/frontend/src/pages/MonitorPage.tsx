import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  LinearProgress,
  Alert,
  Button,
  List,
  ListItem,
  ListItemText,
  IconButton,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Stop as StopIcon,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { reservationsAPI } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import { WebSocketMessage, ReservationStatus } from '../types';

const MonitorPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [logs, setLogs] = useState<string[]>([]);
  const [wsStatus, setWsStatus] = useState<string>('연결 중...');

  const { data: reservation, refetch } = useQuery(
    ['reservation', id],
    () => reservationsAPI.getById(parseInt(id!)).then(res => res.data),
    {
      enabled: !!id,
      refetchInterval: 5000,
    }
  );

  const { isConnected } = useWebSocket({
    onMessage: (message: WebSocketMessage) => {
      if (message.reservation_id?.toString() === id) {
        const timestamp = new Date().toLocaleTimeString();
        let logMessage = `[${timestamp}] `;
        
        switch (message.type) {
          case 'reservation_update':
            logMessage += `상태 업데이트: ${message.message}`;
            break;
          case 'reservation_progress':
            logMessage += `진행 상황: ${message.message} (${message.attempt_count}회 시도)`;
            break;
          case 'reservation_success':
            logMessage += `✅ 예매 성공! ${message.message}`;
            break;
          case 'reservation_failed':
            logMessage += `❌ 예매 실패: ${message.error}`;
            break;
          case 'reservation_error':
            logMessage += `⚠️ 오류 발생: ${message.error}`;
            break;
          default:
            logMessage += `알림: ${message.message}`;
        }
        
        setLogs(prev => [logMessage, ...prev.slice(0, 99)]); // Keep last 100 logs
        refetch(); // Refresh reservation data
      }
    },
    onOpen: () => setWsStatus('연결됨'),
    onClose: () => setWsStatus('연결 끊김'),
    onError: () => setWsStatus('연결 오류'),
  });

  useEffect(() => {
    if (isConnected) {
      setWsStatus('연결됨');
    }
  }, [isConnected]);

  const getStatusColor = (status: ReservationStatus) => {
    switch (status) {
      case 'pending': return 'default';
      case 'running': return 'warning';
      case 'success': return 'success';
      case 'failed': return 'error';
      case 'cancelled': return 'secondary';
      default: return 'default';
    }
  };

  const getStatusLabel = (status: ReservationStatus) => {
    switch (status) {
      case 'pending': return '대기중';
      case 'running': return '실행중';
      case 'success': return '성공';
      case 'failed': return '실패';
      case 'cancelled': return '취소됨';
      default: return status;
    }
  };

  const handleCancel = () => {
    // TODO: Cancel reservation
    console.log('Cancel reservation', id);
  };

  if (!reservation) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
        <Typography>예매 정보를 불러오는 중...</Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          예매 모니터링
        </Typography>
        <Box>
          <IconButton onClick={() => refetch()} sx={{ mr: 1 }}>
            <RefreshIcon />
          </IconButton>
          {reservation.status === 'running' && (
            <Button
              variant="contained"
              color="error"
              startIcon={<StopIcon />}
              onClick={handleCancel}
            >
              예매 중지
            </Button>
          )}
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Reservation Info */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                예매 정보
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemText
                    primary="열차"
                    secondary={
                      <Chip
                        label={reservation.rail_type}
                        color={reservation.rail_type === 'SRT' ? 'secondary' : 'primary'}
                        size="small"
                      />
                    }
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="구간"
                    secondary={`${reservation.departure_station} → ${reservation.arrival_station}`}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="출발일시"
                    secondary={`${reservation.departure_date.slice(0, 4)}-${reservation.departure_date.slice(4, 6)}-${reservation.departure_date.slice(6, 8)} ${reservation.departure_time.slice(0, 2)}:${reservation.departure_time.slice(2, 4)}`}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="상태"
                    secondary={
                      <Chip
                        label={getStatusLabel(reservation.status)}
                        color={getStatusColor(reservation.status)}
                        size="small"
                      />
                    }
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Progress Info */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                진행 상황
              </Typography>
              <Box mb={2}>
                <Typography variant="body2" color="text.secondary">
                  시도 횟수: {reservation.attempt_count}회
                </Typography>
                {reservation.status === 'running' && (
                  <LinearProgress sx={{ mt: 1 }} />
                )}
              </Box>
              <Typography variant="body2">
                {reservation.progress_message || '대기 중...'}
              </Typography>
              <Box mt={2}>
                <Typography variant="body2" color="text.secondary">
                  WebSocket: {wsStatus}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Success Info */}
        {reservation.status === 'success' && reservation.reserved_train_info && (
          <Grid item xs={12}>
            <Alert severity="success">
              <Typography variant="h6">예매 성공!</Typography>
              <Typography variant="body2">
                {JSON.stringify(reservation.reserved_train_info, null, 2)}
              </Typography>
            </Alert>
          </Grid>
        )}

        {/* Error Info */}
        {reservation.status === 'failed' && reservation.error_message && (
          <Grid item xs={12}>
            <Alert severity="error">
              <Typography variant="h6">예매 실패</Typography>
              <Typography variant="body2">
                {reservation.error_message}
              </Typography>
            </Alert>
          </Grid>
        )}

        {/* Real-time Logs */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                실시간 로그
              </Typography>
              <Box
                sx={{
                  height: 300,
                  overflowY: 'auto',
                  backgroundColor: 'grey.100',
                  p: 2,
                  fontFamily: 'monospace',
                  fontSize: '0.875rem',
                }}
              >
                {logs.length === 0 ? (
                  <Typography color="text.secondary">
                    로그가 없습니다. WebSocket 연결을 확인해주세요.
                  </Typography>
                ) : (
                  logs.map((log, index) => (
                    <div key={index}>{log}</div>
                  ))
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default MonitorPage;