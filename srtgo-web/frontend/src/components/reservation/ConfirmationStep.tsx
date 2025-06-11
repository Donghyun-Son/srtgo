import React from 'react';
import {
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  List,
  ListItem,
  ListItemText,
  Divider,
  Alert,
} from '@mui/material';

interface ConfirmationStepProps {
  data: any;
  onDataChange: (data: any) => void;
}

const ConfirmationStep: React.FC<ConfirmationStepProps> = ({ data }) => {
  const formatDate = (dateStr: string) => {
    if (!dateStr || dateStr.length !== 8) return dateStr;
    return `${dateStr.slice(0, 4)}-${dateStr.slice(4, 6)}-${dateStr.slice(6, 8)}`;
  };

  const formatTime = (timeStr: string) => {
    if (!timeStr || timeStr.length !== 6) return timeStr;
    return `${timeStr.slice(0, 2)}:${timeStr.slice(2, 4)}`;
  };

  const getSeatTypeLabel = (seatType: string) => {
    const types: Record<string, string> = {
      'GENERAL_FIRST': '일반실 우선',
      'GENERAL_ONLY': '일반실만',
      'SPECIAL_FIRST': '특실 우선',
      'SPECIAL_ONLY': '특실만',
    };
    return types[seatType] || seatType;
  };

  const getTotalPassengers = () => {
    if (!data.passengers) return 0;
    return Object.values(data.passengers).reduce((sum: number, count: any) => sum + count, 0);
  };

  const getPassengerSummary = () => {
    if (!data.passengers) return '';
    const summary = [];
    if (data.passengers.adult > 0) summary.push(`성인 ${data.passengers.adult}명`);
    if (data.passengers.child > 0) summary.push(`어린이 ${data.passengers.child}명`);
    if (data.passengers.senior > 0) summary.push(`경로우대 ${data.passengers.senior}명`);
    if (data.passengers.disability1to3 > 0) summary.push(`1~3급 장애인 ${data.passengers.disability1to3}명`);
    if (data.passengers.disability4to6 > 0) summary.push(`4~6급 장애인 ${data.passengers.disability4to6}명`);
    return summary.join(', ');
  };

  return (
    <div>
      <Typography variant="h6" gutterBottom>
        예매 정보를 확인해주세요
      </Typography>

      <Alert severity="info" sx={{ mb: 3 }}>
        아래 정보로 예매를 시작합니다. 예매는 백그라운드에서 실행되므로 페이지를 닫아도 계속 진행됩니다.
      </Alert>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                기본 정보
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemText
                    primary="열차 종류"
                    secondary={
                      <Chip
                        label={data.rail_type}
                        color={data.rail_type === 'SRT' ? 'secondary' : 'primary'}
                        size="small"
                      />
                    }
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="구간"
                    secondary={`${data.departure_station} → ${data.arrival_station}`}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="출발일시"
                    secondary={`${formatDate(data.departure_date)} ${formatTime(data.departure_time)}`}
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                승객 및 좌석 정보
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemText
                    primary="총 승객"
                    secondary={`${getTotalPassengers()}명`}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="승객 구성"
                    secondary={getPassengerSummary()}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="좌석 유형"
                    secondary={getSeatTypeLabel(data.seat_type)}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="자동 결제"
                    secondary={data.auto_payment ? '사용' : '미사용'}
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                선택된 열차
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {data.selected_trains?.length || 0}개의 열차가 선택되었습니다.
              </Typography>
              {data.selected_trains?.length > 0 && (
                <Typography variant="body2">
                  선택된 열차 순서대로 예매를 시도합니다.
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Alert severity="warning" sx={{ mt: 3 }}>
        <Typography variant="body2">
          <strong>주의사항:</strong>
          <br />
          • 예매 시도는 실제 코레일/SRT 시스템에 접속하므로 로그인 정보가 필요합니다.
          <br />
          • 예매가 시작되면 실시간으로 좌석을 확인하며 자동으로 예매를 시도합니다.
          <br />
          • 예매 모니터링 페이지에서 진행 상황을 확인할 수 있습니다.
          <br />
          • 예매 성공 시 텔레그램으로 알림을 받을 수 있습니다. (설정 필요)
        </Typography>
      </Alert>
    </div>
  );
};

export default ConfirmationStep;