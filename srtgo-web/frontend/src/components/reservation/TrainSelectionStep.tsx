import React, { useState, useEffect, useCallback } from 'react';
import {
  Typography,
  Button,
  Box,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Checkbox,
  Chip,
  Alert,
  FormControlLabel,
  Switch,
  IconButton,
  Tooltip,
} from '@mui/material';
import { 
  Search as SearchIcon, 
  SelectAll as SelectAllIcon,
  Deselect as DeselectIcon 
} from '@mui/icons-material';
import { settingsAPI } from '../../services/api';
import { Train } from '../../types';
import { useAuth } from '../../hooks/useAuth';

interface TrainSelectionStepProps {
  data: any;
  onDataChange: (data: any) => void;
}


const TrainSelectionStep: React.FC<TrainSelectionStepProps> = ({ data, onDataChange }) => {
  const { railType } = useAuth();
  const [trains, setTrains] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedTrains, setSelectedTrains] = useState<number[]>(data.selected_trains || []);
  const [error, setError] = useState<string>('');
  const [backendMessage, setBackendMessage] = useState<string>('');
  const [showSoldOutTrains, setShowSoldOutTrains] = useState(false);
  const [includeNoSeats, setIncludeNoSeats] = useState(false);

  // Keyboard shortcuts for train selection
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (trains.length === 0) return;
    
    // Ctrl+A or Cmd+A: Select all trains
    if ((event.ctrlKey || event.metaKey) && event.key === 'a') {
      event.preventDefault();
      const availableTrainIndices = trains
        .map((train, index) => ({ train, index }))
        .filter(({ train }) => !train.sold_out && train.bookable)
        .map(({ index }) => index);
      setSelectedTrains(availableTrainIndices);
      return;
    }
    
    // Ctrl+R or Cmd+R: Deselect all trains
    if ((event.ctrlKey || event.metaKey) && event.key === 'r') {
      event.preventDefault();
      setSelectedTrains([]);
      return;
    }
  }, [trains]);

  // Add keyboard event listener
  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown]);

  // Select/Deselect all functions
  const selectAllAvailable = () => {
    const availableTrainIndices = trains
      .map((train, index) => ({ train, index }))
      .filter(({ train }) => !train.sold_out && train.bookable)
      .map(({ index }) => index);
    setSelectedTrains(availableTrainIndices);
  };

  const deselectAll = () => {
    setSelectedTrains([]);
  };

  const searchTrains = async () => {
    // Use railType from auth context instead of data.rail_type
    const currentRailType = railType || data.rail_type;
    
    if (!currentRailType || !data.departure_station || !data.arrival_station || !data.departure_date) {
      setError('필수 정보가 누락되었습니다');
      return;
    }

    // Check if user can access the requested rail type
    if (railType && railType !== currentRailType) {
      setError(`${railType} 계정으로 로그인하셨으므로 ${currentRailType} 기차는 조회할 수 없습니다.`);
      return;
    }

    setLoading(true);
    setError('');
    setBackendMessage('');
    
    try {
      // Format date for API (YYYYMMDD)
      const formattedDate = data.departure_date.replace(/-/g, '');
      const formattedTime = data.departure_time ? data.departure_time.replace(':', '') + '00' : '000000';

      const response = await settingsAPI.searchTrains(currentRailType, {
        departure: data.departure_station,
        arrival: data.arrival_station,
        date: formattedDate,
        time: formattedTime,
        available_only: railType === 'SRT' ? !showSoldOutTrains : true,
        include_no_seats: railType === 'KTX' ? includeNoSeats : false,
      });

      if (response.data.success) {
        setTrains(response.data.trains || []);
        setError('');
        // Handle backend message if provided
        if (response.data.message) {
          setBackendMessage(response.data.message);
        }
      } else {
        setError(response.data.message || '열차 검색에 실패했습니다');
        setTrains([]);
      }
    } catch (error: any) {
      console.error('Failed to search trains:', error);
      const errorData = error.response?.data;
      const errorCode = errorData?.code;
      
      if (errorCode === 'BOT_DETECTED') {
        setError('🤖 ' + (errorData?.detail || '봇으로 감지되었습니다. 잠시 후 다시 시도해주세요.'));
      } else if (errorCode === 'SESSION_EXPIRED' || errorCode === 'INVALID_CREDENTIALS') {
        setError('🔐 세션이 만료되었습니다. 다시 로그인해주세요.');
      } else if (error.response?.status === 400 && errorData?.detail?.includes('credentials')) {
        setError('⚙️ 로그인 정보가 설정되지 않았습니다. 설정 페이지에서 로그인 정보를 먼저 설정해주세요.');
      } else {
        setError(errorData?.detail || errorData?.message || '열차 검색 중 오류가 발생했습니다');
      }
      setTrains([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    onDataChange({ selected_trains: selectedTrains });
  }, [selectedTrains, onDataChange]);

  const handleTrainSelection = (trainIndex: number) => {
    console.log('handleTrainSelection called with index:', trainIndex);
    setSelectedTrains(prev => {
      console.log('Previous selected trains:', prev);
      const newSelection = prev.includes(trainIndex) 
        ? prev.filter(i => i !== trainIndex)
        : [...prev, trainIndex];
      console.log('New selected trains:', newSelection);
      return newSelection;
    });
  };

  // 시간 형식 변환 함수들
  const formatTime = (timeString: string) => {
    try {
      // HHMMSS 형식을 HH시 MM분으로 변환
      if (timeString && timeString.length >= 4) {
        const hour = timeString.substring(0, 2);
        const minute = timeString.substring(2, 4);
        return `${hour}시 ${minute}분`;
      }
      return timeString;
    } catch {
      return timeString;
    }
  };

  const calculateTravelTime = (departureTime: string, arrivalTime: string) => {
    try {
      // HHMMSS 형식에서 시간과 분 추출
      const depHour = parseInt(departureTime.substring(0, 2));
      const depMin = parseInt(departureTime.substring(2, 4));
      const arrHour = parseInt(arrivalTime.substring(0, 2));
      const arrMin = parseInt(arrivalTime.substring(2, 4));
      
      let totalMinutes = (arrHour * 60 + arrMin) - (depHour * 60 + depMin);
      if (totalMinutes < 0) totalMinutes += 24 * 60; // Handle next day arrival
      
      const hours = Math.floor(totalMinutes / 60);
      const minutes = totalMinutes % 60;
      
      if (hours > 0) {
        return minutes > 0 ? `${hours}시간 ${minutes}분` : `${hours}시간`;
      } else {
        return `${minutes}분`;
      }
    } catch {
      return '-';
    }
  };

  const getSeatStatus = (train: any) => {
    const chips = [];
    
    // 일반실 상태 표시
    if (train.general_seat_state) {
      const color = train.general_seat_state === '예약가능' ? 'success' : 
                   train.general_seat_state === '예약대기' ? 'warning' : 'default';
      chips.push(
        <Chip 
          key="general" 
          label={`일반실: ${train.general_seat_state}`} 
          color={color as any} 
          size="small" 
          sx={{ mr: 0.5 }} 
        />
      );
    }
    
    // 특실 상태 표시
    if (train.special_seat_state) {
      const color = train.special_seat_state === '예약가능' ? 'primary' : 
                   train.special_seat_state === '예약대기' ? 'warning' : 'default';
      chips.push(
        <Chip 
          key="special" 
          label={`특실: ${train.special_seat_state}`} 
          color={color as any} 
          size="small" 
          sx={{ mr: 0.5 }} 
        />
      );
    }
    
    // 완전 매진인 경우
    if (train.sold_out) {
      chips.push(
        <Chip key="soldout" label="매진" color="error" size="small" />
      );
    }

    return <Box display="flex" flexWrap="wrap" gap={0.5}>{chips}</Box>;
  };

  // 모든 열차가 매진인지 확인하는 함수
  const areAllTrainsSoldOut = () => {
    return trains.length > 0 && trains.every(train => 
      train.sold_out || 
      (train.general_seat_state === '매진' && train.special_seat_state === '매진')
    );
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        열차를 검색하고 선택해주세요
      </Typography>

      <Box mb={2}>
        <Box display="flex" alignItems="center" gap={2} flexWrap="wrap">
          <Button
            variant="contained"
            startIcon={<SearchIcon />}
            onClick={searchTrains}
            disabled={loading || (!railType && !data.rail_type) || !data.departure_station || !data.arrival_station}
          >
            {loading ? <CircularProgress size={20} /> : '열차 검색'}
          </Button>
          
          {railType === 'SRT' && (
            <FormControlLabel
              control={
                <Switch
                  checked={showSoldOutTrains}
                  onChange={(e) => setShowSoldOutTrains(e.target.checked)}
                  color="primary"
                />
              }
              label="매진된 열차도 표시"
            />
          )}
          
          {railType === 'KTX' && (
            <FormControlLabel
              control={
                <Switch
                  checked={includeNoSeats}
                  onChange={(e) => setIncludeNoSeats(e.target.checked)}
                  color="primary"
                />
              }
              label="좌석 없는 열차도 표시"
            />
          )}
        </Box>
        
        {trains.length > 0 && (
          <Box display="flex" alignItems="center" gap={1} mt={1}>
            <Tooltip title="예약 가능한 모든 열차 선택 (Ctrl+A)">
              <IconButton 
                size="small" 
                onClick={selectAllAvailable}
                color="primary"
              >
                <SelectAllIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="모든 선택 해제 (Ctrl+R)">
              <IconButton 
                size="small" 
                onClick={deselectAll}
                color="default"
              >
                <DeselectIcon />
              </IconButton>
            </Tooltip>
            <Typography variant="caption" color="text.secondary">
              키보드 단축키: Ctrl+A (전체선택), Ctrl+R (선택해제)
            </Typography>
          </Box>
        )}
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {(!railType && !data.rail_type) || !data.departure_station || !data.arrival_station ? (
        <Alert severity="info">
          먼저 기본 정보를 입력해주세요.
        </Alert>
      ) : trains.length === 0 && !loading && !error ? (
        <>
          {backendMessage ? (
            <Alert severity="info">
              {backendMessage}
            </Alert>
          ) : (
            <Alert severity="warning">
              열차를 검색해주세요.
            </Alert>
          )}
        </>
      ) : trains.length > 0 ? (
        <>
          {/* 모든 열차가 매진인 경우 안내 메시지 */}
          {areAllTrainsSoldOut() && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              <Box>
                <Typography variant="body2" fontWeight="bold" gutterBottom>
                  🚫 모든 열차가 매진되었습니다
                </Typography>
                <Typography variant="body2">
                  • 예약 대기나 취소표 모니터링을 원하시면 매진된 열차를 선택하여 예약을 시도해보세요<br/>
                  • 다른 시간대나 날짜를 검색해보시거나, 나중에 다시 확인해주세요<br/>
                  {!showSoldOutTrains && '• "매진된 열차도 표시" 옵션을 체크하면 더 많은 열차를 볼 수 있습니다'}
                </Typography>
              </Box>
            </Alert>
          )}
        </>
      ) : null}

      {trains.length > 0 && (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell padding="checkbox">선택</TableCell>
                <TableCell>열차</TableCell>
                <TableCell>출발시간</TableCell>
                <TableCell>도착시간</TableCell>
                <TableCell>소요시간</TableCell>
                <TableCell>좌석현황</TableCell>
                <TableCell align="right">요금</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <CircularProgress />
                  </TableCell>
                </TableRow>
              ) : (
                trains.map((train, index) => (
                  <TableRow
                    key={train.train_no || index}
                    hover
                    onClick={() => handleTrainSelection(index)}
                    sx={{ cursor: 'pointer' }}
                  >
                    <TableCell padding="checkbox" onClick={(e) => e.stopPropagation()}>
                      <Checkbox
                        checked={selectedTrains.includes(index)}
                        onChange={() => handleTrainSelection(index)}
                      />
                    </TableCell>
                    <TableCell>
                      <Box>
                        <Typography variant="body2" fontWeight="bold">
                          {train.train_name || `${railType || data.rail_type} ${train.train_no}`}
                        </Typography>
                        <Chip
                          label={railType || data.rail_type}
                          color={(railType || data.rail_type) === 'SRT' ? 'secondary' : 'primary'}
                          size="small"
                        />
                      </Box>
                    </TableCell>
                    <TableCell>{formatTime(train.departure_time)}</TableCell>
                    <TableCell>{formatTime(train.arrival_time)}</TableCell>
                    <TableCell>
                      {train.travel_time || 
                        (train.departure_time && train.arrival_time ? 
                          calculateTravelTime(train.departure_time, train.arrival_time) : 
                          '-')}
                    </TableCell>
                    <TableCell>{getSeatStatus(train)}</TableCell>
                    <TableCell align="right">
                      {train.price ? `${train.price.toLocaleString()}원` : '-'}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {selectedTrains.length > 0 && (
        <Alert severity="success" sx={{ mt: 2 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="body2">
              {selectedTrains.length}개의 열차가 선택되었습니다.
            </Typography>
            <Box display="flex" gap={1}>
              <Chip 
                label={`선택: ${selectedTrains.length}`} 
                color="primary" 
                size="small" 
              />
              <Chip 
                label={`전체: ${trains.length}`} 
                color="default" 
                size="small" 
              />
            </Box>
          </Box>
        </Alert>
      )}
      
      {trains.length > 0 && selectedTrains.length === 0 && (
        <Alert severity="info" sx={{ mt: 2 }}>
          예약하실 열차를 선택해주세요. 다중 선택이 가능합니다.
        </Alert>
      )}
    </Box>
  );
};

export default TrainSelectionStep;