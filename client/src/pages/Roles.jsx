import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Edit2, Trash2 } from 'lucide-react'
import api from '../api/client'
import Modal from '../components/Modal'
import Spinner from '../components/Spinner'
import { useT } from '../i18n'

const PERM_KEYS = ['tables', 'items', 'stock', 'stats', 'users', 'roles']

function PermsBadges({ permissions, t }) {
  if (!permissions?.length) return <span className="text-gray-600 text-sm">{t('roles_no_perms')}</span>
  return (
    <div className="flex flex-wrap gap-1">
      {permissions.map((p) => (
        <span key={p} className="badge-amber text-xs">{p}</span>
      ))}
    </div>
  )
}

function RoleForm({ initial, onSubmit, isPending, error, onCancel, t }) {
  const [name, setName] = useState(initial?.name ?? '')
  const [description, setDescription] = useState(initial?.description ?? '')
  const [perms, setPerms] = useState(new Set(initial?.permissions ?? []))

  const togglePerm = (key) => {
    setPerms((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit({ name: name.trim(), description: description.trim() || null, permissions: [...perms] })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="label">{t('roles_form_name')}</label>
        <input className="input" value={name} onChange={(e) => setName(e.target.value)} required autoFocus />
      </div>
      <div>
        <label className="label">{t('roles_form_description')}</label>
        <input className="input" value={description} onChange={(e) => setDescription(e.target.value)} />
      </div>
      <div>
        <label className="label">{t('roles_form_perms')}</label>
        <div className="grid grid-cols-2 gap-2 mt-2">
          {PERM_KEYS.map((key) => (
            <label
              key={key}
              className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                perms.has(key)
                  ? 'border-amber-500/50 bg-amber-500/10'
                  : 'border-gray-700 hover:border-gray-600'
              }`}
            >
              <input
                type="checkbox"
                className="accent-amber-500"
                checked={perms.has(key)}
                onChange={() => togglePerm(key)}
              />
              <span className="text-sm text-gray-300">{t(`perm_${key}`)}</span>
            </label>
          ))}
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

export default function Roles() {
  const qc = useQueryClient()
  const t = useT()
  const [modal, setModal] = useState(null)
  const [deleteTarget, setDeleteTarget] = useState(null)

  const { data: roles = [], isLoading } = useQuery({
    queryKey: ['roles'],
    queryFn: () => api.get('/roles/').then((r) => r.data),
  })

  const createMutation = useMutation({
    mutationFn: (data) => api.post('/roles/', data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['roles'] }); setModal(null) },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => api.patch(`/roles/${id}`, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['roles'] }); setModal(null) },
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => api.delete(`/roles/${id}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['roles'] }); setDeleteTarget(null) },
  })

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-100">{t('roles_title')}</h1>
        <button onClick={() => setModal('add')} className="btn-primary btn-sm">
          <Plus size={16} />
          {t('roles_new')}
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16"><Spinner className="text-amber-500 w-8 h-8" /></div>
      ) : (
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('roles_col_name')}</th>
                <th>{t('roles_col_description')}</th>
                <th>{t('roles_col_perms')}</th>
                <th style={{ width: 80 }} />
              </tr>
            </thead>
            <tbody>
              {roles.map((role) => (
                <tr key={role.id}>
                  <td className="font-medium">{role.name}</td>
                  <td className="text-gray-400">{role.description ?? <span className="text-gray-600">—</span>}</td>
                  <td><PermsBadges permissions={role.permissions} t={t} /></td>
                  <td>
                    <div className="flex gap-1">
                      <button onClick={() => setModal(role)} className="btn-ghost btn-sm p-1.5">
                        <Edit2 size={14} />
                      </button>
                      <button
                        onClick={() => setDeleteTarget(role)}
                        disabled={role.name === 'admin'}
                        className="btn-ghost btn-sm p-1.5 text-red-400 hover:text-red-300 hover:bg-red-900/20 disabled:opacity-30"
                        title={role.name === 'admin' ? t('roles_cant_delete_admin') : ''}
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

      <Modal open={modal === 'add'} onClose={() => setModal(null)} title={t('roles_add_title')} size="md">
        <RoleForm
          t={t}
          onSubmit={(data) => createMutation.mutate(data)}
          isPending={createMutation.isPending}
          error={createMutation.error}
          onCancel={() => setModal(null)}
        />
      </Modal>

      <Modal open={!!modal && modal !== 'add'} onClose={() => setModal(null)} title={t('roles_edit_title')} size="md">
        {modal && modal !== 'add' && (
          <RoleForm
            t={t}
            initial={modal}
            onSubmit={(data) => updateMutation.mutate({ id: modal.id, data })}
            isPending={updateMutation.isPending}
            error={updateMutation.error}
            onCancel={() => setModal(null)}
          />
        )}
      </Modal>

      <Modal open={!!deleteTarget} onClose={() => setDeleteTarget(null)} title={t('roles_delete_title')} size="sm">
        {deleteTarget && (
          <div className="space-y-4">
            <p className="text-gray-300">
              {t('roles_delete_q', { name: deleteTarget.name })}
              {' '}{t('roles_delete_warning')}
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
