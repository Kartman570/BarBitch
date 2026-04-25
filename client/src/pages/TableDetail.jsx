import { useState, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft, Plus, Trash2, Edit2, Check, X, Download, Lock, Search,
} from 'lucide-react'
import api from '../api/client'
import Modal from '../components/Modal'
import Spinner from '../components/Spinner'
import { useT, useDateLocale, pluralItems } from '../i18n'
import { CURRENCY } from '../currency'

function OrderRow({ order, isActive, onDelete, onUpdateQty, t }) {
  const [editing, setEditing] = useState(false)
  const [qty, setQty] = useState(String(order.quantity))
  const discount = order.discount ?? 0
  const lineTotal = order.price * order.quantity * (1 - discount / 100)

  const handleSave = () => {
    const newQty = parseInt(qty, 10)
    if (newQty > 0 && newQty !== order.quantity) onUpdateQty(order.id, newQty)
    setEditing(false)
  }

  return (
    <tr>
      <td>{order.item_name || `${t('td_item_fallback')}${order.item_id ?? ''}`}</td>
      <td>
        {isActive && editing ? (
          <div className="flex items-center gap-1">
            <input
              className="input w-20 py-1 text-center"
              type="number"
              min="1"
              step="1"
              value={qty}
              onChange={(e) => setQty(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') handleSave(); if (e.key === 'Escape') setEditing(false) }}
              autoFocus
            />
            <button onClick={handleSave} className="btn-ghost btn-sm p-1 text-green-400"><Check size={14} /></button>
            <button onClick={() => setEditing(false)} className="btn-ghost btn-sm p-1 text-gray-500"><X size={14} /></button>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <span>{order.quantity}</span>
            {isActive && (
              <button
                onClick={() => { setQty(String(order.quantity)); setEditing(true) }}
                className="btn-ghost btn-sm p-1 opacity-0 group-hover:opacity-100"
              >
                <Edit2 size={12} />
              </button>
            )}
          </div>
        )}
      </td>
      <td>{order.price.toFixed(2)} {CURRENCY}</td>
      <td>
        {discount > 0
          ? <span className="text-xs text-green-400">−{discount}%</span>
          : <span className="text-gray-600">—</span>}
      </td>
      <td className="font-medium text-amber-400">{lineTotal.toFixed(2)} {CURRENCY}</td>
      <td>
        {isActive && (
          <button
            onClick={() => onDelete(order.id)}
            className="btn-ghost btn-sm p-1.5 text-red-400 hover:text-red-300 hover:bg-red-900/20"
          >
            <Trash2 size={14} />
          </button>
        )}
      </td>
    </tr>
  )
}

function AddOrderModal({ open, onClose, tableId, t }) {
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState(null)
  const [qty, setQty] = useState('1')
  const [discount, setDiscount] = useState('0')
  const [policyDiscount, setPolicyDiscount] = useState(null)  // ActiveDiscountRead | null
  const [confirmOverride, setConfirmOverride] = useState(false)
  const qc = useQueryClient()

  const { data: items = [] } = useQuery({
    queryKey: ['items', 'available'],
    queryFn: () => api.get('/items/', { params: { available_only: true } }).then((r) => r.data),
    enabled: open,
  })

  const filtered = useMemo(
    () => items.filter((i) => i.name.toLowerCase().includes(search.toLowerCase())),
    [items, search]
  )

  const addMutation = useMutation({
    mutationFn: ({ itemId, quantity, discount }) =>
      api.post(`/tables/${tableId}/orders/`, { item_id: itemId, quantity, discount }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['table', tableId] })
      handleClose()
    },
  })

  const handleClose = () => {
    setSearch('')
    setSelected(null)
    setQty('1')
    setDiscount('0')
    setPolicyDiscount(null)
    setConfirmOverride(false)
    onClose()
  }

  const selectItem = (item) => {
    setSelected(item)
    setPolicyDiscount(null)
    api.get(`/discounts/for-item/${item.id}`)
      .then((r) => {
        setPolicyDiscount(r.data)
        setDiscount(String(r.data.percent))
      })
      .catch(() => {
        setPolicyDiscount(null)
        setDiscount('0')
      })
  }

  const discountVal = Math.min(100, Math.max(0, parseFloat(discount || 0)))
  const subtotal = selected ? selected.price * parseInt(qty || 0, 10) * (1 - discountVal / 100) : 0
  const isOverride = policyDiscount !== null && discountVal !== policyDiscount.percent

  const doAdd = () => {
    addMutation.mutate({ itemId: selected.id, quantity: parseInt(qty, 10), discount: discountVal })
  }

  const handleAddClick = () => {
    if (isOverride) {
      setConfirmOverride(true)
    } else {
      doAdd()
    }
  }

  return (
    <Modal open={open} onClose={handleClose} title={t('td_add_title')} size="md">
      <div className="space-y-4">
        {!selected ? (
          <>
            <div className="relative">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
              <input
                className="input pl-9"
                placeholder={t('td_search_placeholder')}
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                autoFocus
              />
            </div>
            <div className="space-y-1 max-h-64 overflow-y-auto">
              {filtered.length === 0 ? (
                <p className="text-gray-500 text-sm text-center py-4">{t('nothing_found')}</p>
              ) : (
                filtered.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => selectItem(item)}
                    className="w-full flex items-center justify-between px-3 py-2.5 rounded-lg hover:bg-gray-800 text-left transition-colors"
                  >
                    <div>
                      <p className="text-sm font-medium text-gray-200">{item.name}</p>
                      {item.category && <p className="text-xs text-gray-500">{item.category}</p>}
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-amber-400">{item.price.toFixed(2)} {CURRENCY}</p>
                      {item.stock_qty !== null && (
                        <p className={`text-xs ${item.stock_qty <= 3 ? 'text-red-400' : 'text-gray-500'}`}>
                          {t('td_stock_left')}: {item.stock_qty}
                        </p>
                      )}
                    </div>
                  </button>
                ))
              )}
            </div>
          </>
        ) : (
          <>
            <div className="card p-3 flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-200">{selected.name}</p>
                <p className="text-sm text-amber-400">{selected.price.toFixed(2)} {t('td_per_unit', { currency: CURRENCY })}</p>
              </div>
              <button onClick={() => { setSelected(null); setPolicyDiscount(null) }} className="btn-ghost btn-sm p-1.5">
                <X size={16} />
              </button>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">{t('td_quantity_label')}</label>
                <input
                  className="input"
                  type="number"
                  min="1"
                  step="1"
                  value={qty}
                  onChange={(e) => setQty(e.target.value)}
                  autoFocus
                />
              </div>
              <div>
                <label className="label">{t('td_discount_label')}</label>
                <input
                  className={`input ${isOverride ? 'border-amber-500/60' : ''}`}
                  type="number"
                  min="0"
                  max="100"
                  step="1"
                  value={discount}
                  onChange={(e) => setDiscount(e.target.value)}
                  placeholder="0"
                />
              </div>
            </div>
            {isOverride && (
              <p className="text-xs text-amber-400 bg-amber-500/10 border border-amber-500/30 rounded-lg px-3 py-2">
                {t('disc_override_warning', { name: policyDiscount.policy_name, percent: policyDiscount.percent })}
              </p>
            )}
            {qty && selected && (
              <p className="text-xs text-gray-500">
                {t('td_subtotal_label')}: {subtotal.toFixed(2)} {CURRENCY}
                {discountVal > 0 && <span className="text-green-400 ml-1">(−{discountVal}%)</span>}
              </p>
            )}
            {addMutation.error && (
              <p className="text-red-400 text-sm">
                {addMutation.error.response?.data?.detail ?? t('error')}
              </p>
            )}
            <div className="flex gap-2 justify-end">
              <button onClick={handleClose} className="btn-secondary">{t('cancel')}</button>
              <button
                onClick={handleAddClick}
                className="btn-primary"
                disabled={addMutation.isPending || !qty || parseInt(qty, 10) <= 0}
              >
                {addMutation.isPending ? <Spinner className="text-gray-950" /> : null}
                {t('add')}
              </button>
            </div>
          </>
        )}
      </div>

      {/* Override confirmation modal */}
      <Modal
        open={confirmOverride}
        onClose={() => setConfirmOverride(false)}
        title={t('disc_override_confirm_title')}
        size="sm"
      >
        {policyDiscount && (
          <div className="space-y-4">
            <p className="text-gray-300 text-sm">
              {t('disc_override_confirm_body', {
                name: policyDiscount.policy_name,
                percent: policyDiscount.percent,
                custom: discountVal,
              })}
            </p>
            <div className="flex gap-2 justify-end">
              <button onClick={() => setConfirmOverride(false)} className="btn-secondary">{t('cancel')}</button>
              <button
                onClick={() => { setConfirmOverride(false); doAdd() }}
                className="btn-primary"
                disabled={addMutation.isPending}
              >
                {addMutation.isPending ? <Spinner className="text-gray-950" /> : null}
                {t('disc_override_proceed')}
              </button>
            </div>
          </div>
        )}
      </Modal>
    </Modal>
  )
}

