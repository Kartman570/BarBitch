import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ClipboardList } from 'lucide-react'
import api from '../api/client'
import Spinner from '../components/Spinner'
import { useT, useDateLocale } from '../i18n'

const ACTION_KEYS = [
  'login_success', 'login_failure', 'logout',
  'role_created', 'role_updated', 'role_deleted',
  'user_created', 'user_updated', 'user_deleted',
  'table_created', 'table_renamed', 'table_closed', 'table_deleted',
  'item_created', 'item_updated', 'item_deleted',
  'stock_adjusted',
  'order_added', 'order_updated', 'order_deleted',
]

const ACTION_COLORS = {
  login_success:  'badge-green',
  login_failure:  'badge-red',
  logout:         'badge-gray',
  role_created:   'badge-amber',
  role_updated:   'badge-amber',
  role_deleted:   'badge-red',
  user_created:   'badge-amber',
  user_updated:   'badge-amber',
  user_deleted:   'badge-red',
  table_created:  'badge-green',
  table_renamed:  'badge-amber',
  table_closed:   'badge-gray',
  table_deleted:  'badge-red',
  item_created:   'badge-amber',
  item_updated:   'badge-amber',
  item_deleted:   'badge-red',
  stock_adjusted: 'badge-amber',
  order_added:    'badge-green',
  order_updated:  'badge-amber',
  order_deleted:  'badge-red',
}

function ActionBadge({ action, t }) {
  const color = ACTION_COLORS[action]
  const label = t(`action_${action}`)
  return <span className={color ?? 'badge-gray'}>{label}</span>
}

export default function Audit() {
  const t = useT()
  const dateLocale = useDateLocale()
  const [actionFilter, setActionFilter] = useState('')
  const [limit, setLimit] = useState(100)

  const { data: events = [], isLoading } = useQuery({
    queryKey: ['audit', actionFilter, limit],
    queryFn: () =>
      api
        .get('/audit/events', { params: { action: actionFilter || undefined, limit } })
        .then((r) => r.data),
  })

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-100">{t('audit_title')}</h1>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-4">
        <select
          className="input w-auto"
          value={actionFilter}
          onChange={(e) => setActionFilter(e.target.value)}
        >
          <option value="">{t('audit_all_events')}</option>
          {ACTION_KEYS.map((key) => (
            <option key={key} value={key}>{t(`action_${key}`)}</option>
          ))}
        </select>
        <select
          className="input w-auto"
          value={limit}
          onChange={(e) => setLimit(Number(e.target.value))}
        >
          {[50, 100, 250, 500].map((n) => (
            <option key={n} value={n}>{t('audit_n_records', { n })}</option>
          ))}
        </select>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16"><Spinner className="text-amber-500 w-8 h-8" /></div>
      ) : events.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-gray-500">
          <ClipboardList size={40} className="mb-3 opacity-30" />
          <p>{t('audit_empty')}</p>
        </div>
      ) : (
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('audit_col_time')}</th>
                <th>{t('audit_col_user')}</th>
                <th>{t('audit_col_action')}</th>
                <th>{t('audit_col_resource')}</th>
                <th>{t('audit_col_ip')}</th>
              </tr>
            </thead>
            <tbody>
              {events.map((e) => (
                <tr key={e.id}>
                  <td className="text-gray-500 text-xs whitespace-nowrap">
                    {new Date(e.created_at).toLocaleString(dateLocale, {
                      day: '2-digit', month: '2-digit',
                      hour: '2-digit', minute: '2-digit', second: '2-digit',
                      hour12: false,
                    })}
                  </td>
                  <td>{e.username ?? <span className="text-gray-600">—</span>}</td>
                  <td><ActionBadge action={e.action} t={t} /></td>
                  <td className="text-gray-500">{e.resource_id ?? '—'}</td>
                  <td className="text-gray-500 text-xs">{e.ip ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
