import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Search, Plus, Minus, Package } from 'lucide-react'
import api from '../api/client'
import Spinner from '../components/Spinner'
import { useT } from '../i18n'

function AdjustCell({ item, t }) {
  const qc = useQueryClient()
  const [delta, setDelta] = useState('')
  const [error, setError] = useState('')

  const adjustMutation = useMutation({
    mutationFn: (d) => api.patch(`/items/${item.id}/stock`, { delta: d }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['items'] })
      setDelta('')
      setError('')
    },
    onError: (e) => setError(e.response?.data?.detail ?? t('error')),
  })

  const apply = (sign) => {
    const val = parseInt(delta, 10)
    if (!delta || isNaN(val) || val <= 0) {
      setError(t('stock_invalid'))
      return
    }
    setError('')
    adjustMutation.mutate(sign * val)
  }

  return (
    <div className="flex items-center gap-2">
      <input
        className="input w-24 py-1 text-center"
        type="number"
        min="1"
        step="1"
        placeholder="0"
        value={delta}
        onChange={(e) => { setDelta(e.target.value); setError('') }}
        onKeyDown={(e) => { if (e.key === 'Enter') apply(1) }}
      />
      <button
        onClick={() => apply(1)}
        disabled={adjustMutation.isPending}
        className="btn-secondary btn-sm p-2 text-green-400 hover:bg-green-900/20"
        title={t('stock_btn_add')}
      >
        <Plus size={14} />
      </button>
      <button
        onClick={() => apply(-1)}
        disabled={adjustMutation.isPending}
        className="btn-secondary btn-sm p-2 text-red-400 hover:bg-red-900/20"
        title={t('stock_btn_deduct')}
      >
        <Minus size={14} />
      </button>
      {error && <span className="text-red-400 text-xs">{error}</span>}
    </div>
  )
}

export default function Stock() {
  const t = useT()
  const [search, setSearch] = useState('')
  const [showAll, setShowAll] = useState(false)

  const { data: items = [], isLoading } = useQuery({
    queryKey: ['items'],
    queryFn: () => api.get('/items/').then((r) => r.data),
  })

  const filtered = useMemo(() => {
    let list = showAll ? items : items.filter((i) => i.stock_qty !== null)
    if (search) list = list.filter((i) => i.name.toLowerCase().includes(search.toLowerCase()))
    return list
  }, [items, search, showAll])

  const stockedCount = items.filter((i) => i.stock_qty !== null).length
  const lowStock = items.filter((i) => i.stock_qty !== null && i.stock_qty <= 3).length

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-100">{t('stock_title')}</h1>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-6">
        <div className="card p-4">
          <p className="text-xs text-gray-500 mb-1">{t('stock_tracked_label')}</p>
          <p className="text-2xl font-bold text-gray-100">{stockedCount}</p>
        </div>
        <div className="card p-4">
          <p className="text-xs text-gray-500 mb-1">{t('stock_low_label')}</p>
          <p className={`text-2xl font-bold ${lowStock > 0 ? 'text-red-400' : 'text-gray-100'}`}>
            {lowStock}
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-4">
        <div className="relative flex-1 min-w-48">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            className="input pl-9"
            placeholder={t('search')}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer select-none">
          <input
            type="checkbox"
            className="accent-amber-500"
            checked={showAll}
            onChange={(e) => setShowAll(e.target.checked)}
          />
          {t('stock_show_all')}
        </label>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16"><Spinner className="text-amber-500 w-8 h-8" /></div>
      ) : (
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('stock_col_item')}</th>
                <th>{t('stock_col_category')}</th>
                <th>{t('stock_col_current')}</th>
                <th>{t('stock_col_adjust')}</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={4} className="text-center py-10">
                    <div className="flex flex-col items-center gap-2 text-gray-500">
                      <Package size={32} className="opacity-30" />
                      <span>{t('stock_empty')}</span>
                      <span className="text-xs">{t('stock_enable_hint')}</span>
                    </div>
                  </td>
                </tr>
              ) : (
                filtered.map((item) => (
                  <tr key={item.id}>
                    <td className="font-medium">{item.name}</td>
                    <td>{item.category ?? <span className="text-gray-600">—</span>}</td>
                    <td>
                      {item.stock_qty !== null ? (
                        <span
                          className={`font-semibold ${
                            item.stock_qty <= 0
                              ? 'text-red-400'
                              : item.stock_qty <= 3
                              ? 'text-amber-400'
                              : 'text-green-400'
                          }`}
                        >
                          {item.stock_qty}
                        </span>
                      ) : (
                        <span className="text-gray-600 text-sm">{t('stock_not_tracked')}</span>
                      )}
                    </td>
                    <td>
                      {item.stock_qty !== null ? (
                        <AdjustCell item={item} t={t} />
                      ) : (
                        <span className="text-gray-600 text-sm">—</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
