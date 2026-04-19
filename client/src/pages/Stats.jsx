import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'
import { TrendingUp, Lock, Activity, ShoppingCart, Users } from 'lucide-react'
import api from '../api/client'
import Spinner from '../components/Spinner'
import { useT, useDateLocale } from '../i18n'
import { CURRENCY } from '../currency'

function today() {
  return new Date().toISOString().slice(0, 10)
}

function StatCard({ icon: Icon, label, value, sub, color = 'text-amber-400' }) {
  return (
    <div className="card p-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-gray-500 mb-1">{label}</p>
          <p className={`text-2xl font-bold ${color}`}>{value}</p>
          {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
        </div>
        <div className="w-9 h-9 rounded-lg bg-gray-800 flex items-center justify-center text-gray-500">
          <Icon size={18} />
        </div>
      </div>
    </div>
  )
}

const CHART_COLORS = ['#f59e0b', '#f97316', '#ef4444', '#8b5cf6', '#06b6d4', '#10b981']

export default function Stats() {
  const t = useT()
  const dateLocale = useDateLocale()
  const [date, setDate] = useState(today())

  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['stats', date],
    queryFn: () => api.get('/stats/daily', { params: { date } }).then((r) => r.data),
  })

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-100">{t('stats_title')}</h1>
        <input
          type="date"
          className="input w-auto"
          value={date}
          max={today()}
          onChange={(e) => setDate(e.target.value)}
        />
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16"><Spinner className="text-amber-500 w-8 h-8" /></div>
      ) : error ? (
        <p className="text-red-400">{error.response?.data?.detail ?? t('load_error')}</p>
      ) : !stats ? null : (
        <div className="space-y-6">
          {/* Summary cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <StatCard
              icon={TrendingUp}
              label={t('stats_revenue')}
              value={`${stats.revenue_total.toFixed(2)} ${CURRENCY}`}
            />
            <StatCard
              icon={Lock}
              label={t('stats_locked')}
              value={`${stats.revenue_locked.toFixed(2)} ${CURRENCY}`}
              color="text-green-400"
            />
            <StatCard
              icon={Activity}
              label={t('stats_running')}
              value={`${stats.revenue_running.toFixed(2)} ${CURRENCY}`}
              color="text-blue-400"
            />
            <div className="grid grid-rows-2 gap-3">
              <StatCard
                icon={ShoppingCart}
                label={t('stats_orders')}
                value={stats.orders_count}
                color="text-purple-400"
              />
              <StatCard
                icon={Users}
                label={t('stats_served')}
                value={stats.tables_served}
                color="text-gray-200"
              />
            </div>
          </div>

          {/* Items chart */}
          {stats.items_sold.length > 0 && (
            <div className="card p-5">
              <h2 className="text-sm font-semibold text-gray-300 mb-4">{t('stats_chart_title')}</h2>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={stats.items_sold} margin={{ top: 0, right: 0, bottom: 40, left: 0 }}>
                  <XAxis
                    dataKey="item_name"
                    tick={{ fill: '#9ca3af', fontSize: 11 }}
                    angle={-35}
                    textAnchor="end"
                    interval={0}
                  />
                  <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} width={55} tickFormatter={(v) => `${v} ${CURRENCY}`} />
                  <Tooltip
                    contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: 8 }}
                    labelStyle={{ color: '#f3f4f6' }}
                    formatter={(val, _name, props) => [
                      `${val.toFixed(2)} ${CURRENCY} (${props.payload.quantity} ${t('stats_pcs')})`,
                      t('stats_revenue_label'),
                    ]}
                  />
                  <Bar dataKey="revenue" radius={[4, 4, 0, 0]}>
                    {stats.items_sold.map((_, i) => (
                      <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Orders log */}
          {stats.orders_log.length > 0 && (
            <div className="card overflow-hidden">
              <div className="px-5 py-3 border-b border-gray-800">
                <h2 className="text-sm font-semibold text-gray-300">{t('stats_log_title')}</h2>
              </div>
              <div className="table-wrapper border-0 rounded-none max-h-80 overflow-y-auto">
                <table className="data-table">
                  <thead className="sticky top-0 z-10">
                    <tr>
                      <th>{t('stats_col_time')}</th>
                      <th>{t('stats_col_table')}</th>
                      <th>{t('stats_col_item')}</th>
                      <th>{t('stats_col_qty')}</th>
                      <th>{t('stats_col_total')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.orders_log.map((entry) => (
                      <tr key={entry.order_id}>
                        <td className="text-gray-500 text-xs">
                          {new Date(entry.created_at).toLocaleTimeString(dateLocale, { hour: '2-digit', minute: '2-digit' })}
                        </td>
                        <td>{entry.table_name}</td>
                        <td>{entry.item_name}</td>
                        <td>{entry.quantity}</td>
                        <td className="text-amber-400 font-medium">{entry.line_total.toFixed(2)} {CURRENCY}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {stats.orders_count === 0 && (
            <div className="flex flex-col items-center justify-center py-16 text-gray-500">
              <TrendingUp size={40} className="mb-3 opacity-30" />
              <p>{t('stats_empty', { date })}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
