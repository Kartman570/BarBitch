import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Edit2, Trash2, Search } from 'lucide-react'
import api from '../api/client'
import Modal from '../components/Modal'
import Spinner from '../components/Spinner'
import { useAuthStore } from '../store/authStore'
import { useT } from '../i18n'

const EMPTY_FORM = { name: '', username: '', password: '', role_id: '' }

function UserForm({ initial = EMPTY_FORM, roles, onSubmit, isPending, error, onCancel, isEdit, t }) {
  const [form, setForm] = useState(initial)
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  const handleSubmit = (e) => {
    e.preventDefault()
    const payload = {
      name: form.name.trim(),
      username: form.username.trim(),
      role_id: parseInt(form.role_id),
      ...(form.password ? { password: form.password } : {}),
    }
    if (!isEdit) payload.password = form.password
    onSubmit(payload)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="label">{t('users_form_name')}</label>
        <input className="input" value={form.name} onChange={set('name')} required autoFocus />
      </div>
      <div>
        <label className="label">{t('users_form_username')}</label>
        <input className="input" value={form.username} onChange={set('username')} required autoComplete="off" />
      </div>
      <div>
        <label className="label">{isEdit ? t('users_form_password_edit') : t('users_form_password')}</label>
        <input
          className="input"
          type="password"
          value={form.password}
          onChange={set('password')}
          required={!isEdit}
          autoComplete="new-password"
          placeholder={isEdit ? t('users_form_password_no_change') : ''}
        />
        {!isEdit && (
          <p className="text-xs text-gray-500 mt-1">{t('users_form_password_hint')}</p>
        )}
      </div>
      <div>
        <label className="label">{t('users_form_role')}</label>
        <select className="input" value={form.role_id} onChange={set('role_id')} required>
          <option value="">{t('users_form_role_placeholder')}</option>
          {roles.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}
        </select>
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

export default function Users() {
  const qc = useQueryClient()
  const t = useT()
  const currentUser = useAuthStore((s) => s.user)
  const [search, setSearch] = useState('')
  const [modal, setModal] = useState(null)
  const [deleteTarget, setDeleteTarget] = useState(null)

  const { data: users = [], isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: () => api.get('/users/').then((r) => r.data),
  })

  const { data: roles = [] } = useQuery({
    queryKey: ['roles'],
    queryFn: () => api.get('/roles/').then((r) => r.data),
  })

  const filtered = search
    ? users.filter((u) => u.name.toLowerCase().includes(search.toLowerCase()) || u.username?.toLowerCase().includes(search.toLowerCase()))
    : users

  const createMutation = useMutation({
    mutationFn: (data) => api.post('/users/', data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['users'] }); setModal(null) },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => api.put(`/users/${id}`, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['users'] }); setModal(null) },
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => api.delete(`/users/${id}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['users'] }); setDeleteTarget(null) },
  })

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-100">{t('users_title')}</h1>
        <button onClick={() => setModal('add')} className="btn-primary btn-sm">
          <Plus size={16} />
          {t('users_add')}
        </button>
      </div>

      <div className="relative mb-4 max-w-sm">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
        <input
          className="input pl-9"
          placeholder={t('users_search_placeholder')}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16"><Spinner className="text-amber-500 w-8 h-8" /></div>
      ) : (
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('users_col_name')}</th>
                <th>{t('users_col_username')}</th>
                <th>{t('users_col_role')}</th>
                <th style={{ width: 80 }} />
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr><td colSpan={4} className="text-center text-gray-500 py-8">{t('nothing_found')}</td></tr>
              ) : (
                filtered.map((user) => (
                  <tr key={user.id}>
                    <td className="font-medium">
                      {user.name}
                      {user.id === currentUser?.id && (
                        <span className="ml-2 badge-amber">{t('users_you')}</span>
                      )}
                    </td>
                    <td className="text-gray-400">{user.username}</td>
                    <td><span className="badge-gray">{user.role_name}</span></td>
                    <td>
                      <div className="flex gap-1">
                        <button onClick={() => setModal(user)} className="btn-ghost btn-sm p-1.5">
                          <Edit2 size={14} />
                        </button>
                        <button
                          onClick={() => setDeleteTarget(user)}
                          disabled={user.id === currentUser?.id}
                          className="btn-ghost btn-sm p-1.5 text-red-400 hover:text-red-300 hover:bg-red-900/20 disabled:opacity-30"
                        >
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

      <Modal open={modal === 'add'} onClose={() => setModal(null)} title={t('users_add_title')}>
        <UserForm
          t={t}
          roles={roles}
          onSubmit={(data) => createMutation.mutate(data)}
          isPending={createMutation.isPending}
          error={createMutation.error}
          onCancel={() => setModal(null)}
        />
      </Modal>

      <Modal open={!!modal && modal !== 'add'} onClose={() => setModal(null)} title={t('users_edit_title')}>
        {modal && modal !== 'add' && (
          <UserForm
            t={t}
            initial={{ name: modal.name, username: modal.username ?? '', password: '', role_id: String(modal.role_id) }}
            roles={roles}
            isEdit
            onSubmit={(data) => updateMutation.mutate({ id: modal.id, data })}
            isPending={updateMutation.isPending}
            error={updateMutation.error}
            onCancel={() => setModal(null)}
          />
        )}
      </Modal>

      <Modal open={!!deleteTarget} onClose={() => setDeleteTarget(null)} title={t('users_delete_title')} size="sm">
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
              <button onClick={() => deleteMutation.mutate(deleteTarget.id)} className="btn-danger" disabled={deleteMutation.isPending}>
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
