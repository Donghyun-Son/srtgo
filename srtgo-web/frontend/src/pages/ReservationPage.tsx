import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Stepper,
  Step,
  StepLabel,
  Grid,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useMutation } from 'react-query';
import { useSnackbar } from 'notistack';
import { reservationsAPI } from '../services/api';
import { ReservationCreate } from '../types';

// Step components (to be implemented)
import BasicInfoStep from '../components/reservation/BasicInfoStep';
import TrainSelectionStep from '../components/reservation/TrainSelectionStep';
import PassengerInfoStep from '../components/reservation/PassengerInfoStep';
import ConfirmationStep from '../components/reservation/ConfirmationStep';

const steps = [
  '기본 정보',
  '열차 선택',
  '승객 정보',
  '확인',
];

const ReservationPage: React.FC = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [reservationData, setReservationData] = useState<Partial<ReservationCreate>>({});
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();

  const createReservationMutation = useMutation(
    (data: ReservationCreate) => reservationsAPI.create(data),
    {
      onSuccess: (response) => {
        enqueueSnackbar('예매가 시작되었습니다!', { variant: 'success' });
        navigate(`/monitor/${response.data.id}`);
      },
      onError: (error: any) => {
        const message = error.response?.data?.detail || '예매 시작에 실패했습니다.';
        enqueueSnackbar(message, { variant: 'error' });
      },
    }
  );

  const handleNext = () => {
    if (activeStep < steps.length - 1) {
      setActiveStep(prev => prev + 1);
    } else {
      // Final step - create reservation
      createReservationMutation.mutate(reservationData as ReservationCreate);
    }
  };

  const handleBack = () => {
    setActiveStep(prev => prev - 1);
  };

  const handleStepData = (stepData: any) => {
    setReservationData(prev => ({ ...prev, ...stepData }));
  };

  const isStepValid = () => {
    switch (activeStep) {
      case 0:
        return !!(
          reservationData.rail_type &&
          reservationData.departure_station &&
          reservationData.arrival_station &&
          reservationData.departure_date &&
          reservationData.departure_time
        );
      case 1:
        return !!(reservationData.selected_trains && reservationData.selected_trains.length > 0);
      case 2:
        return !!(reservationData.passengers && reservationData.seat_type);
      case 3:
        return true;
      default:
        return false;
    }
  };

  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return (
          <BasicInfoStep
            data={reservationData}
            onDataChange={handleStepData}
          />
        );
      case 1:
        return (
          <TrainSelectionStep
            data={reservationData}
            onDataChange={handleStepData}
          />
        );
      case 2:
        return (
          <PassengerInfoStep
            data={reservationData}
            onDataChange={handleStepData}
          />
        );
      case 3:
        return (
          <ConfirmationStep
            data={reservationData}
            onDataChange={handleStepData}
          />
        );
      default:
        return null;
    }
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        새 예매
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Stepper activeStep={activeStep} alternativeLabel>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          {renderStepContent()}

          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
            <Button
              onClick={handleBack}
              disabled={activeStep === 0}
            >
              이전
            </Button>
            <Button
              variant="contained"
              onClick={handleNext}
              disabled={!isStepValid() || createReservationMutation.isLoading}
            >
              {activeStep === steps.length - 1 ? '예매 시작' : '다음'}
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default ReservationPage;