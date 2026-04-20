import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Search, Edit2, Trash2, CheckCircle, XCircle } from 'lucide-react'
import api from '../api/client'
import Modal from '../components/Modal'
import Spinner from '../components/Spinner'
import { useT } from '../i18n'
import { CURRENCY } from '../currency'

const EMPTY_FORM = { name: '', price: '', category: '', is_available: true, stock_qty: '' }

function ItemForm({ initial = EMPTY_FORM, isEdit = false, onSubmit, isPending, error, onCancel, t }) {
  const [form, setForm] = useState(initial)
  const set = (k) => (e) =>
    setForm((f) => ({ ...f, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value }))

  const handleSubmit = (e) => {
    e.preventDefault()
    const payload = {
      name: form.name.trim(),
      price: parseFloat(form.price),
      category: form.category.trim() || null,
      is_available: form.is_available,
      ...(!isEdit && { stock_qty: form.stock_qty !== '' ? parseInt(form.stock_qty, 10) : null }),
    }
    onSubmit(payload)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="col-span-2">
          <label className="label">{t('menu_form_name')}</label>
          <input className="input" value={form.name} onChange={set('name')} required autoFocus />
        </div>
        <div>
          <label className="label">{t('menu_form_price', { currency: CURRENCY })}</label>
          <input className="input" type="number" min="0.01" step="0.01" value={form.price} onChange={set('price')} required />
        </div>
        <div>
          <label className="label">{t('menu_form_category')}</label>
          <input className="input" placeholder={t('menu_form_category_placeholder')} value={form.category} onChange={set('category')} />
        </div>
        {!isEdit && (
          <div>
            <label className="label">{t('menu_form_stock')}</label>
            <input className="input" type="number" min="0" step="1" placeholder={t('menu_form_stock_placeholder')} value={form.stock_qty} onChange={set('stock_qty')} />
          </div>
        )}
        <div className="flex items-center gap-3 pt-6">
          <input
            id="is_available"
            type="checkbox"
            className="w-4 h-4 accent-amber-500"
            checked={form.is_available}
            onChange={set('is_available')}
          />
          <label htmlFor="is_available" className="text-sm text-gray-300 cursor-pointer">
            {t('menu_form_available')}
          </label>
        </div>
      </div>
      {error && (
        <p className="text-red-400 text-sm">{error.response?.data?.detail ?? t('error')}</p>
      )}
      <div className="flex gap-2 justify-end">
        <button type="button" onClick={onCancel} className="btn-secondary">{t('cancel')}</button>
        <button type="submit" className="btn-primary" disabled={isPending}>
          {isPending ? <Spinner className="text-gray-950" /> : null}
          {t('save')}
        </button>
      </div>
    </form>
  )
}

