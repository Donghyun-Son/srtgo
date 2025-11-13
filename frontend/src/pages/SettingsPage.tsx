import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { credentialsApi } from '../services/api'
import { Train, CreditCard, MessageSquare, Check } from 'lucide-react'

export default function SettingsPage() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'train' | 'card' | 'telegram'>('train')
  const [successMessage, setSuccessMessage] = useState('')

  // Train credentials form
  const trainForm = useForm({
    defaultValues: {
      train_type: 'SRT',
      user_id: '',
      password: '',
    }
  })

  const saveTrainCredential = useMutation({
    mutationFn: (data: any) => credentialsApi.createTrainCredential(data),
    onSuccess: () => {
      setSuccessMessage('열차 로그인 정보가 저장되었습니다')
      setTimeout(() => setSuccessMessage(''), 3000)
      queryClient.invalidateQueries({ queryKey: ['train-credentials'] })
    },
  })

  // Card credentials form
  const cardForm = useForm({
    defaultValues: {
      card_number: '',
      card_password: '',
      birthday: '',
      expire: '',
    }
  })

  const saveCardCredential = useMutation({
    mutationFn: (data: any) => credentialsApi.createCardCredential(data),
    onSuccess: () => {
      setSuccessMessage('카드 정보가 저장되었습니다')
      setTimeout(() => setSuccessMessage(''), 3000)
    },
  })

  // Telegram credentials form
  const telegramForm = useForm({
    defaultValues: {
      token: '',
      chat_id: '',
      is_enabled: true,
    }
  })

  const saveTelegramCredential = useMutation({
    mutationFn: (data: any) => credentialsApi.createTelegramCredential(data),
    onSuccess: () => {
      setSuccessMessage('텔레그램 알림 설정이 저장되었습니다')
      setTimeout(() => setSuccessMessage(''), 3000)
    },
  })

  const tabs = [
    { id: 'train' as const, label: '열차 로그인', icon: Train },
    { id: 'card' as const, label: '카드 정보', icon: CreditCard },
    { id: 'telegram' as const, label: '텔레그램 알림', icon: MessageSquare },
  ]

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">설정</h1>

      {successMessage && (
        <div className="mb-4 bg-green-50 text-green-600 p-4 rounded-md flex items-center gap-2">
          <Check size={20} />
          <span>{successMessage}</span>
        </div>
      )}

      <div className="card">
        {/* Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="flex space-x-4">
            {tabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 py-3 px-4 border-b-2 font-medium transition-colors ${
                    activeTab === tab.id
                      ? 'border-primary-600 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <Icon size={20} />
                  <span>{tab.label}</span>
                </button>
              )
            })}
          </nav>
        </div>

        {/* Train Credentials */}
        {activeTab === 'train' && (
          <form onSubmit={trainForm.handleSubmit((data) => saveTrainCredential.mutate(data))} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                열차 종류
              </label>
              <div className="flex gap-4">
                <label className="flex items-center">
                  <input
                    {...trainForm.register('train_type')}
                    type="radio"
                    value="SRT"
                    className="mr-2"
                  />
                  <span>SRT</span>
                </label>
                <label className="flex items-center">
                  <input
                    {...trainForm.register('train_type')}
                    type="radio"
                    value="KTX"
                    className="mr-2"
                  />
                  <span>KTX</span>
                </label>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                회원번호 / 아이디
              </label>
              <input
                {...trainForm.register('user_id', { required: true })}
                type="text"
                className="input"
                placeholder="회원번호 또는 아이디"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                비밀번호
              </label>
              <input
                {...trainForm.register('password', { required: true })}
                type="password"
                className="input"
                placeholder="비밀번호"
              />
            </div>

            <button
              type="submit"
              disabled={saveTrainCredential.isPending}
              className="btn btn-primary w-full disabled:opacity-50"
            >
              {saveTrainCredential.isPending ? '저장 중...' : '저장'}
            </button>
          </form>
        )}

        {/* Card Credentials */}
        {activeTab === 'card' && (
          <form onSubmit={cardForm.handleSubmit((data) => saveCardCredential.mutate(data))} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                카드번호 (16자리)
              </label>
              <input
                {...cardForm.register('card_number', {
                  required: true,
                  pattern: /^\d{15,16}$/
                })}
                type="text"
                className="input"
                placeholder="1234567812345678"
                maxLength={16}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                카드 비밀번호 (앞 2자리)
              </label>
              <input
                {...cardForm.register('card_password', {
                  required: true,
                  minLength: 2,
                  maxLength: 2
                })}
                type="password"
                className="input"
                placeholder="••"
                maxLength={2}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                생년월일 (YYMMDD)
              </label>
              <input
                {...cardForm.register('birthday', {
                  required: true,
                  pattern: /^\d{6}$/
                })}
                type="text"
                className="input"
                placeholder="990101"
                maxLength={6}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                유효기간 (YYMM)
              </label>
              <input
                {...cardForm.register('expire', {
                  required: true,
                  pattern: /^\d{4}$/
                })}
                type="text"
                className="input"
                placeholder="2512"
                maxLength={4}
              />
            </div>

            <button
              type="submit"
              disabled={saveCardCredential.isPending}
              className="btn btn-primary w-full disabled:opacity-50"
            >
              {saveCardCredential.isPending ? '저장 중...' : '저장'}
            </button>

            <p className="text-sm text-gray-600">
              ⚠️ 카드 정보는 암호화되어 안전하게 저장됩니다.
            </p>
          </form>
        )}

        {/* Telegram Credentials */}
        {activeTab === 'telegram' && (
          <form onSubmit={telegramForm.handleSubmit((data) => saveTelegramCredential.mutate(data))} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                봇 토큰
              </label>
              <input
                {...telegramForm.register('token', { required: true })}
                type="text"
                className="input"
                placeholder="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                채팅 ID
              </label>
              <input
                {...telegramForm.register('chat_id', { required: true })}
                type="text"
                className="input"
                placeholder="123456789"
              />
            </div>

            <div className="flex items-center">
              <input
                {...telegramForm.register('is_enabled')}
                type="checkbox"
                className="mr-2"
              />
              <label className="text-sm text-gray-700">
                알림 활성화
              </label>
            </div>

            <button
              type="submit"
              disabled={saveTelegramCredential.isPending}
              className="btn btn-primary w-full disabled:opacity-50"
            >
              {saveTelegramCredential.isPending ? '저장 중...' : '저장'}
            </button>

            <div className="bg-blue-50 p-4 rounded-md text-sm text-blue-800">
              <p className="font-semibold mb-2">텔레그램 봇 설정 방법:</p>
              <ol className="list-decimal list-inside space-y-1">
                <li>@BotFather에게 /newbot 명령 전송</li>
                <li>봇 이름 및 username 설정</li>
                <li>받은 토큰을 여기에 입력</li>
                <li>봇에게 메시지를 보내고 채팅 ID 확인</li>
              </ol>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
