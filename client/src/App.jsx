import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import Layout from './components/Layout'
import Login from './pages/Login'
import Tables from './pages/Tables'
import TableDetail from './pages/TableDetail'
import Menu from './pages/Menu'
import Stock from './pages/Stock'
import Users from './pages/Users'
import Roles from './pages/Roles'
import Stats from './pages/Stats'
import Audit from './pages/Audit'

function RequireAuth({ children }) {
  const accessToken = useAuthStore((s) => s.accessToken)
  const refreshToken = useAuthStore((s) => s.refreshToken)
  if (!accessToken && !refreshToken) return <Navigate to="/login" replace />
  return children
}

function RequirePerm({ permission, children }) {
  const user = useAuthStore((s) => s.user)
  if (permission && !user?.permissions?.includes(permission)) {
    return <Navigate to="/tables" replace />
  }
  return children
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <RequireAuth>
              <Layout />
            </RequireAuth>
          }
        >
          <Route index element={<Navigate to="/tables" replace />} />
          <Route path="tables" element={<Tables />} />
          <Route path="tables/:id" element={<TableDetail />} />
          <Route
            path="menu"
            element={
              <RequirePerm permission="items">
                <Menu />
              </RequirePerm>
            }
          />
          <Route
            path="stock"
            element={
              <RequirePerm permission="stock">
                <Stock />
              </RequirePerm>
            }
          />
          <Route
            path="users"
            element={
              <RequirePerm permission="users">
                <Users />
              </RequirePerm>
            }
          />
          <Route
            path="roles"
            element={
              <RequirePerm permission="roles">
                <Roles />
              </RequirePerm>
            }
          />
          <Route
            path="stats"
            element={
              <RequirePerm permission="stats">
                <Stats />
              </RequirePerm>
            }
          />
          <Route
            path="audit"
            element={
              <RequirePerm permission="roles">
                <Audit />
              </RequirePerm>
            }
          />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
