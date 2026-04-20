import { useState } from 'react'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import {
  LayoutGrid,
  UtensilsCrossed,
  Package,
  Users,
  ShieldCheck,
  BarChart2,
  ClipboardList,
  LogOut,
  Menu,
  X,
  Beer,
} from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import { useT, useLangStore, LANGUAGES } from '../i18n'
import api from '../api/client'

const NAV_KEYS = [
  { to: '/tables', tKey: 'nav_tables', icon: LayoutGrid,      perm: 'tables' },
  { to: '/menu',   tKey: 'nav_menu',   icon: UtensilsCrossed, perm: 'items'  },
  { to: '/stock',  tKey: 'nav_stock',  icon: Package,         perm: 'stock'  },
  { to: '/stats',  tKey: 'nav_stats',  icon: BarChart2,       perm: 'stats'  },
  { to: '/users',  tKey: 'nav_users',  icon: Users,           perm: 'users'  },
  { to: '/roles',  tKey: 'nav_roles',  icon: ShieldCheck,     perm: 'roles'  },
  { to: '/audit',  tKey: 'nav_audit',  icon: ClipboardList,   perm: 'roles'  },
]

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { user, refreshToken, clearAuth } = useAuthStore()
  const navigate = useNavigate()
  const t = useT()
  const lang = useLangStore((s) => s.lang)
  const setLang = useLangStore((s) => s.setLang)

  const perms = user?.permissions ?? []

  const logoutMutation = useMutation({
    mutationFn: () => api.post('/auth/logout', { refresh_token: refreshToken }),
    onSettled: () => {
      clearAuth()
      navigate('/login', { replace: true })
    },
  })

  // Low-stock badge: count items with stock_qty <= 3 (only when user has stock perm)
  const { data: lowStockCount = 0 } = useQuery({
    queryKey: ['items', 'low-stock-count'],
    queryFn: () =>
      api.get('/items/').then((r) =>
        r.data.filter((i) => i.stock_qty !== null && i.stock_qty <= 3).length
      ),
    enabled: perms.includes('stock'),
    refetchInterval: 60_000,
  })

  const visibleNav = NAV_KEYS.filter((item) => perms.includes(item.perm))

  const linkClass = ({ isActive }) =>
    `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
      isActive
        ? 'bg-amber-500/15 text-amber-400'
        : 'text-gray-400 hover:bg-gray-800 hover:text-gray-100'
    }`

  const Sidebar = () => (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-4 py-5 border-b border-gray-800">
        <Beer size={24} className="text-amber-500 shrink-0" />
        <span className="text-lg font-bold text-gray-100">BarPOS</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto p-3 space-y-1">
        {visibleNav.map(({ to, tKey, icon: Icon, perm }) => (
          <NavLink key={to} to={to} className={linkClass} onClick={() => setSidebarOpen(false)}>
            <Icon size={18} className="shrink-0" />
            <span className="flex-1">{t(tKey)}</span>
            {perm === 'stock' && lowStockCount > 0 && (
              <span className="bg-red-500 text-white text-xs font-bold rounded-full min-w-[18px] h-[18px] flex items-center justify-center px-1">
                {lowStockCount}
              </span>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Bottom: user info + language + logout */}
      <div className="p-3 border-t border-gray-800 space-y-1">
        <div className="px-3 py-2">
          <p className="text-sm font-medium text-gray-200 truncate">{user?.name}</p>
          <p className="text-xs text-gray-500 truncate">{user?.role_name}</p>
        </div>

        {/* Language switcher */}
        <div className="flex gap-1 px-3 py-1">
          {LANGUAGES.map(({ code, label }) => (
            <button
              key={code}
              onClick={() => setLang(code)}
              title={LANGUAGES.find((l) => l.code === code)?.name}
              className={`text-xs px-2 py-1 rounded font-medium transition-colors ${
                lang === code
                  ? 'bg-amber-500/20 text-amber-400'
                  : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        <button
          onClick={() => logoutMutation.mutate()}
          disabled={logoutMutation.isPending}
          className="btn-ghost w-full justify-start text-red-400 hover:text-red-300 hover:bg-red-900/20"
        >
          <LogOut size={16} />
          {t('logout')}
        </button>
      </div>
    </div>
  )

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Desktop sidebar */}
      <aside className="hidden md:flex md:flex-col w-60 bg-gray-900 border-r border-gray-800 shrink-0">
        <Sidebar />
      </aside>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Mobile drawer */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-60 bg-gray-900 border-r border-gray-800 flex flex-col transform transition-transform md:hidden ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <Sidebar />
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Mobile topbar */}
        <header className="md:hidden flex items-center gap-3 px-4 py-3 bg-gray-900 border-b border-gray-800 shrink-0">
          <button onClick={() => setSidebarOpen(!sidebarOpen)} className="btn-ghost p-1.5">
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          <div className="flex items-center gap-2">
            <Beer size={20} className="text-amber-500" />
            <span className="font-bold text-gray-100">BarPOS</span>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