export default function TableDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [addOpen, setAddOpen] = useState(false)
  const [confirmClose, setConfirmClose] = useState(false)
  const [renaming, setRenaming] = useState(false)
  const [newName, setNewName] = useState('')
  const t = useT()
  const dateLocale = useDateLocale()

  const { data: table, isLoading, error } = useQuery({
    queryKey: ['table', id],
    queryFn: () => api.get(`/tables/${id}`).then((r) => r.data),
    refetchInterval: 30_000,
  })

  const { data: allItems = [] } = useQuery({
    queryKey: ['items'],
    queryFn: () => api.get('/items/').then((r) => r.data),
  })

  const itemsMap = useMemo(
    () => Object.fromEntries(allItems.map((i) => [i.id, i])),
    [allItems]
  )

  const deleteOrderMutation = useMutation({
    mutationFn: (orderId) => api.delete(`/tables/${id}/orders/${orderId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['table', id] }),
  })

  const updateOrderMutation = useMutation({
    mutationFn: ({ orderId, quantity }) =>
      api.patch(`/tables/${id}/orders/${orderId}`, { quantity }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['table', id] }),
  })

  const closeTableMutation = useMutation({
    mutationFn: () => api.post(`/tables/${id}/close`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['table', id] })
      qc.invalidateQueries({ queryKey: ['tables'] })
      setConfirmClose(false)
    },
  })

  const renameMutation = useMutation({
    mutationFn: (name) => api.patch(`/tables/${id}`, { table_name: name }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['table', id] })
      qc.invalidateQueries({ queryKey: ['tables'] })
      setRenaming(false)
    },
  })

  const downloadReceipt = () => {
    api
      .get(`/tables/${id}/receipt`, { responseType: 'blob' })
      .then(({ data }) => {
        const url = URL.createObjectURL(data)
        const a = document.createElement('a')
        a.href = url
        a.download = `receipt_table_${id}.pdf`
        a.click()
        URL.revokeObjectURL(url)
      })
  }

  if (isLoading) {
    return <div className="flex justify-center py-16"><Spinner className="text-amber-500 w-8 h-8" /></div>
  }

  if (error || !table) {
    return (
      <div className="text-center py-16 text-gray-500">
        <p>{t('td_not_found')}</p>
        <button onClick={() => navigate('/tables')} className="btn-secondary mt-4">
          {t('td_back')}
        </button>
      </div>
    )
  }

  const isActive = table.status === 'Active'
  const orders = table.orders ?? []
  const total = orders.reduce((sum, o) => {
    const discount = o.discount ?? 0
    return sum + o.price * o.quantity * (1 - discount / 100)
  }, 0)

  return (
    <div className="max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => navigate('/tables')} className="btn-ghost p-2">
          <ArrowLeft size={20} />
        </button>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3">
            {renaming ? (
              <div className="flex items-center gap-2 flex-1">
                <input
                  className="input text-xl font-bold py-1 flex-1"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && newName.trim()) renameMutation.mutate(newName.trim())
                    if (e.key === 'Escape') setRenaming(false)
                  }}
                  autoFocus
                />
                <button
                  onClick={() => newName.trim() && renameMutation.mutate(newName.trim())}
                  disabled={renameMutation.isPending || !newName.trim()}
                  className="btn-ghost p-1.5 text-green-400"
                >
                  <Check size={16} />
                </button>
                <button onClick={() => setRenaming(false)} className="btn-ghost p-1.5 text-gray-500">
                  <X size={16} />
                </button>
              </div>
            ) : (
              <>
                <h1 className="text-2xl font-bold text-gray-100 truncate">{table.table_name}</h1>
                {isActive && (
                  <button
                    onClick={() => { setNewName(table.table_name); setRenaming(true) }}
                    className="btn-ghost p-1.5 text-gray-500 hover:text-gray-300 shrink-0"
                    title={t('td_rename_label')}
                  >
                    <Edit2 size={15} />
                  </button>
                )}
              </>
            )}
            {!renaming && (
              isActive
                ? <span className="badge-green shrink-0">{t('status_active')}</span>
                : <span className="badge-gray shrink-0">{t('status_closed')}</span>
            )}
          </div>
          <p className="text-sm text-gray-500 mt-0.5">
            {t('td_opened')}: {new Date(table.created_at).toLocaleString(dateLocale, { hour12: false })}
            {!isActive && table.closed_at && (
              <> · {t('td_closed_at')}: {new Date(table.closed_at).toLocaleString(dateLocale, { hour12: false })}</>
            )}
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {isActive ? (
            <>
              <button onClick={() => setAddOpen(true)} className="btn-primary btn-sm">
                <Plus size={16} />
                {t('td_add')}
              </button>
              <button
                onClick={() => setConfirmClose(true)}
                className="btn-secondary btn-sm"
                disabled={orders.length === 0}
              >
                <Lock size={14} />
                {t('td_close')}
              </button>
            </>
          ) : (
            <button onClick={downloadReceipt} className="btn-secondary btn-sm">
              <Download size={14} />
              {t('td_receipt_pdf')}
            </button>
          )}
        </div>
      </div>

      {/* Orders table */}
      <div className="card overflow-hidden">
        {orders.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-gray-500">
            <Plus size={32} className="mb-2 opacity-30" />
            <p>{t('td_no_orders')}</p>
          </div>
        ) : (
          <div className="table-wrapper border-0 rounded-none">
            <table className="data-table group">
              <thead>
                <tr>
                  <th>{t('td_col_item')}</th>
                  <th>{t('td_col_qty')}</th>
                  <th>{t('td_col_price')}</th>
                  <th>{t('td_col_discount')}</th>
                  <th>{t('td_col_total')}</th>
                  <th style={{ width: 48 }} />
                </tr>
              </thead>
              <tbody>
                {orders.map((order) => (
                  <OrderRow
                    key={order.id}
                    order={order}

                    isActive={isActive}
                    t={t}
                    onDelete={(oid) => deleteOrderMutation.mutate(oid)}
                    onUpdateQty={(oid, quantity) =>
                      updateOrderMutation.mutate({ orderId: oid, quantity })
                    }
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}

        {orders.length > 0 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-800 bg-gray-800/30">
            <span className="text-sm text-gray-400">
              {orders.length} {pluralItems(orders.length, t)}
            </span>
            <span className="text-lg font-bold text-amber-400">{total.toFixed(2)} {CURRENCY}</span>
          </div>
        )}
      </div>

      <AddOrderModal open={addOpen} onClose={() => setAddOpen(false)} tableId={id} t={t} />

      {/* Confirm close modal */}
      <Modal
        open={confirmClose}
        onClose={() => setConfirmClose(false)}
        title={t('td_close_title')}
        size="sm"
      >
        <div className="space-y-4">
          <p className="text-gray-300">
            {t('td_close_pre')}{' '}
            <span className="text-gray-100 font-medium">{table.table_name}</span>?
            {' '}{t('td_close_total_label')}:{' '}
            <span className="text-amber-400 font-bold">{total.toFixed(2)} {CURRENCY}</span>
          </p>
          <p className="text-sm text-gray-500">{t('td_close_warning')}</p>
          {closeTableMutation.error && (
            <p className="text-red-400 text-sm">
              {closeTableMutation.error.response?.data?.detail ?? t('error')}
            </p>
          )}
          <div className="flex gap-2 justify-end">
            <button onClick={() => setConfirmClose(false)} className="btn-secondary">
              {t('cancel')}
            </button>
            <button
              onClick={() => closeTableMutation.mutate()}
              className="btn-primary"
              disabled={closeTableMutation.isPending}
            >
              {closeTableMutation.isPending ? <Spinner className="text-gray-950" /> : null}
              {t('td_close_button')}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
