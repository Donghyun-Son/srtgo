import React, { useState, useEffect } from 'react';
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
} from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';
import { utilityAPI } from '../../services/api';
import { Train } from '../../types';

interface TrainSelectionStepProps {
  data: any;
  onDataChange: (data: any) => void;
}

// Mock train data for demonstration
const mockTrains: Train[] = [
  {
    id: 'SRT001',
    name: 'SRT 301',
    departure_time: '06:00',
    arrival_time: '08:42',
    departure_station: '수서',
    arrival_station: '부산',
    travel_time: '2시간 42분',
    general_available: true,
    special_available: false,
    waiting_available: true,
    price: 59800,
  },
  {
    id: 'SRT002',
    name: 'SRT 303',
    departure_time: '06:30',
    arrival_time: '09:12',
    departure_station: '수서',
    arrival_station: '부산',
    travel_time: '2시간 42분',
    general_available: false,
    special_available: true,
    waiting_available: false,
    price: 59800,
  },
  {
    id: 'SRT003',
    name: 'SRT 305',
    departure_time: '07:00',
    arrival_time: '09:42',
    departure_station: '수서',
    arrival_station: '부산',
    travel_time: '2시간 42분',
    general_available: true,
    special_available: true,
    waiting_available: false,
    price: 59800,
  },
];

const TrainSelectionStep: React.FC<TrainSelectionStepProps> = ({ data, onDataChange }) => {
  const [trains, setTrains] = useState<Train[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedTrains, setSelectedTrains] = useState<number[]>(data.selected_trains || []);

  const searchTrains = async () => {
    if (!data.rail_type || !data.departure_station || !data.arrival_station || !data.departure_date || !data.departure_time) {
      return;
    }

    setLoading(true);
    try {
      // In real app, call API
      // const response = await utilityAPI.searchTrains({
      //   rail_type: data.rail_type,
      //   departure: data.departure_station,
      //   arrival: data.arrival_station,
      //   date: data.departure_date,
      //   time: data.departure_time,
      // });
      // setTrains(response.data);

      // For now, use mock data
      setTimeout(() => {
        setTrains(mockTrains);
        setLoading(false);
      }, 1000);
    } catch (error) {
      console.error('Failed to search trains:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    onDataChange({ selected_trains: selectedTrains });
  }, [selectedTrains, onDataChange]);

  const handleTrainSelection = (trainIndex: number) => {
    setSelectedTrains(prev => {
      if (prev.includes(trainIndex)) {
        return prev.filter(i => i !== trainIndex);
      } else {
        return [...prev, trainIndex];
      }
    });
  };

  const getSeatStatus = (train: Train) => {
    if (train.general_available || train.special_available) {
      return (
        <Box>
          {train.general_available && (
            <Chip label="일반실" color="success" size="small" sx={{ mr: 0.5 }} />
          )}
          {train.special_available && (
            <Chip label="특실" color="primary" size="small" sx={{ mr: 0.5 }} />
          )}
        </Box>
      );
    } else if (train.waiting_available) {
      return <Chip label="예약대기" color="warning" size="small" />;
    } else {
      return <Chip label="매진" color="error" size="small" />;
    }
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        열차를 검색하고 선택해주세요
      </Typography>

      <Box mb={2}>
        <Button
          variant="contained"
          startIcon={<SearchIcon />}
          onClick={searchTrains}
          disabled={loading || !data.rail_type || !data.departure_station || !data.arrival_station}
        >
          {loading ? <CircularProgress size={20} /> : '열차 검색'}
        </Button>
      </Box>

      {!data.rail_type || !data.departure_station || !data.arrival_station ? (
        <Alert severity="info">
          먼저 기본 정보를 입력해주세요.
        </Alert>
      ) : trains.length === 0 && !loading ? (
        <Alert severity="warning">
          열차를 검색해주세요.
        </Alert>
      ) : (
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
                    key={train.id}
                    hover
                    onClick={() => handleTrainSelection(index)}
                    sx={{ cursor: 'pointer' }}
                  >
                    <TableCell padding="checkbox">
                      <Checkbox
                        checked={selectedTrains.includes(index)}
                        onChange={() => handleTrainSelection(index)}
                      />
                    </TableCell>
                    <TableCell>
                      <Box>
                        <Typography variant="body2" fontWeight="bold">
                          {train.name}
                        </Typography>
                        <Chip
                          label={data.rail_type}
                          color={data.rail_type === 'SRT' ? 'secondary' : 'primary'}
                          size="small"
                        />
                      </Box>
                    </TableCell>
                    <TableCell>{train.departure_time}</TableCell>
                    <TableCell>{train.arrival_time}</TableCell>
                    <TableCell>{train.travel_time}</TableCell>
                    <TableCell>{getSeatStatus(train)}</TableCell>
                    <TableCell align="right">
                      {train.price.toLocaleString()}원
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
          {selectedTrains.length}개의 열차가 선택되었습니다.
        </Alert>
      )}
    </Box>
  );
};

export default TrainSelectionStep;