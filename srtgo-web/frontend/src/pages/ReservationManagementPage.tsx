import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Card,
  CardContent,
  Button,
  Alert,
  Box,
  Grid,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Train as TrainIcon,
  Payment as PaymentIcon,
  Cancel as CancelIcon,
  Refresh as RefreshIcon,
  Telegram as TelegramIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  ErrorOutline as ErrorIcon
} from '@mui/icons-material';
import { useAuth } from '../hooks/useAuth';
import api from '../services/api';

interface ReservationItem {
  id: string | null;
  is_ticket: boolean;
  status: 'paid' | 'unpaid';
  rail_type: string;
  description: string;
  departure_time?: string;
  arrival_time?: string;
  departure_station?: string;
  arrival_station?: string;
  train_name?: string;
  train_no?: string;
  price?: string;
  passenger_count?: number;
  seat_info: Array<{
    description: string;
    car?: string;
    seat?: string;
    seat_type?: string;
  }>;
  raw_data: any;
}

const ReservationManagementPage: React.FC = () => {
  const { user, railType } = useAuth();
  const [reservations, setReservations] = useState<ReservationItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [confirmDialog, setConfirmDialog] = useState<{
    open: boolean;
    title: string;
    message: string;
    action: () => void;
  }>({
    open: false,
    title: '',
    message: '',
    action: () => {}
  });

  const fetchReservations = async () => {
    if (!railType) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.get(`/reservations/all/${railType}`);
      if (response.data.success) {
        setReservations(response.data.reservations || []);
      } else {
        setError(response.data.message || '예약 조회에 실패했습니다');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || '예약 조회 중 오류가 발생했습니다');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReservations();
  }, [railType]);

  const handleCancel = async (reservation: ReservationItem) => {
    setActionLoading(`cancel_${reservation.id}`);
    
    try {
      const response = await api.post(`/reservations/cancel/${railType}`, reservation.raw_data);
      if (response.data.success) {
        await fetchReservations(); // Refresh list
        setConfirmDialog({ ...confirmDialog, open: false });
      } else {
        setError(response.data.message || '취소에 실패했습니다');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || '취소 중 오류가 발생했습니다');
    } finally {
      setActionLoading(null);
    }
  };

  const handlePay = async (reservation: ReservationItem) => {
    setActionLoading(`pay_${reservation.id}`);
    
    try {
      const response = await api.post(`/reservations/pay/${railType}`, reservation.raw_data);
      if (response.data.success) {
        await fetchReservations(); // Refresh list
      } else {
        setError(response.data.message || '결제에 실패했습니다');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || '결제 중 오류가 발생했습니다');
    } finally {
      setActionLoading(null);
    }
  };

  const handleSendToTelegram = async () => {
    setActionLoading('telegram');
    
    try {
      const response = await api.post(`/reservations/send-to-telegram/${railType}`, reservations);
      if (response.data.success) {
        // Show success message
      } else {
        setError(response.data.message || '텔레그램 전송에 실패했습니다');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || '텔레그램 전송 중 오류가 발생했습니다');
    } finally {
      setActionLoading(null);
    }
  };

  const openConfirmDialog = (title: string, message: string, action: () => void) => {
    setConfirmDialog({
      open: true,
      title,
      message,
      action
    });
  };

  const getStatusChip = (reservation: ReservationItem) => {
    if (reservation.is_ticket) {
      return <Chip label="발권완료" color="success" size="small" icon={<CheckCircleIcon />} />;
    } else {
      return <Chip label="결제대기" color="warning" size="small" icon={<ScheduleIcon />} />;
    }
  };

  const formatTime = (time: string | undefined) => {
    if (!time) return '';
    return time.replace(/(\d{2})(\d{2})(\d{2})/, '$1:$2');
  };

  if (!user) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Alert severity="error">로그인이 필요합니다</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Paper elevation={3} sx={{ p: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h4" component="h1">
            예매 내역 관리
            <Chip 
              label={railType} 
              color={railType === 'SRT' ? 'error' : 'info'} 
              sx={{ ml: 2 }} 
            />
          </Typography>
          <Box>
            <Tooltip title="새로고침">
              <IconButton onClick={fetchReservations} disabled={loading}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            {reservations.length > 0 && (
              <Tooltip title="텔레그램으로 전송">
                <IconButton 
                  onClick={handleSendToTelegram} 
                  disabled={actionLoading === 'telegram'}
                  color="primary"
                >
                  {actionLoading === 'telegram' ? <CircularProgress size={24} /> : <TelegramIcon />}
                </IconButton>
              </Tooltip>
            )}
          </Box>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {loading ? (
          <Box display="flex" justifyContent="center" p={4}>
            <CircularProgress />
          </Box>
        ) : reservations.length === 0 ? (
          <Box textAlign="center" p={4}>
            <ErrorIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary">
              예매 내역이 없습니다
            </Typography>
          </Box>
        ) : (
          <Grid container spacing={2}>
            {reservations.map((reservation, index) => (
              <Grid item xs={12} key={`${reservation.id}_${index}`}>
                <Card variant="outlined">
                  <CardContent>
                    <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                      <Box display="flex" alignItems="center" gap={1}>
                        <TrainIcon color="primary" />
                        <Typography variant="h6">
                          {reservation.train_name || '열차 정보'} {reservation.train_no && `(${reservation.train_no})`}
                        </Typography>
                        {getStatusChip(reservation)}
                      </Box>
                      <Box display="flex" gap={1}>
                        {!reservation.is_ticket && (
                          <>
                            <Button
                              variant="contained"
                              color="primary"
                              size="small"
                              startIcon={<PaymentIcon />}
                              onClick={() => handlePay(reservation)}
                              disabled={actionLoading === `pay_${reservation.id}`}
                            >
                              {actionLoading === `pay_${reservation.id}` ? <CircularProgress size={16} /> : '결제'}
                            </Button>
                            <Button
                              variant="outlined"
                              color="error"
                              size="small"
                              startIcon={<CancelIcon />}
                              onClick={() => openConfirmDialog(
                                '예약 취소',
                                '정말로 이 예약을 취소하시겠습니까?',
                                () => handleCancel(reservation)
                              )}
                              disabled={actionLoading === `cancel_${reservation.id}`}
                            >
                              {actionLoading === `cancel_${reservation.id}` ? <CircularProgress size={16} /> : '취소'}
                            </Button>
                          </>
                        )}
                        {reservation.is_ticket && (
                          <Button
                            variant="outlined"
                            color="error"
                            size="small"
                            startIcon={<CancelIcon />}
                            onClick={() => openConfirmDialog(
                              '티켓 환불',
                              '정말로 이 티켓을 환불하시겠습니까?',
                              () => handleCancel(reservation)
                            )}
                            disabled={actionLoading === `cancel_${reservation.id}`}
                          >
                            {actionLoading === `cancel_${reservation.id}` ? <CircularProgress size={16} /> : '환불'}
                          </Button>
                        )}
                      </Box>
                    </Box>

                    <Grid container spacing={2}>
                      <Grid item xs={12} md={6}>
                        <Typography variant="body2" color="text.secondary">
                          여행 정보
                        </Typography>
                        <Typography variant="body1">
                          {reservation.departure_station} → {reservation.arrival_station}
                        </Typography>
                        <Typography variant="body2">
                          {formatTime(reservation.departure_time)} → {formatTime(reservation.arrival_time)}
                        </Typography>
                      </Grid>
                      
                      {reservation.seat_info.length > 0 && (
                        <Grid item xs={12} md={6}>
                          <Typography variant="body2" color="text.secondary">
                            좌석 정보
                          </Typography>
                          <List dense>
                            {reservation.seat_info.map((seat, seatIndex) => (
                              <ListItem key={seatIndex} sx={{ py: 0 }}>
                                <ListItemText 
                                  primary={seat.description}
                                  secondary={seat.car && seat.seat ? `${seat.car}호차 ${seat.seat}` : undefined}
                                />
                              </ListItem>
                            ))}
                          </List>
                        </Grid>
                      )}
                    </Grid>

                    <Typography variant="body2" sx={{ mt: 2, p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                      {reservation.description}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </Paper>

      {/* Confirmation Dialog */}
      <Dialog open={confirmDialog.open} onClose={() => setConfirmDialog({ ...confirmDialog, open: false })}>
        <DialogTitle>{confirmDialog.title}</DialogTitle>
        <DialogContent>
          <Typography>{confirmDialog.message}</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialog({ ...confirmDialog, open: false })}>
            취소
          </Button>
          <Button onClick={confirmDialog.action} color="primary" variant="contained">
            확인
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default ReservationManagementPage;