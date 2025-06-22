import React, { useEffect } from 'react';
import {
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Typography,
  Chip,
  Box,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import dayjs, { Dayjs } from 'dayjs';
import { useAuth } from '../../hooks/useAuth';
import 'dayjs/locale/ko';

dayjs.locale('ko');

interface BasicInfoStepProps {
  data: any;
  onDataChange: (data: any) => void;
}

// Mock data - in real app, fetch from API
const stations = {
  SRT: ['수서', '동탄', '평택지제', '대전', '동대구', '부산', '광주송정', '목포'],
  KTX: ['서울', '용산', '광명', '천안아산', '대전', '동대구', '부산', '광주송정', '목포'],
};

const timeOptions = Array.from({ length: 24 }, (_, i) => ({
  value: `${i.toString().padStart(2, '0')}0000`,
  label: `${i.toString().padStart(2, '0')}:00`,
}));

const BasicInfoStep: React.FC<BasicInfoStepProps> = ({ data, onDataChange }) => {
  const { railType } = useAuth();
  const [selectedDate, setSelectedDate] = React.useState<Dayjs | null>(
    data.departure_date ? dayjs(data.departure_date, 'YYYYMMDD') : dayjs().add(1, 'day')
  );

  useEffect(() => {
    if (selectedDate) {
      onDataChange({
        departure_date: selectedDate.format('YYYYMMDD'),
      });
    }
  }, [selectedDate, onDataChange]);

  const handleChange = (field: string, value: any) => {
    onDataChange({ [field]: value });
  };

  const availableStations = data.rail_type ? stations[data.rail_type as keyof typeof stations] : [];

  return (
    <LocalizationProvider dateAdapter={AdapterDayjs} adapterLocale="ko">
      <Typography variant="h6" gutterBottom>
        기본 예매 정보를 입력해주세요
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          {railType ? (
            <Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                열차 종류
              </Typography>
              <Chip 
                label={`${railType} (로그인 시 선택됨)`}
                color={railType === 'SRT' ? 'secondary' : 'primary'}
                variant="outlined"
                size="medium"
                sx={{ height: 40 }}
              />
            </Box>
          ) : (
            <FormControl fullWidth>
              <InputLabel>열차 종류</InputLabel>
              <Select
                value={data.rail_type || ''}
                label="열차 종류"
                onChange={(e) => handleChange('rail_type', e.target.value)}
              >
                <MenuItem value="SRT">SRT</MenuItem>
                <MenuItem value="KTX">KTX</MenuItem>
              </Select>
            </FormControl>
          )}
        </Grid>

        <Grid item xs={12} md={6}>
          <DatePicker
            label="출발일"
            value={selectedDate}
            onChange={(newValue) => setSelectedDate(newValue)}
            minDate={dayjs()}
            maxDate={dayjs().add(30, 'day')}
            slotProps={{
              textField: {
                fullWidth: true,
              },
            }}
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <FormControl fullWidth>
            <InputLabel>출발역</InputLabel>
            <Select
              value={data.departure_station || ''}
              label="출발역"
              onChange={(e) => handleChange('departure_station', e.target.value)}
              disabled={!data.rail_type}
            >
              {availableStations.map((station) => (
                <MenuItem key={station} value={station}>
                  {station}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        <Grid item xs={12} md={6}>
          <FormControl fullWidth>
            <InputLabel>도착역</InputLabel>
            <Select
              value={data.arrival_station || ''}
              label="도착역"
              onChange={(e) => handleChange('arrival_station', e.target.value)}
              disabled={!data.rail_type}
            >
              {availableStations
                .filter((station) => station !== data.departure_station)
                .map((station) => (
                  <MenuItem key={station} value={station}>
                    {station}
                  </MenuItem>
                ))}
            </Select>
          </FormControl>
        </Grid>

        <Grid item xs={12} md={6}>
          <FormControl fullWidth>
            <InputLabel>출발 시간</InputLabel>
            <Select
              value={data.departure_time || ''}
              label="출발 시간"
              onChange={(e) => handleChange('departure_time', e.target.value)}
            >
              {timeOptions.map((time) => (
                <MenuItem key={time.value} value={time.value}>
                  {time.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
      </Grid>
    </LocalizationProvider>
  );
};

export default BasicInfoStep;