export default function Menu() {
  const qc = useQueryClient()
  const t = useT()
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [modal, setModal] = useState(null) // null | 'add' | { item }
  const [deleteTarget, setDeleteTarget] = useState(null)

  const { data: items = [], isLoading } = useQuery({
    queryKey: ['items'],
    queryFn: () => api.get('/items/').then((r) => r.data),
  })

  const categories = useMemo(
    () => [...new Set(items.map((i) => i.category).filter(Boolean))].sort(),
    [items]
  )

  const filtered = useMemo(
    () =>
      items.filter((i) => {
        const matchSearch = i.name.toLowerCase().includes(search.toLowerCase())
        const matchCat = !categoryFilter || i.category === categoryFilter
        return matchSearch && matchCat
      }),
    [items, search, categoryFilter]
  )

  const createMutation = useMutation({
    mutationFn: (data) => api.post('/items/', data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['items'] }); setModal(null) },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => api.put(`/items/${id}`, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['items'] }); setModal(null) },
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => api.delete(`/items/${id}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['items'] }); setDeleteTarget(null) },
  })

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-100">{t('menu_title')}</h1>
        <button onClick={() => setModal('add')} className="btn-primary btn-sm">
          <Plus size={16} />
          {t('menu_add')}
        </button>
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
        <select
          className="input w-auto"
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
        >
          <option value="">{t('menu_all_categories')}</option>
          {categories.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16"><Spinner className="text-amber-500 w-8 h-8" /></div>
      ) : (
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('menu_col_name')}</th>
                <th>{t('menu_col_category')}</th>
                <th>{t('menu_col_price')}</th>
                <th>{t('menu_col_stock')}</th>
                <th>{t('menu_col_status')}</th>
                <th style={{ width: 80 }} />
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr><td colSpan={6} className="text-center text-gray-500 py-8">{t('nothing_found')}</td></tr>
              ) : (
                filtered.map((item) => (
                  <tr key={item.id}>
                    <td className="font-medium">{item.name}</td>
                    <td>{item.category ? <span className="badge-gray">{item.category}</span> : <span className="text-gray-600">—</span>}</td>
                    <td className="text-amber-400 font-medium">{item.price.toFixed(2)} {CURRENCY}</td>
                    <td>
                      {item.stock_qty !== null
                        ? <span className={item.stock_qty <= 3 ? 'text-red-400' : 'text-gray-300'}>{item.stock_qty}</span>
                        : <span className="text-gray-600">—</span>}
                    </td>
                    <td>
                      {item.is_available
                        ? <span className="flex items-center gap-1 text-green-400 text-xs"><CheckCircle size={14} />{t('menu_avail_yes')}</span>
                        : <span className="flex items-center gap-1 text-gray-500 text-xs"><XCircle size={14} />{t('menu_avail_no')}</span>}
                    </td>
                    <td>
                      <div className="flex gap-1">
                        <button onClick={() => setModal(item)} className="btn-ghost btn-sm p-1.5">
                          <Edit2 size={14} />
                        </button>
                        <button onClick={() => setDeleteTarget(item)} className="btn-ghost btn-sm p-1.5 text-red-400 hover:text-red-300 hover:bg-red-900/20">
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Add modal */}
      <Modal open={modal === 'add'} onClose={() => setModal(null)} title={t('menu_add_title')}>
        <ItemForm
          t={t}
          onSubmit={(data) => createMutation.mutate(data)}
          isPending={createMutation.isPending}
          error={createMutation.error}
          onCancel={() => setModal(null)}
        />
      </Modal>

      {/* Edit modal */}
      <Modal open={!!modal && modal !== 'add'} onClose={() => setModal(null)} title={t('menu_edit_title')}>
        {modal && modal !== 'add' && (
          <ItemForm
            t={t}
            isEdit
            initial={{
              name: modal.name,
              price: String(modal.price),
              category: modal.category ?? '',
              is_available: modal.is_available,
            }}
            onSubmit={(data) => updateMutation.mutate({ id: modal.id, data })}
            isPending={updateMutation.isPending}
            error={updateMutation.error}
            onCancel={() => setModal(null)}
          />
        )}
      </Modal>

      {/* Delete confirm */}
      <Modal open={!!deleteTarget} onClose={() => setDeleteTarget(null)} title={t('menu_delete_title')} size="sm">
        {deleteTarget && (
          <div className="space-y-4">
            <p className="text-gray-300">
              {t('delete_q', { name: deleteTarget.name })}
            </p>
            {deleteMutation.error && (
              <p className="text-red-400 text-sm">{deleteMutation.error.response?.data?.detail ?? t('error')}</p>
            )}
            <div className="flex gap-2 justify-end">
              <button onClick={() => setDeleteTarget(null)} className="btn-secondary">{t('cancel')}</button>
              <button
                onClick={() => deleteMutation.mutate(deleteTarget.id)}
                className="btn-danger"
                disabled={deleteMutation.isPending}
              >
                {deleteMutation.isPending ? <Spinner /> : null}
                {t('delete')}
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
