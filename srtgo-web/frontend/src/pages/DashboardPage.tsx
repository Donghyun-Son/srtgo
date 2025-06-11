import React from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
} from '@mui/material';
import {
  Add as AddIcon,
  Visibility as VisibilityIcon,
  Cancel as CancelIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useQuery } from 'react-query';
import { reservationsAPI } from '../services/api';
import { Reservation, ReservationStatus } from '../types';

const DashboardPage: React.FC = () => {
  const navigate = useNavigate();

  const { data: reservations, isLoading, refetch } = useQuery(
    ['reservations'],
    () => reservationsAPI.getAll().then(res => res.data),
    {
      refetchInterval: 5000, // Refetch every 5 seconds
    }
  );

  const getStatusColor = (status: ReservationStatus) => {
    switch (status) {
      case 'pending':
        return 'default';
      case 'running':
        return 'warning';
      case 'success':
        return 'success';
      case 'failed':
        return 'error';
      case 'cancelled':
        return 'secondary';
      default:
        return 'default';
    }
  };

  const getStatusLabel = (status: ReservationStatus) => {
    switch (status) {
      case 'pending':
        return '대기중';
      case 'running':
        return '실행중';
      case 'success':
        return '성공';
      case 'failed':
        return '실패';
      case 'cancelled':
        return '취소됨';
      default:
        return status;
    }
  };

  const stats = {
    total: reservations?.length || 0,
    running: reservations?.filter(r => r.status === 'running').length || 0,
    success: reservations?.filter(r => r.status === 'success').length || 0,
    failed: reservations?.filter(r => r.status === 'failed').length || 0,
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          대시보드
        </Typography>
        <Box>
          <IconButton onClick={() => refetch()} sx={{ mr: 1 }}>
            <RefreshIcon />
          </IconButton>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => navigate('/reservation')}
          >
            새 예매
          </Button>
        </Box>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                전체 예매
              </Typography>
              <Typography variant="h4" component="div">
                {stats.total}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                실행중
              </Typography>
              <Typography variant="h4" component="div" color="warning.main">
                {stats.running}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                성공
              </Typography>
              <Typography variant="h4" component="div" color="success.main">
                {stats.success}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                실패
              </Typography>
              <Typography variant="h4" component="div" color="error.main">
                {stats.failed}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Reservations */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            최근 예매 내역
          </Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>열차</TableCell>
                  <TableCell>구간</TableCell>
                  <TableCell>날짜/시간</TableCell>
                  <TableCell>상태</TableCell>
                  <TableCell>진행률</TableCell>
                  <TableCell align="right">작업</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {isLoading ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center">
                      로딩중...
                    </TableCell>
                  </TableRow>
                ) : reservations?.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center">
                      예매 내역이 없습니다.
                    </TableCell>
                  </TableRow>
                ) : (
                  reservations?.slice(0, 10).map((reservation) => (
                    <TableRow key={reservation.id}>
                      <TableCell>
                        <Chip
                          label={reservation.rail_type}
                          color={reservation.rail_type === 'SRT' ? 'secondary' : 'primary'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        {reservation.departure_station} → {reservation.arrival_station}
                      </TableCell>
                      <TableCell>
                        {reservation.departure_date.slice(0, 4)}-
                        {reservation.departure_date.slice(4, 6)}-
                        {reservation.departure_date.slice(6, 8)}{' '}
                        {reservation.departure_time.slice(0, 2)}:
                        {reservation.departure_time.slice(2, 4)}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={getStatusLabel(reservation.status)}
                          color={getStatusColor(reservation.status)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        {reservation.status === 'running'
                          ? `${reservation.attempt_count}회 시도`
                          : reservation.progress_message || '-'}
                      </TableCell>
                      <TableCell align="right">
                        <IconButton
                          size="small"
                          onClick={() => navigate(`/monitor/${reservation.id}`)}
                          title="모니터링"
                        >
                          <VisibilityIcon />
                        </IconButton>
                        {reservation.status === 'running' && (
                          <IconButton
                            size="small"
                            onClick={() => {
                              // TODO: Cancel reservation
                            }}
                            title="취소"
                          >
                            <CancelIcon />
                          </IconButton>
                        )}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
};

export default DashboardPage;