import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Edit2, Trash2, Pause, Play, Tag } from 'lucide-react'
import api from '../api/client'
import Modal from '../components/Modal'
import Spinner from '../components/Spinner'
import { useT, useDateLocale } from '../i18n'

// Server returns timezone-naive UTC strings (no Z suffix). Force UTC parsing.
const asUtc = (iso) =>
  typeof iso === 'string' && !iso.endsWith('Z') && !iso.includes('+') ? iso + 'Z' : iso

const toLocalDT = (date) => {
  const d = new Date(asUtc(date))
  return new Date(d - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16)
}

const emptyForm = () => ({
  name: '',
  percent: '10',
  allItems: true,
  selectedItemIds: [],
  validFrom: toLocalDT(new Date()),
  validUntil: '',
})

function policyStatus(policy) {
  if (!policy.is_active) return 'paused'
  const now = new Date()
  if (policy.valid_until && new Date(asUtc(policy.valid_until)) < now) return 'expired'
  if (new Date(asUtc(policy.valid_from)) > now) return 'pending'
  return 'active'
}

function StatusBadge({ policy, t }) {
  const s = policyStatus(policy)
  const cls = {
    active:  'badge-green',
    paused:  'badge-amber',
    expired: 'badge-gray',
    pending: 'badge-gray',
  }[s]
  const label = {
    active:  t('disc_status_active'),
    paused:  t('disc_status_paused'),
    expired: t('disc_status_expired'),
    pending: t('disc_status_pending'),
  }[s]
  return <span className={cls}>{label}</span>
}

