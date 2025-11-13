import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { reservationsApi } from '../services/api'
import { Calendar, Clock, MapPin, AlertCircle } from 'lucide-react'
import { format } from 'date-fns'

export default function DashboardPage() {
  const { data: reservations, isLoading } = useQuery({
    queryKey: ['reservations'],
    queryFn: async () => {
      const response = await reservationsApi.getAll(10)
      return response.data
    },
  })

  const getStatusBadge = (status: string) => {
    const styles = {
      pending: 'bg-gray-100 text-gray-800',
      searching: 'bg-blue-100 text-blue-800',
      reserved: 'bg-green-100 text-green-800',
      paid: 'bg-purple-100 text-purple-800',
      cancelled: 'bg-red-100 text-red-800',
      failed: 'bg-red-100 text-red-800',
      expired: 'bg-gray-100 text-gray-800',
    }

    const labels = {
      pending: '대기중',
      searching: '검색중',
      reserved: '예약완료',
      paid: '결제완료',
      cancelled: '취소됨',
      failed: '실패',
      expired: '만료됨',
    }

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${styles[status as keyof typeof styles] || styles.pending}`}>
        {labels[status as keyof typeof labels] || status}
      </span>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">대시보드</h1>
        <Link to="/reservation" className="btn btn-primary">
          새 예약
        </Link>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-primary-100 rounded-lg">
              <Calendar className="text-primary-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">전체 예약</p>
              <p className="text-2xl font-bold">{reservations?.length || 0}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-green-100 rounded-lg">
              <Clock className="text-green-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">예약 완료</p>
              <p className="text-2xl font-bold">
                {reservations?.filter((r: any) => r.status === 'reserved' || r.status === 'paid').length || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-blue-100 rounded-lg">
              <AlertCircle className="text-blue-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">검색 중</p>
              <p className="text-2xl font-bold">
                {reservations?.filter((r: any) => r.status === 'searching').length || 0}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Reservations */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">최근 예약</h2>

        {isLoading ? (
          <div className="text-center py-8 text-gray-600">로딩 중...</div>
        ) : !reservations || reservations.length === 0 ? (
          <div className="text-center py-8 text-gray-600">
            <p className="mb-4">예약 내역이 없습니다</p>
            <Link to="/reservation" className="btn btn-primary">
              첫 예약 만들기
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {reservations.map((reservation: any) => (
              <div
                key={reservation.id}
                className="border border-gray-200 rounded-lg p-4 hover:border-primary-300 transition-colors"
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="font-semibold text-lg">{reservation.train_type}</span>
                      {getStatusBadge(reservation.status)}
                    </div>

                    <div className="flex items-center gap-4 text-sm text-gray-600">
                      <div className="flex items-center gap-1">
                        <MapPin size={16} />
                        <span>{reservation.departure_station}</span>
                        <span>→</span>
                        <span>{reservation.arrival_station}</span>
                      </div>

                      <div className="flex items-center gap-1">
                        <Calendar size={16} />
                        <span>
                          {reservation.departure_date.slice(0, 4)}-
                          {reservation.departure_date.slice(4, 6)}-
                          {reservation.departure_date.slice(6, 8)}
                        </span>
                      </div>

                      <div className="flex items-center gap-1">
                        <Clock size={16} />
                        <span>{reservation.departure_time}</span>
                      </div>
                    </div>

                    {reservation.error_message && (
                      <p className="mt-2 text-sm text-red-600">{reservation.error_message}</p>
                    )}
                  </div>

                  <div className="text-sm text-gray-500">
                    {format(new Date(reservation.created_at), 'yyyy-MM-dd HH:mm')}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
