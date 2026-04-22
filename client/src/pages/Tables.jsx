import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Plus, RefreshCw, Clock, CheckCircle, LayoutGrid } from 'lucide-react'
import api from '../api/client'
import Modal from '../components/Modal'
import Spinner from '../components/Spinner'
import { useT, useDateLocale } from '../i18n'
import { CURRENCY } from '../currency'

function TableCard({ table, onClick, t, dateLocale }) {
  const isActive = table.status === 'Active'
  return (
    <button
      onClick={onClick}
      className="card p-4 text-left hover:border-amber-500/50 transition-all hover:shadow-lg hover:shadow-amber-500/5 group"
    >
      <div className="flex items-start justify-between mb-3">
        <h3 className="font-semibold text-gray-100 group-hover:text-amber-400 transition-colors">
          {table.table_name}
        </h3>
        {isActive
          ? <span className="badge-green">{t('status_active')}</span>
          : <span className="badge-gray">{t('status_closed')}</span>}
      </div>
      <div className="flex items-center gap-1 text-xs text-gray-500">
        <Clock size={12} />
        <span>
          {new Date(isActive ? table.created_at : table.closed_at).toLocaleTimeString(dateLocale, {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false,
          })}
        </span>
      </div>
      {!isActive && table.total > 0 && (
        <p className="mt-2 text-sm font-medium text-amber-400">
          {table.total.toFixed(2)} {CURRENCY}
        </p>
      )}
    </button>
  )
}

export default function Tables() {
  const [tab, setTab] = useState('active')
  const [modalOpen, setModalOpen] = useState(false)
  const [tableName, setTableName] = useState('')
  const navigate = useNavigate()
  const qc = useQueryClient()
  const t = useT()
  const dateLocale = useDateLocale()

  const statusParam = tab === 'active' ? 'Active' : tab === 'closed' ? 'Closed' : undefined

  const { data: tables = [], isLoading, refetch } = useQuery({
    queryKey: ['tables', tab],
    queryFn: () => api.get('/tables/', { params: statusParam ? { status: statusParam } : {} }).then((r) => r.data),
    refetchInterval: tab !== 'closed' ? 30_000 : false,
  })

  const createMutation = useMutation({
    mutationFn: (name) => api.post('/tables/', { table_name: name }),
    onSuccess: ({ data }) => {
      qc.invalidateQueries({ queryKey: ['tables'] })
      setModalOpen(false)
      setTableName('')
      navigate(`/tables/${data.id}`)
    },
  })

const handleCreate = (e) => {
    e.preventDefault()
    if (tableName.trim()) createMutation.mutate(tableName.trim())
  }

  const TABS = [
    { key: 'all', tKey: 'tables_tab_all', icon: LayoutGrid },
    { key: 'active', tKey: 'tables_tab_active', icon: Clock },
    { key: 'closed', tKey: 'tables_tab_closed', icon: CheckCircle },
  ]

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-100">{t('tables_title')}</h1>
        <div className="flex items-center gap-2">
          <button onClick={() => refetch()} className="btn-secondary btn-sm">
            <RefreshCw size={14} />
          </button>
          <button onClick={() => setModalOpen(true)} className="btn-primary btn-sm">
            <Plus size={16} />
            {t('tables_new')}
          </button>
        </div>
      </div>

      <div className="flex gap-1 p-1 bg-gray-900 rounded-lg border border-gray-800 w-fit mb-6">
        {TABS.map(({ key, tKey, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              tab === key ? 'bg-amber-500 text-gray-950' : 'text-gray-400 hover:text-gray-100'
            }`}
          >
            <Icon size={14} />
            {t(tKey)}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16">
          <Spinner className="text-amber-500 w-8 h-8" />
        </div>
      ) : tables.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-gray-500">
          <Clock size={40} className="mb-3 opacity-30" />
          <p>{tab === 'active' ? t('tables_empty_active') : tab === 'closed' ? t('tables_empty_closed') : t('tables_empty_all')}</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
          {tables.map((table) => (
            <TableCard
              key={table.id}
              table={table}
              t={t}
              dateLocale={dateLocale}
              onClick={() => navigate(`/tables/${table.id}`)}
            />
          ))}
        </div>
      )}

      <Modal
        open={modalOpen}
        onClose={() => { setModalOpen(false); setTableName('') }}
        title={t('tables_new')}
        size="sm"
      >
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="label">{t('tables_name_label')}</label>
            <input
              className="input"
              placeholder={t('tables_name_placeholder')}
              value={tableName}
              onChange={(e) => setTableName(e.target.value)}
              autoFocus
              required
            />
          </div>
          {createMutation.error && (
            <p className="text-red-400 text-sm">
              {createMutation.error.response?.data?.detail ?? t('error')}
            </p>
          )}
          <div className="flex gap-2 justify-end">
            <button
              type="button"
              onClick={() => { setModalOpen(false); setTableName('') }}
              className="btn-secondary"
            >
              {t('cancel')}
            </button>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? <Spinner className="text-gray-950" /> : null}
              {t('tables_create')}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
