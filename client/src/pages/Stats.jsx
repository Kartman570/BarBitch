import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'
import { TrendingUp, Lock, Activity, ShoppingCart, Users, Trophy } from 'lucide-react'
import api from '../api/client'
import Spinner from '../components/Spinner'
import { useT, useDateLocale } from '../i18n'
import { CURRENCY } from '../currency'

function today() {
  return new Date().toISOString().slice(0, 10)
}

function daysAgo(n) {
  const d = new Date()
  d.setDate(d.getDate() - n)
  return d.toISOString().slice(0, 10)
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

  // ── Daily / range stats ────────────────────────────────────────────────────
  const [dateFrom, setDateFrom] = useState(today())
  const [dateTo, setDateTo] = useState(today())

  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['stats', dateFrom, dateTo],
    queryFn: () =>
      api.get('/stats/daily', { params: { date_from: dateFrom, date_to: dateTo } }).then((r) => r.data),
  })

  // ── Top items ──────────────────────────────────────────────────────────────
  const [topFrom, setTopFrom] = useState(daysAgo(30))
  const [topTo, setTopTo] = useState(today())

  const { data: topItems = [], isLoading: topLoading } = useQuery({
    queryKey: ['stats', 'top-items', topFrom, topTo],
    queryFn: () =>
      api.get('/stats/top-items', { params: { date_from: topFrom, date_to: topTo, limit: 10 } }).then((r) => r.data),
  })

  return (
    <div className="space-y-8">
      {/* ── Daily / range section ── */}
      <div>
        <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
          <h1 className="text-2xl font-bold text-gray-100">{t('stats_title')}</h1>
          <div className="flex items-center gap-2">
            <label className="text-xs text-gray-500">{t('stats_date_from')}</label>
            <input
              type="date"
              className="input w-auto"
              value={dateFrom}
              max={today()}
              onChange={(e) => setDateFrom(e.target.value)}
            />
            <label className="text-xs text-gray-500">{t('stats_date_to')}</label>
            <input
              type="date"
              className="input w-auto"
              value={dateTo}
              max={today()}
              min={dateFrom}
              onChange={(e) => setDateTo(e.target.value)}
            />
          </div>
        </div>

        {isLoading ? (
          <div className="flex justify-center py-16"><Spinner className="text-amber-500 w-8 h-8" /></div>
        ) : error ? (
          <p className="text-red-400">{error.response?.data?.detail ?? t('load_error')}</p>
        ) : !stats ? null : (
          <div className="space-y-6">
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
                          <td>
                            {entry.quantity}
                            {entry.discount > 0 && (
                              <span className="text-xs text-green-400 ml-1">−{entry.discount}%</span>
                            )}
                          </td>
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
                <p>{t('stats_empty', { date: stats.date })}</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── Top items section ── */}
      <div>
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <h2 className="text-xl font-bold text-gray-100 flex items-center gap-2">
            <Trophy size={20} className="text-amber-400" />
            {t('stats_top_title')}
          </h2>
          <div className="flex items-center gap-2">
            <label className="text-xs text-gray-500">{t('stats_date_from')}</label>
            <input
              type="date"
              className="input w-auto"
              value={topFrom}
              max={today()}
              onChange={(e) => setTopFrom(e.target.value)}
            />
            <label className="text-xs text-gray-500">{t('stats_date_to')}</label>
            <input
              type="date"
              className="input w-auto"
              value={topTo}
              max={today()}
              min={topFrom}
              onChange={(e) => setTopTo(e.target.value)}
            />
          </div>
        </div>

        {topLoading ? (
          <div className="flex justify-center py-8"><Spinner className="text-amber-500 w-6 h-6" /></div>
        ) : topItems.length === 0 ? (
          <div className="card flex flex-col items-center justify-center py-10 text-gray-500">
            <Trophy size={32} className="mb-2 opacity-20" />
            <p className="text-sm">{t('stats_top_empty')}</p>
          </div>
        ) : (
          <div className="card overflow-hidden">
            <div className="table-wrapper border-0 rounded-none">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>{t('td_col_item')}</th>
                    <th>{t('stats_top_col_qty')}</th>
                    <th>{t('stats_top_col_orders')}</th>
                    <th>{t('stats_top_col_revenue')}</th>
                  </tr>
                </thead>
                <tbody>
                  {topItems.map((item, idx) => (
                    <tr key={item.item_name}>
                      <td className="text-gray-600 font-medium">{idx + 1}</td>
                      <td className="font-medium text-gray-200">{item.item_name}</td>
                      <td>{item.quantity}</td>
                      <td>{item.orders_count}</td>
                      <td className="text-amber-400 font-medium">{item.revenue.toFixed(2)} {CURRENCY}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
