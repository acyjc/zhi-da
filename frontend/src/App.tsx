import { Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import ProfileInput from './pages/ProfileInput'
import Dashboard from './pages/Dashboard'
import SalaryCat from './components/SalaryCat/SalaryCat'

export default function App() {
  return (
    <>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/input" element={<ProfileInput />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
      <SalaryCat />
    </>
  )
}