function DiscountForm({ initial = null, items, onSubmit, isPending, error, onCancel, t }) {
  const [form, setForm] = useState(() => initial ?? emptyForm())
  const set = (k) => (v) => setForm((f) => ({ ...f, [k]: v }))
  const setE = (k) => (e) => set(k)(e.target.value)

  const toggleItem = (id) => {
    setForm((f) => ({
      ...f,
      selectedItemIds: f.selectedItemIds.includes(id)
        ? f.selectedItemIds.filter((x) => x !== id)
        : [...f.selectedItemIds, id],
    }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit({
      name: form.name.trim(),
      percent: parseFloat(form.percent),
      item_ids: form.allItems ? [] : form.selectedItemIds,
      valid_from: form.validFrom ? new Date(form.validFrom).toISOString() : undefined,
      valid_until: form.validUntil ? new Date(form.validUntil).toISOString() : null,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="label">{t('disc_form_name')}</label>
        <input className="input" value={form.name} onChange={setE('name')} required autoFocus />
      </div>

      <div>
        <label className="label">{t('disc_form_percent')}</label>
        <input
          className="input"
          type="number"
          min="0"
          max="100"
          step="0.1"
          value={form.percent}
          onChange={setE('percent')}
          required
        />
      </div>

      <div>
        <label className="label">{t('disc_form_items')}</label>
        <div className="flex gap-4 mb-2">
          <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
            <input
              type="radio"
              className="accent-amber-500"
              checked={form.allItems}
              onChange={() => set('allItems')(true)}
            />
            {t('disc_form_items_all')}
          </label>
          <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
            <input
              type="radio"
              className="accent-amber-500"
              checked={!form.allItems}
              onChange={() => set('allItems')(false)}
            />
            {t('disc_form_items_select')}
          </label>
        </div>
        {!form.allItems && (
          <div className="max-h-40 overflow-y-auto border border-gray-700 rounded-lg p-2 space-y-1">
            {items.map((item) => (
              <label key={item.id} className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer hover:text-gray-100 px-1 py-0.5 rounded hover:bg-gray-800">
                <input
                  type="checkbox"
                  className="accent-amber-500"
                  checked={form.selectedItemIds.includes(item.id)}
                  onChange={() => toggleItem(item.id)}
                />
                <span className="flex-1">{item.name}</span>
                <span className="text-xs text-gray-500">{item.category ?? ''}</span>
              </label>
            ))}
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="label">{t('disc_form_valid_from')}</label>
          <input
            className="input"
            type="datetime-local"
            value={form.validFrom}
            onChange={setE('validFrom')}
          />
        </div>
        <div>
          <label className="label">{t('disc_form_valid_until')}</label>
          <input
            className="input"
            type="datetime-local"
            value={form.validUntil}
            onChange={setE('validUntil')}
          />
        </div>
      </div>

      {error && (
        <p className="text-red-400 text-sm">
          {error.response?.data?.detail ?? t('error')}
        </p>
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

function fmtDt(iso, dateLocale) {
  if (!iso) return '—'
  return new Date(asUtc(iso)).toLocaleString(dateLocale, {
    day: '2-digit', month: '2-digit', year: '2-digit',
    hour: '2-digit', minute: '2-digit',
    hour12: false,
  })
}

export default function Discounts() {
  const qc = useQueryClient()
  const t = useT()
  const dateLocale = useDateLocale()
  const [modal, setModal] = useState(null)   // null | 'add' | policy object
  const [deleteTarget, setDeleteTarget] = useState(null)

  const { data: policies = [], isLoading } = useQuery({
    queryKey: ['discounts'],
    queryFn: () => api.get('/discounts/').then((r) => r.data),
  })

  const { data: items = [] } = useQuery({
    queryKey: ['items'],
    queryFn: () => api.get('/items/').then((r) => r.data),
  })

  const itemsMap = useMemo(() => Object.fromEntries(items.map((i) => [i.id, i])), [items])

  const createMutation = useMutation({
    mutationFn: (data) => api.post('/discounts/', data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['discounts'] }); setModal(null) },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => api.patch(`/discounts/${id}`, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['discounts'] }); setModal(null) },
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => api.delete(`/discounts/${id}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['discounts'] }); setDeleteTarget(null) },
  })

  const toggleActive = (policy) =>
    updateMutation.mutate({ id: policy.id, data: { is_active: !policy.is_active } })

  const editInitial = (policy) => ({
    name: policy.name,
    percent: String(policy.percent),
    allItems: policy.item_ids.length === 0,
    selectedItemIds: policy.item_ids,
    validFrom: policy.valid_from ? toLocalDT(policy.valid_from) : '',
    validUntil: policy.valid_until ? toLocalDT(policy.valid_until) : '',
  })

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-100">{t('disc_title')}</h1>
        <button onClick={() => setModal('add')} className="btn-primary btn-sm">
          <Plus size={16} />
          {t('disc_new')}
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16"><Spinner className="text-amber-500 w-8 h-8" /></div>
      ) : policies.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-gray-500">
          <Tag size={40} className="mb-3 opacity-30" />
          <p>{t('disc_empty')}</p>
        </div>
      ) : (
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('disc_col_name')}</th>
                <th>{t('disc_col_percent')}</th>
                <th>{t('disc_col_items')}</th>
                <th>{t('disc_col_valid_from')}</th>
                <th>{t('disc_col_valid_until')}</th>
                <th>{t('disc_col_status')}</th>
                <th style={{ width: 100 }} />
              </tr>
            </thead>
            <tbody>
              {policies.map((policy) => (
                <tr key={policy.id}>
                  <td className="font-medium">{policy.name}</td>
                  <td className="text-amber-400 font-semibold">{policy.percent}%</td>
                  <td className="text-gray-400">
                    {policy.item_ids.length === 0
                      ? <span className="badge-gray">{t('disc_items_all')}</span>
                      : <span className="badge-gray">{t('disc_items_count', { n: policy.item_ids.length })}</span>
                    }
                  </td>
                  <td className="text-gray-400 text-xs whitespace-nowrap">{fmtDt(policy.valid_from, dateLocale)}</td>
                  <td className="text-gray-400 text-xs whitespace-nowrap">
                    {policy.valid_until ? fmtDt(policy.valid_until, dateLocale) : <span className="text-gray-600">{t('disc_unlimited')}</span>}
                  </td>
                  <td><StatusBadge policy={policy} t={t} /></td>
                  <td>
                    <div className="flex gap-1">
                      <button
                        onClick={() => toggleActive(policy)}
                        className="btn-ghost btn-sm p-1.5 text-gray-400 hover:text-gray-200"
                        title={policy.is_active ? t('disc_pause') : t('disc_resume')}
                        disabled={updateMutation.isPending}
                      >
                        {policy.is_active ? <Pause size={14} /> : <Play size={14} />}
                      </button>
                      <button
                        onClick={() => setModal(policy)}
                        className="btn-ghost btn-sm p-1.5"
                      >
                        <Edit2 size={14} />
                      </button>
                      <button
                        onClick={() => setDeleteTarget(policy)}
                        className="btn-ghost btn-sm p-1.5 text-red-400 hover:text-red-300 hover:bg-red-900/20"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal open={modal === 'add'} onClose={() => setModal(null)} title={t('disc_add_title')} size="md">
        <DiscountForm
          t={t}
          items={items}
          onSubmit={(data) => createMutation.mutate(data)}
          isPending={createMutation.isPending}
          error={createMutation.error}
          onCancel={() => setModal(null)}
        />
      </Modal>

      <Modal open={!!modal && modal !== 'add'} onClose={() => setModal(null)} title={t('disc_edit_title')} size="md">
        {modal && modal !== 'add' && (
          <DiscountForm
            t={t}
            items={items}
            initial={editInitial(modal)}
            onSubmit={(data) => updateMutation.mutate({ id: modal.id, data })}
            isPending={updateMutation.isPending}
            error={updateMutation.error}
            onCancel={() => setModal(null)}
          />
        )}
      </Modal>

      <Modal open={!!deleteTarget} onClose={() => setDeleteTarget(null)} title={t('disc_delete_title')} size="sm">
        {deleteTarget && (
          <div className="space-y-4">
            <p className="text-gray-300">{t('delete_q', { name: deleteTarget.name })}</p>
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
