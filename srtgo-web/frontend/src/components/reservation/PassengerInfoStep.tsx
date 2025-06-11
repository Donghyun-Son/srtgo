import React, { useEffect } from 'react';
import {
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  TextField,
  FormControlLabel,
  Switch,
  Card,
  CardContent,
} from '@mui/material';

interface PassengerInfoStepProps {
  data: any;
  onDataChange: (data: any) => void;
}

const seatTypes = [
  { key: 'GENERAL_FIRST', label: '일반실 우선' },
  { key: 'GENERAL_ONLY', label: '일반실만' },
  { key: 'SPECIAL_FIRST', label: '특실 우선' },
  { key: 'SPECIAL_ONLY', label: '특실만' },
];

const PassengerInfoStep: React.FC<PassengerInfoStepProps> = ({ data, onDataChange }) => {
  const [passengers, setPassengers] = React.useState({
    adult: 1,
    child: 0,
    senior: 0,
    disability1to3: 0,
    disability4to6: 0,
    ...data.passengers,
  });

  useEffect(() => {
    onDataChange({
      passengers,
      seat_type: data.seat_type || 'GENERAL_FIRST',
      auto_payment: data.auto_payment || false,
    });
  }, [passengers, onDataChange]);

  const handlePassengerChange = (type: string, value: number) => {
    setPassengers((prev: Record<string, number>) => ({ ...prev, [type]: value }));
  };

  const handleChange = (field: string, value: any) => {
    onDataChange({ [field]: value });
  };

  const totalPassengers = Object.values(passengers).reduce((sum: number, count: any) => sum + count, 0);

  return (
    <div>
      <Typography variant="h6" gutterBottom>
        승객 정보와 좌석 옵션을 설정해주세요
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                승객 정보
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6} sm={4} md={2}>
                  <TextField
                    fullWidth
                    label="성인"
                    type="number"
                    value={passengers.adult}
                    onChange={(e) => handlePassengerChange('adult', parseInt(e.target.value) || 0)}
                    inputProps={{ min: 0, max: 9 }}
                  />
                </Grid>
                <Grid item xs={6} sm={4} md={2}>
                  <TextField
                    fullWidth
                    label="어린이"
                    type="number"
                    value={passengers.child}
                    onChange={(e) => handlePassengerChange('child', parseInt(e.target.value) || 0)}
                    inputProps={{ min: 0, max: 9 }}
                  />
                </Grid>
                <Grid item xs={6} sm={4} md={2}>
                  <TextField
                    fullWidth
                    label="경로우대"
                    type="number"
                    value={passengers.senior}
                    onChange={(e) => handlePassengerChange('senior', parseInt(e.target.value) || 0)}
                    inputProps={{ min: 0, max: 9 }}
                  />
                </Grid>
                <Grid item xs={6} sm={4} md={3}>
                  <TextField
                    fullWidth
                    label="1~3급 장애인"
                    type="number"
                    value={passengers.disability1to3}
                    onChange={(e) => handlePassengerChange('disability1to3', parseInt(e.target.value) || 0)}
                    inputProps={{ min: 0, max: 9 }}
                  />
                </Grid>
                <Grid item xs={6} sm={4} md={3}>
                  <TextField
                    fullWidth
                    label="4~6급 장애인"
                    type="number"
                    value={passengers.disability4to6}
                    onChange={(e) => handlePassengerChange('disability4to6', parseInt(e.target.value) || 0)}
                    inputProps={{ min: 0, max: 9 }}
                  />
                </Grid>
              </Grid>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                총 승객: {totalPassengers}명
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <FormControl fullWidth>
            <InputLabel>좌석 유형</InputLabel>
            <Select
              value={data.seat_type || 'GENERAL_FIRST'}
              label="좌석 유형"
              onChange={(e) => handleChange('seat_type', e.target.value)}
            >
              {seatTypes.map((type) => (
                <MenuItem key={type.key} value={type.key}>
                  {type.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        <Grid item xs={12}>
          <Card>
            <CardContent>
              <FormControlLabel
                control={
                  <Switch
                    checked={data.auto_payment || false}
                    onChange={(e) => handleChange('auto_payment', e.target.checked)}
                  />
                }
                label="자동 결제 (예매 성공 시 자동으로 결제)"
              />
              <Typography variant="body2" color="text.secondary">
                자동 결제를 위해서는 설정에서 카드 정보를 미리 등록해야 합니다.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </div>
  );
};

export default PassengerInfoStep;