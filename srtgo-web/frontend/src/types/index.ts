export interface User {
  id: number;
  username: string;
  email?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email?: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export type RailType = 'SRT' | 'KTX';

export interface UserSettings {
  id: number;
  user_id: number;
  rail_type: RailType;
  login_id?: string;
  encrypted_password?: string;
  favorite_stations: string[];
  default_departure?: string;
  default_arrival?: string;
  default_adult_count: number;
  default_child_count: number;
  default_senior_count: number;
  default_disability1to3_count: number;
  default_disability4to6_count: number;
  passenger_options: string[];
  telegram_token?: string;
  telegram_chat_id?: string;
  telegram_enabled: boolean;
  card_number?: string;
  card_password?: string;
  card_birthday?: string;
  card_expire?: string;
  auto_payment: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserSettingsCreate {
  rail_type: RailType;
  login_id?: string;
  encrypted_password?: string;
  favorite_stations?: string[];
  default_departure?: string;
  default_arrival?: string;
  default_adult_count?: number;
  default_child_count?: number;
  default_senior_count?: number;
  default_disability1to3_count?: number;
  default_disability4to6_count?: number;
  passenger_options?: string[];
  telegram_token?: string;
  telegram_chat_id?: string;
  telegram_enabled?: boolean;
  card_number?: string;
  card_password?: string;
  card_birthday?: string;
  card_expire?: string;
  auto_payment?: boolean;
}

export type ReservationStatus = 'pending' | 'running' | 'success' | 'failed' | 'cancelled';

export interface Reservation {
  id: number;
  user_id: number;
  task_id?: string;
  rail_type: RailType;
  departure_station: string;
  arrival_station: string;
  departure_date: string;
  departure_time: string;
  passengers: Record<string, number>;
  seat_type: string;
  selected_trains: number[];
  auto_payment: boolean;
  status: ReservationStatus;
  progress_message?: string;
  attempt_count: number;
  reserved_train_info?: any;
  error_message?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export interface ReservationCreate {
  rail_type: RailType;
  departure_station: string;
  arrival_station: string;
  departure_date: string;
  departure_time: string;
  passengers: Record<string, number>;
  seat_type: string;
  selected_trains: number[];
  auto_payment?: boolean;
}

export interface Train {
  id: string;
  name: string;
  departure_time: string;
  arrival_time: string;
  departure_station: string;
  arrival_station: string;
  travel_time: string;
  general_available: boolean;
  special_available: boolean;
  waiting_available: boolean;
  price: number;
}

export interface Station {
  name: string;
  code: string;
}

export interface PassengerType {
  key: string;
  label: string;
}

export interface SeatType {
  key: string;
  label: string;
}

export interface WebSocketMessage {
  type: string;
  reservation_id?: number;
  status?: string;
  message?: string;
  attempt_count?: number;
  train_info?: any;
  error?: string;
}