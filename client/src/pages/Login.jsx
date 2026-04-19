import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { Beer, Eye, EyeOff } from 'lucide-react'
import axios from 'axios'
import { useAuthStore } from '../store/authStore'
import { useT } from '../i18n'
import Spinner from '../components/Spinner'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPw, setShowPw] = useState(false)
  const setAuth = useAuthStore((s) => s.setAuth)
  const navigate = useNavigate()
  const t = useT()

  const loginMutation = useMutation({
    mutationFn: (creds) => axios.post('/api/v1/auth/login', creds),
    onSuccess: ({ data }) => {
      setAuth(
        {
          id: data.id,
          name: data.name,
          username: data.username,
          role_name: data.role_name,
          permissions: data.permissions,
        },
        data.access_token,
        data.refresh_token
      )
      navigate('/tables', { replace: true })
    },
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    loginMutation.mutate({ username, password })
  }

  const errorMsg =
    loginMutation.error?.response?.data?.detail ?? loginMutation.error?.message

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950 p-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 bg-amber-500/15 rounded-2xl flex items-center justify-center mb-4">
            <Beer size={32} className="text-amber-500" />
          </div>
          <h1 className="text-2xl font-bold text-gray-100">BarPOS</h1>
          <p className="text-gray-500 text-sm mt-1">{t('login_subtitle')}</p>
        </div>

        <div className="card p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">{t('login_username')}</label>
              <input
                className="input"
                type="text"
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoFocus
              />
            </div>

            <div>
              <label className="label">{t('login_password')}</label>
              <div className="relative">
                <input
                  className="input pr-10"
                  type={showPw ? 'text' : 'password'}
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
                  tabIndex={-1}
                >
                  {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {errorMsg && (
              <p className="text-red-400 text-sm bg-red-900/20 border border-red-800 rounded-lg px-3 py-2">
                {errorMsg}
              </p>
            )}

            <button
              type="submit"
              className="btn-primary w-full justify-center"
              disabled={loginMutation.isPending}
            >
              {loginMutation.isPending ? <Spinner className="text-gray-950" /> : null}
              {loginMutation.isPending ? t('login_pending') : t('login_submit')}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
