import { Routes, Route, useLocation } from 'react-router-dom'
import Home from './pages/Home'
import ProfileInput from './pages/ProfileInput'
import Dashboard from './pages/Dashboard'
import AdminDashboard from './pages/AdminDashboard'
import EnterpriseDashboard from './pages/EnterpriseDashboard'
import NotFound from './pages/NotFound'
import SalaryCat from './components/SalaryCat/SalaryCat'
import IdentitySwitcher from './components/shared/IdentitySwitcher'

export default function App() {
  const location = useLocation()
  const isStudentPage = location.pathname.startsWith('/student')
  const showIdentitySwitcher = localStorage.getItem('show_identity_switcher') === '1'

  return (
    <>
      {showIdentitySwitcher && <IdentitySwitcher />}

      <Routes>
        {/* Three-Tier Portal Hub */}
        <Route path="/" element={<Home />} />

        {/* Student Portal */}
        <Route path="/student/input" element={<ProfileInput />} />
        <Route path="/student/dashboard" element={<Dashboard />} />

        {/* School Admin Portal */}
        <Route path="/admin" element={<AdminDashboard />} />

        {/* Enterprise Portal */}
        <Route path="/enterprise" element={<EnterpriseDashboard />} />

        {/* 404 Fallback */}
        <Route path="*" element={<NotFound />} />
      </Routes>

      {/* Mascot desktop cat helper - only shown on student pages */}
      {isStudentPage && <SalaryCat />}
    </>
  )
}
