import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Tabs,
  Tab,
  TextField,
  Button,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  FormControlLabel,
  Alert,
  Snackbar,
  Divider,
  Chip,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import { settingsAPI } from '../services/api';
import { UserSettings, UserSettingsCreate, RailType } from '../types';
import { useAuth } from '../hooks/useAuth';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const SettingsPage: React.FC = () => {
  const { railType } = useAuth();
  const [tabValue, setTabValue] = useState(0);
  const [srtSettings, setSrtSettings] = useState<UserSettings | null>(null);
  const [ktxSettings, setKtxSettings] = useState<UserSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [alert, setAlert] = useState<{ show: boolean; message: string; severity: 'success' | 'error' | 'info' }>({
    show: false,
    message: '',
    severity: 'info'
  });
  
  // Station data
  const [srtStations, setSrtStations] = useState<string[]>([]);
  const [ktxStations, setKtxStations] = useState<string[]>([]);
  
  // Form states - default to user's rail type
  const defaultRailType = (railType as RailType) || 'SRT';
  const [loginForm, setLoginForm] = useState({ rail_type: defaultRailType, login_id: '', password: '' });
  const [telegramForm, setTelegramForm] = useState({ rail_type: defaultRailType, token: '', chat_id: '', enabled: false });
  const [cardForm, setCardForm] = useState({ rail_type: defaultRailType, card_number: '', card_password: '', card_birthday: '', card_expire: '', auto_payment: false });
  const [stationForm, setStationForm] = useState({ rail_type: defaultRailType, favorite_stations: [] as string[], default_departure: '', default_arrival: '' });
  const [passengerForm, setPassengerForm] = useState({
    rail_type: defaultRailType,
    default_adult_count: 1,
    default_child_count: 0,
    default_senior_count: 0,
    default_disability1to3_count: 0,
    default_disability4to6_count: 0,
    passenger_options: [] as string[]
  });
  
  // Test dialogs
  const [testDialog, setTestDialog] = useState({ open: false, type: '', loading: false, result: '' });

  useEffect(() => {
    loadSettings();
    loadStations();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      
      // If user has a specific rail type, only load settings for that type
      if (railType) {
        try {
          const response = await settingsAPI.getByRailType(railType);
          if (railType === 'SRT') {
            setSrtSettings(response.data);
          } else {
            setKtxSettings(response.data);
          }
          populateFormFromSettings(response.data, railType);
        } catch (error: any) {
          if (error.response?.status !== 404) {
            console.error(`Error loading ${railType} settings:`, error);
          }
        }
      } else {
        // Load both if no specific rail type (fallback)
        // Load SRT settings
        try {
          const srtResponse = await settingsAPI.getByRailType('SRT');
          setSrtSettings(srtResponse.data);
          populateFormFromSettings(srtResponse.data, 'SRT');
        } catch (error: any) {
          if (error.response?.status !== 404) {
            console.error('Error loading SRT settings:', error);
          }
        }
        
        // Load KTX settings
        try {
          const ktxResponse = await settingsAPI.getByRailType('KTX');
          setKtxSettings(ktxResponse.data);
          populateFormFromSettings(ktxResponse.data, 'KTX');
        } catch (error: any) {
          if (error.response?.status !== 404) {
            console.error('Error loading KTX settings:', error);
          }
        }
      }
      
    } catch (error) {
      console.error('Error loading settings:', error);
      showAlert('설정을 불러오는데 실패했습니다', 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadStations = async () => {
    try {
      const [srtResponse, ktxResponse] = await Promise.all([
        settingsAPI.getStations('SRT'),
        settingsAPI.getStations('KTX')
      ]);
      setSrtStations(srtResponse.data.stations);
      setKtxStations(ktxResponse.data.stations);
    } catch (error) {
      console.error('Error loading stations:', error);
    }
  };

  const populateFormFromSettings = (settings: UserSettings, railType: string) => {
    if (railType === 'SRT' || railType === 'KTX') {
      setLoginForm(prev => ({ ...prev, rail_type: railType, login_id: settings.login_id || '' }));
      setTelegramForm(prev => ({ 
        ...prev, 
        rail_type: railType,
        chat_id: settings.telegram_chat_id || '',
        enabled: settings.telegram_enabled 
      }));
      setCardForm(prev => ({ ...prev, rail_type: railType, auto_payment: settings.auto_payment }));
      setStationForm(prev => ({
        ...prev,
        rail_type: railType,
        favorite_stations: settings.favorite_stations || [],
        default_departure: settings.default_departure || '',
        default_arrival: settings.default_arrival || ''
      }));
      setPassengerForm(prev => ({
        ...prev,
        rail_type: railType,
        default_adult_count: settings.default_adult_count,
        default_child_count: settings.default_child_count,
        default_senior_count: settings.default_senior_count,
        default_disability1to3_count: settings.default_disability1to3_count,
        default_disability4to6_count: settings.default_disability4to6_count,
        passenger_options: settings.passenger_options || []
      }));
    }
  };

  const showAlert = (message: string, severity: 'success' | 'error' | 'info') => {
    setAlert({ show: true, message, severity });
  };

  const getSettings = (railType: string) => railType === 'SRT' ? srtSettings : ktxSettings;
  const getStations = (railType: string) => railType === 'SRT' ? srtStations : ktxStations;

  const saveSettings = async (railType: RailType, formData: Partial<UserSettingsCreate>) => {
    try {
      setSaving(true);
      const existingSettings = getSettings(railType);
      
      const settingsData: UserSettingsCreate = {
        rail_type: railType,
        user_id: 0, // Will be set by backend
        ...formData
      };

      if (existingSettings) {
        await settingsAPI.update(existingSettings.id, settingsData);
      } else {
        await settingsAPI.create(settingsData);
      }
      
      await loadSettings(); // Reload settings
      showAlert('설정이 저장되었습니다', 'success');
    } catch (error) {
      console.error('Error saving settings:', error);
      showAlert('설정 저장에 실패했습니다', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleTestLogin = async () => {
    if (!loginForm.login_id || !loginForm.password) {
      showAlert('아이디와 비밀번호를 입력해주세요', 'error');
      return;
    }

    setTestDialog({ open: true, type: 'login', loading: true, result: '' });
    
    try {
      const response = await settingsAPI.testLogin(loginForm.rail_type, {
        login_id: loginForm.login_id,
        password: loginForm.password
      });
      
      setTestDialog(prev => ({ ...prev, loading: false, result: response.data.message }));
    } catch (error: any) {
      setTestDialog(prev => ({ ...prev, loading: false, result: error.response?.data?.message || '테스트 실패' }));
    }
  };

  const handleTestTelegram = async () => {
    if (!telegramForm.token || !telegramForm.chat_id) {
      showAlert('토큰과 채팅 ID를 입력해주세요', 'error');
      return;
    }

    setTestDialog({ open: true, type: 'telegram', loading: true, result: '' });
    
    try {
      const response = await settingsAPI.testTelegram(telegramForm.rail_type, {
        token: telegramForm.token,
        chat_id: telegramForm.chat_id
      });
      
      setTestDialog(prev => ({ ...prev, loading: false, result: response.data.message }));
    } catch (error: any) {
      setTestDialog(prev => ({ ...prev, loading: false, result: error.response?.data?.message || '테스트 실패' }));
    }
  };

  const handleSaveLogin = () => {
    saveSettings(loginForm.rail_type, {
      login_id: loginForm.login_id,
      encrypted_password: loginForm.password // Will be encrypted by backend
    });
  };

  const handleSaveTelegram = () => {
    saveSettings(telegramForm.rail_type, {
      telegram_token: telegramForm.token, // Will be encrypted by backend
      telegram_chat_id: telegramForm.chat_id,
      telegram_enabled: telegramForm.enabled
    });
  };

  const handleSaveCard = () => {
    saveSettings(cardForm.rail_type, {
      card_number: cardForm.card_number, // Will be encrypted by backend
      card_password: cardForm.card_password, // Will be encrypted by backend
      card_birthday: cardForm.card_birthday, // Will be encrypted by backend
      card_expire: cardForm.card_expire, // Will be encrypted by backend
      auto_payment: cardForm.auto_payment
    });
  };

  const handleSaveStation = () => {
    saveSettings(stationForm.rail_type, {
      favorite_stations: stationForm.favorite_stations,
      default_departure: stationForm.default_departure,
      default_arrival: stationForm.default_arrival
    });
  };

  const handleSavePassenger = () => {
    saveSettings(passengerForm.rail_type, {
      default_adult_count: passengerForm.default_adult_count,
      default_child_count: passengerForm.default_child_count,
      default_senior_count: passengerForm.default_senior_count,
      default_disability1to3_count: passengerForm.default_disability1to3_count,
      default_disability4to6_count: passengerForm.default_disability4to6_count,
      passenger_options: passengerForm.passenger_options
    });
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        설정 관리 {railType && <Chip label={railType} color={railType === 'SRT' ? 'secondary' : 'primary'} />}
      </Typography>

      {railType && (
        <Alert severity="info" sx={{ mb: 2 }}>
          {railType} 계정으로 로그인하셨습니다. {railType} 관련 설정만 관리할 수 있습니다.
        </Alert>
      )}

      <Card>
        <Tabs value={tabValue} onChange={(_, value) => setTabValue(value)} sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tab label="로그인 설정" />
          <Tab label="텔레그램 설정" />
          <Tab label="카드 설정" />
          <Tab label="역 설정" />
          <Tab label="승객 설정" />
        </Tabs>

        {/* 로그인 설정 */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            {!railType && (
              <Grid item xs={12}>
                <FormControl sx={{ minWidth: 120, mb: 2 }}>
                  <InputLabel>열차 종류</InputLabel>
                  <Select
                    value={loginForm.rail_type}
                    label="열차 종류"
                    onChange={(e) => setLoginForm(prev => ({ ...prev, rail_type: e.target.value as RailType }))}
                  >
                    <MenuItem value="SRT">SRT</MenuItem>
                    <MenuItem value="KTX">KTX</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            )}
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="아이디"
                value={loginForm.login_id}
                onChange={(e) => setLoginForm(prev => ({ ...prev, login_id: e.target.value }))}
                placeholder="멤버십 번호, 이메일, 전화번호"
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="password"
                label="비밀번호"
                value={loginForm.password}
                onChange={(e) => setLoginForm(prev => ({ ...prev, password: e.target.value }))}
              />
            </Grid>
            
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button variant="outlined" onClick={handleTestLogin} disabled={saving}>
                  로그인 테스트
                </Button>
                <Button variant="contained" onClick={handleSaveLogin} disabled={saving}>
                  {saving ? <CircularProgress size={20} /> : '저장'}
                </Button>
              </Box>
            </Grid>
          </Grid>
        </TabPanel>

        {/* 텔레그램 설정 */}
        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={3}>
            {!railType && (
              <Grid item xs={12}>
                <FormControl sx={{ minWidth: 120, mb: 2 }}>
                  <InputLabel>열차 종류</InputLabel>
                  <Select
                    value={telegramForm.rail_type}
                    label="열차 종류"
                    onChange={(e) => setTelegramForm(prev => ({ ...prev, rail_type: e.target.value as RailType }))}
                  >
                    <MenuItem value="SRT">SRT</MenuItem>
                    <MenuItem value="KTX">KTX</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            )}
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="텔레그램 봇 토큰"
                value={telegramForm.token}
                onChange={(e) => setTelegramForm(prev => ({ ...prev, token: e.target.value }))}
                placeholder="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
              />
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="채팅 ID"
                value={telegramForm.chat_id}
                onChange={(e) => setTelegramForm(prev => ({ ...prev, chat_id: e.target.value }))}
                placeholder="123456789"
              />
            </Grid>
            
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={telegramForm.enabled}
                    onChange={(e) => setTelegramForm(prev => ({ ...prev, enabled: e.target.checked }))}
                  />
                }
                label="텔레그램 알림 활성화"
              />
            </Grid>
            
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button variant="outlined" onClick={handleTestTelegram} disabled={saving}>
                  테스트 메시지 전송
                </Button>
                <Button variant="contained" onClick={handleSaveTelegram} disabled={saving}>
                  {saving ? <CircularProgress size={20} /> : '저장'}
                </Button>
              </Box>
            </Grid>
          </Grid>
        </TabPanel>

        {/* 카드 설정 */}
        <TabPanel value={tabValue} index={2}>
          <Grid container spacing={3}>
            {!railType && (
              <Grid item xs={12}>
                <FormControl sx={{ minWidth: 120, mb: 2 }}>
                  <InputLabel>열차 종류</InputLabel>
                  <Select
                    value={cardForm.rail_type}
                    label="열차 종류"
                    onChange={(e) => setCardForm(prev => ({ ...prev, rail_type: e.target.value as RailType }))}
                  >
                    <MenuItem value="SRT">SRT</MenuItem>
                    <MenuItem value="KTX">KTX</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            )}
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="카드 번호"
                value={cardForm.card_number}
                onChange={(e) => setCardForm(prev => ({ ...prev, card_number: e.target.value }))}
                placeholder="1234-1234-1234-1234"
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="password"
                label="카드 비밀번호"
                value={cardForm.card_password}
                onChange={(e) => setCardForm(prev => ({ ...prev, card_password: e.target.value }))}
                placeholder="앞 2자리"
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="생년월일"
                value={cardForm.card_birthday}
                onChange={(e) => setCardForm(prev => ({ ...prev, card_birthday: e.target.value }))}
                placeholder="YYMMDD"
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="유효기간"
                value={cardForm.card_expire}
                onChange={(e) => setCardForm(prev => ({ ...prev, card_expire: e.target.value }))}
                placeholder="MMYY"
              />
            </Grid>
            
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={cardForm.auto_payment}
                    onChange={(e) => setCardForm(prev => ({ ...prev, auto_payment: e.target.checked }))}
                  />
                }
                label="자동 결제 활성화"
              />
            </Grid>
            
            <Grid item xs={12}>
              <Button variant="contained" onClick={handleSaveCard} disabled={saving}>
                {saving ? <CircularProgress size={20} /> : '저장'}
              </Button>
            </Grid>
          </Grid>
        </TabPanel>

        {/* 역 설정 */}
        <TabPanel value={tabValue} index={3}>
          <Grid container spacing={3}>
            {!railType && (
              <Grid item xs={12}>
                <FormControl sx={{ minWidth: 120, mb: 2 }}>
                  <InputLabel>열차 종류</InputLabel>
                  <Select
                    value={stationForm.rail_type}
                    label="열차 종류"
                    onChange={(e) => setStationForm(prev => ({ ...prev, rail_type: e.target.value as RailType }))}
                  >
                    <MenuItem value="SRT">SRT</MenuItem>
                    <MenuItem value="KTX">KTX</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            )}
            
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>기본 출발역</InputLabel>
                <Select
                  value={stationForm.default_departure}
                  label="기본 출발역"
                  onChange={(e) => setStationForm(prev => ({ ...prev, default_departure: e.target.value }))}
                >
                  {getStations(stationForm.rail_type).map(station => (
                    <MenuItem key={station} value={station}>{station}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>기본 도착역</InputLabel>
                <Select
                  value={stationForm.default_arrival}
                  label="기본 도착역"
                  onChange={(e) => setStationForm(prev => ({ ...prev, default_arrival: e.target.value }))}
                >
                  {getStations(stationForm.rail_type).map(station => (
                    <MenuItem key={station} value={station}>{station}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>즐겨찾는 역</Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                {stationForm.favorite_stations.map(station => (
                  <Chip
                    key={station}
                    label={station}
                    onDelete={() => setStationForm(prev => ({
                      ...prev,
                      favorite_stations: prev.favorite_stations.filter(s => s !== station)
                    }))}
                  />
                ))}
              </Box>
              
              <FormControl fullWidth>
                <InputLabel>역 추가</InputLabel>
                <Select
                  value=""
                  label="역 추가"
                  onChange={(e) => {
                    const station = e.target.value;
                    if (station && !stationForm.favorite_stations.includes(station)) {
                      setStationForm(prev => ({
                        ...prev,
                        favorite_stations: [...prev.favorite_stations, station]
                      }));
                    }
                  }}
                >
                  {getStations(stationForm.rail_type).map(station => (
                    <MenuItem key={station} value={station}>{station}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12}>
              <Button variant="contained" onClick={handleSaveStation} disabled={saving}>
                {saving ? <CircularProgress size={20} /> : '저장'}
              </Button>
            </Grid>
          </Grid>
        </TabPanel>

        {/* 승객 설정 */}
        <TabPanel value={tabValue} index={4}>
          <Grid container spacing={3}>
            {!railType && (
              <Grid item xs={12}>
                <FormControl sx={{ minWidth: 120, mb: 2 }}>
                  <InputLabel>열차 종류</InputLabel>
                  <Select
                    value={passengerForm.rail_type}
                    label="열차 종류"
                    onChange={(e) => setPassengerForm(prev => ({ ...prev, rail_type: e.target.value as RailType }))}
                  >
                    <MenuItem value="SRT">SRT</MenuItem>
                    <MenuItem value="KTX">KTX</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            )}
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="성인"
                value={passengerForm.default_adult_count}
                onChange={(e) => setPassengerForm(prev => ({ ...prev, default_adult_count: parseInt(e.target.value) || 0 }))}
                inputProps={{ min: 0, max: 10 }}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="어린이"
                value={passengerForm.default_child_count}
                onChange={(e) => setPassengerForm(prev => ({ ...prev, default_child_count: parseInt(e.target.value) || 0 }))}
                inputProps={{ min: 0, max: 10 }}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="경로우대"
                value={passengerForm.default_senior_count}
                onChange={(e) => setPassengerForm(prev => ({ ...prev, default_senior_count: parseInt(e.target.value) || 0 }))}
                inputProps={{ min: 0, max: 10 }}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="중증장애인"
                value={passengerForm.default_disability1to3_count}
                onChange={(e) => setPassengerForm(prev => ({ ...prev, default_disability1to3_count: parseInt(e.target.value) || 0 }))}
                inputProps={{ min: 0, max: 10 }}
              />
            </Grid>
            
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>예매 옵션</Typography>
              <Box>
                {['child', 'senior', 'disability1to3', 'disability4to6'].map(option => (
                  <FormControlLabel
                    key={option}
                    control={
                      <Checkbox
                        checked={passengerForm.passenger_options.includes(option)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setPassengerForm(prev => ({
                              ...prev,
                              passenger_options: [...prev.passenger_options, option]
                            }));
                          } else {
                            setPassengerForm(prev => ({
                              ...prev,
                              passenger_options: prev.passenger_options.filter(o => o !== option)
                            }));
                          }
                        }}
                      />
                    }
                    label={
                      option === 'child' ? '어린이' :
                      option === 'senior' ? '경로우대' :
                      option === 'disability1to3' ? '중증장애인' :
                      option === 'disability4to6' ? '경증장애인' : option
                    }
                  />
                ))}
              </Box>
            </Grid>
            
            <Grid item xs={12}>
              <Button variant="contained" onClick={handleSavePassenger} disabled={saving}>
                {saving ? <CircularProgress size={20} /> : '저장'}
              </Button>
            </Grid>
          </Grid>
        </TabPanel>
      </Card>

      {/* Test Dialog */}
      <Dialog open={testDialog.open} onClose={() => setTestDialog(prev => ({ ...prev, open: false }))}>
        <DialogTitle>
          {testDialog.type === 'login' ? '로그인 테스트' : '텔레그램 테스트'}
        </DialogTitle>
        <DialogContent>
          {testDialog.loading ? (
            <Box display="flex" alignItems="center" gap={2}>
              <CircularProgress size={20} />
              <Typography>테스트 중...</Typography>
            </Box>
          ) : (
            <Typography>{testDialog.result}</Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTestDialog(prev => ({ ...prev, open: false }))}>
            닫기
          </Button>
        </DialogActions>
      </Dialog>

      {/* Alert Snackbar */}
      <Snackbar
        open={alert.show}
        autoHideDuration={6000}
        onClose={() => setAlert(prev => ({ ...prev, show: false }))}
      >
        <Alert severity={alert.severity} onClose={() => setAlert(prev => ({ ...prev, show: false }))}>
          {alert.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default SettingsPage;