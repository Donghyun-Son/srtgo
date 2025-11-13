import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { trainsApi, reservationsApi } from '../services/api'
import { ArrowRight, Users } from 'lucide-react'

interface ReservationForm {
  train_type: string
  departure_station: string
  arrival_station: string
  departure_date: string
  departure_time: string
  adult: number
  child: number
  senior: number
  auto_payment: boolean
}

export default function ReservationPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const { register, handleSubmit, watch, formState: { errors } } = useForm<ReservationForm>({
    defaultValues: {
      train_type: 'SRT',
      adult: 1,
      child: 0,
      senior: 0,
      auto_payment: false,
    }
  })

  const trainType = watch('train_type')

  // Get stations
  const { data: stations } = useQuery({
    queryKey: ['stations', trainType],
    queryFn: async () => {
      const response = await trainsApi.getStations(trainType)
      return response.data
    },
  })

  // Create reservation mutation
  const createReservation = useMutation({
    mutationFn: async (data: ReservationForm) => {
      const reservationData = {
        train_type: data.train_type,
        departure_station: data.departure_station,
        arrival_station: data.arrival_station,
        departure_date: data.departure_date.replace(/-/g, ''),
        departure_time: data.departure_time.replace(/:/g, '') + '00',
        passengers: {
          adult: data.adult,
          child: data.child,
          senior: data.senior,
          disability1to3: 0,
          disability4to6: 0,
        },
        auto_payment: data.auto_payment,
      }

      const response = await reservationsApi.create(reservationData)
      return response.data
    },
    onSuccess: () => {
      navigate('/')
    },
  })

  const onSubmit = (data: ReservationForm) => {
    createReservation.mutate(data)
  }

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">열차 예약</h1>

      <div className="card">
        {/* Progress indicator */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            {['기본 정보', '승객 정보', '확인'].map((label, idx) => (
              <div key={idx} className="flex items-center">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center font-semibold ${
                    step > idx
                      ? 'bg-primary-600 text-white'
                      : step === idx + 1
                      ? 'bg-primary-100 text-primary-600'
                      : 'bg-gray-200 text-gray-600'
                  }`}
                >
                  {idx + 1}
                </div>
                <span className="ml-2 text-sm font-medium">{label}</span>
                {idx < 2 && (
                  <ArrowRight className="mx-4 text-gray-400" size={20} />
                )}
              </div>
            ))}
          </div>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Step 1: Basic Info */}
          {step === 1 && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  열차 종류
                </label>
                <div className="flex gap-4">
                  <label className="flex items-center">
                    <input
                      {...register('train_type')}
                      type="radio"
                      value="SRT"
                      className="mr-2"
                    />
                    <span>SRT</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      {...register('train_type')}
                      type="radio"
                      value="KTX"
                      className="mr-2"
                    />
                    <span>KTX</span>
                  </label>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    출발역
                  </label>
                  <select
                    {...register('departure_station', { required: '출발역을 선택하세요' })}
                    className="input"
                  >
                    <option value="">선택하세요</option>
                    {stations?.map((station: string) => (
                      <option key={station} value={station}>
                        {station}
                      </option>
                    ))}
                  </select>
                  {errors.departure_station && (
                    <p className="mt-1 text-sm text-red-600">{errors.departure_station.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    도착역
                  </label>
                  <select
                    {...register('arrival_station', { required: '도착역을 선택하세요' })}
                    className="input"
                  >
                    <option value="">선택하세요</option>
                    {stations?.map((station: string) => (
                      <option key={station} value={station}>
                        {station}
                      </option>
                    ))}
                  </select>
                  {errors.arrival_station && (
                    <p className="mt-1 text-sm text-red-600">{errors.arrival_station.message}</p>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    출발 날짜
                  </label>
                  <input
                    {...register('departure_date', { required: '날짜를 선택하세요' })}
                    type="date"
                    className="input"
                    min={new Date().toISOString().split('T')[0]}
                  />
                  {errors.departure_date && (
                    <p className="mt-1 text-sm text-red-600">{errors.departure_date.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    출발 시간
                  </label>
                  <input
                    {...register('departure_time', { required: '시간을 선택하세요' })}
                    type="time"
                    className="input"
                  />
                  {errors.departure_time && (
                    <p className="mt-1 text-sm text-red-600">{errors.departure_time.message}</p>
                  )}
                </div>
              </div>

              <div className="flex justify-end">
                <button
                  type="button"
                  onClick={() => setStep(2)}
                  className="btn btn-primary"
                >
                  다음
                </button>
              </div>
            </div>
          )}

          {/* Step 2: Passengers */}
          {step === 2 && (
            <div className="space-y-4">
              <div className="flex items-center gap-2 mb-4">
                <Users size={24} className="text-primary-600" />
                <h3 className="text-lg font-semibold">승객 정보</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    성인
                  </label>
                  <input
                    {...register('adult', {
                      required: true,
                      min: { value: 1, message: '최소 1명' },
                      max: { value: 9, message: '최대 9명' }
                    })}
                    type="number"
                    className="input"
                    min="1"
                    max="9"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    어린이
                  </label>
                  <input
                    {...register('child', {
                      min: { value: 0, message: '최소 0명' },
                      max: { value: 9, message: '최대 9명' }
                    })}
                    type="number"
                    className="input"
                    min="0"
                    max="9"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    경로
                  </label>
                  <input
                    {...register('senior', {
                      min: { value: 0, message: '최소 0명' },
                      max: { value: 9, message: '최대 9명' }
                    })}
                    type="number"
                    className="input"
                    min="0"
                    max="9"
                  />
                </div>
              </div>

              <div className="flex items-center">
                <input
                  {...register('auto_payment')}
                  type="checkbox"
                  className="mr-2"
                />
                <label className="text-sm text-gray-700">
                  자동 결제 (카드 정보가 설정에 저장되어 있어야 합니다)
                </label>
              </div>

              <div className="flex justify-between">
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="btn btn-secondary"
                >
                  이전
                </button>
                <button
                  type="button"
                  onClick={() => setStep(3)}
                  className="btn btn-primary"
                >
                  다음
                </button>
              </div>
            </div>
          )}

          {/* Step 3: Confirm */}
          {step === 3 && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold mb-4">예약 정보 확인</h3>

              <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">열차:</span>
                  <span className="font-medium">{watch('train_type')}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">출발:</span>
                  <span className="font-medium">{watch('departure_station')}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">도착:</span>
                  <span className="font-medium">{watch('arrival_station')}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">날짜:</span>
                  <span className="font-medium">{watch('departure_date')}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">시간:</span>
                  <span className="font-medium">{watch('departure_time')}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">승객:</span>
                  <span className="font-medium">
                    성인 {watch('adult')}명
                    {watch('child') > 0 && `, 어린이 ${watch('child')}명`}
                    {watch('senior') > 0 && `, 경로 ${watch('senior')}명`}
                  </span>
                </div>
              </div>

              <div className="flex justify-between">
                <button
                  type="button"
                  onClick={() => setStep(2)}
                  className="btn btn-secondary"
                >
                  이전
                </button>
                <button
                  type="submit"
                  disabled={createReservation.isPending}
                  className="btn btn-primary disabled:opacity-50"
                >
                  {createReservation.isPending ? '예약 중...' : '예약하기'}
                </button>
              </div>

              {createReservation.isError && (
                <div className="bg-red-50 text-red-600 p-3 rounded-md text-sm">
                  예약 생성에 실패했습니다. 다시 시도해주세요.
                </div>
              )}
            </div>
          )}
        </form>
      </div>
    </div>
  )
}
