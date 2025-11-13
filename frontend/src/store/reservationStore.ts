import { create } from 'zustand'

interface ReservationData {
  train_type: string
  departure_station: string
  arrival_station: string
  departure_date: string
  departure_time: string
  passengers: {
    adult: number
    child: number
    senior: number
    disability1to3: number
    disability4to6: number
  }
  selected_trains?: string[]
  seat_type?: string
  auto_payment: boolean
}

interface ReservationState {
  currentReservation: Partial<ReservationData>
  setReservationData: (data: Partial<ReservationData>) => void
  clearReservation: () => void
}

export const useReservationStore = create<ReservationState>((set) => ({
  currentReservation: {},
  setReservationData: (data) =>
    set((state) => ({
      currentReservation: { ...state.currentReservation, ...data },
    })),
  clearReservation: () => set({ currentReservation: {} }),
}))
