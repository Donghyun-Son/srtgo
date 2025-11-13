import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { authApi } from '../services/api'

interface RegisterForm {
  username: string
  email?: string
  password: string
  confirmPassword: string
}

export default function RegisterPage() {
  const navigate = useNavigate()
  const [error, setError] = useState<string>('')
  const [isLoading, setIsLoading] = useState(false)

  const { register, handleSubmit, watch, formState: { errors } } = useForm<RegisterForm>()
  const password = watch('password')

  const onSubmit = async (data: RegisterForm) => {
    setIsLoading(true)
    setError('')

    try {
      await authApi.register({
        username: data.username,
        email: data.email,
        password: data.password,
      })

      navigate('/login', { state: { message: '회원가입이 완료되었습니다. 로그인해주세요.' } })
    } catch (err: any) {
      setError(err.response?.data?.detail || '회원가입에 실패했습니다.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-primary-600 mb-2">SRTgo</h1>
          <h2 className="text-2xl font-semibold text-gray-900">회원가입</h2>
          <p className="mt-2 text-gray-600">새 계정을 만들어보세요</p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="mt-8 space-y-6 bg-white p-8 rounded-lg shadow-md">
          {error && (
            <div className="bg-red-50 text-red-600 p-3 rounded-md text-sm">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              사용자명 *
            </label>
            <input
              {...register('username', {
                required: '사용자명을 입력하세요',
                minLength: { value: 3, message: '최소 3자 이상이어야 합니다' }
              })}
              type="text"
              className="input"
              placeholder="사용자명"
            />
            {errors.username && (
              <p className="mt-1 text-sm text-red-600">{errors.username.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              이메일 (선택)
            </label>
            <input
              {...register('email')}
              type="email"
              className="input"
              placeholder="email@example.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              비밀번호 *
            </label>
            <input
              {...register('password', {
                required: '비밀번호를 입력하세요',
                minLength: { value: 6, message: '최소 6자 이상이어야 합니다' }
              })}
              type="password"
              className="input"
              placeholder="비밀번호"
            />
            {errors.password && (
              <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              비밀번호 확인 *
            </label>
            <input
              {...register('confirmPassword', {
                required: '비밀번호를 다시 입력하세요',
                validate: value => value === password || '비밀번호가 일치하지 않습니다'
              })}
              type="password"
              className="input"
              placeholder="비밀번호 확인"
            />
            {errors.confirmPassword && (
              <p className="mt-1 text-sm text-red-600">{errors.confirmPassword.message}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full btn btn-primary disabled:opacity-50"
          >
            {isLoading ? '가입 중...' : '회원가입'}
          </button>

          <p className="text-center text-sm text-gray-600">
            이미 계정이 있으신가요?{' '}
            <Link to="/login" className="text-primary-600 hover:text-primary-700 font-medium">
              로그인
            </Link>
          </p>
        </form>
      </div>
    </div>
  )
}
