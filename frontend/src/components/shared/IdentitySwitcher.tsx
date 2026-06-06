import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppStore } from '../../stores/appStore'

export default function IdentitySwitcher() {
  const { role, mockStudentId, mockEnterpriseId, setRole, setMockStudentId, setMockEnterpriseId } = useAppStore()
  const [open, setOpen] = useState(false)
  const [visible, setVisible] = useState(false)
  const navigate = useNavigate()

  const handleRoleChange = (newRole: 'student' | 'enterprise' | 'admin') => {
    setRole(newRole)
    setOpen(false)
    if (newRole === 'student') {
      navigate('/')
    } else if (newRole === 'enterprise') {
      navigate('/enterprise')
    } else if (newRole === 'admin') {
      navigate('/admin')
    }
  }

  const roleLabels = {
    student: '学生端 (Student)',
    enterprise: '企业端 (Enterprise)',
    admin: '学校管理员 (Admin)',
  }

  const roleIcons = {
    student: '🎓',
    enterprise: '💼',
    admin: '🏛️',
  }

  return (
    <>
      {/* Dev Switcher Toggle in bottom-left */}
      <button
        onClick={() => setVisible(!visible)}
        style={{
          position: 'fixed',
          bottom: 16,
          left: 16,
          zIndex: 10001,
          background: 'rgba(255, 255, 255, 0.4)',
          border: '1px solid var(--border-light, rgba(0,0,0,0.1))',
          borderRadius: '50%',
          width: 28,
          height: 28,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          opacity: 0.3,
          transition: 'all 0.2s ease',
          fontSize: '12px',
        }}
        onMouseEnter={e => {
          e.currentTarget.style.opacity = '0.9'
          e.currentTarget.style.background = 'rgba(255, 255, 255, 0.85)'
        }}
        onMouseLeave={e => {
          e.currentTarget.style.opacity = '0.3'
          e.currentTarget.style.background = 'rgba(255, 255, 255, 0.4)'
        }}
        title="切换开发调试面板"
      >
        ⚙️
      </button>

      {visible && (
        <div style={{
          position: 'fixed',
          top: 16,
          left: 16,
          zIndex: 10000,
          fontFamily: 'system-ui, sans-serif',
        }}>
          {/* Trigger Button */}
          <button
            onClick={() => setOpen(!open)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '8px 14px',
              background: 'rgba(255, 255, 255, 0.85)',
              backdropFilter: 'blur(10px)',
              border: '1px solid var(--border-light, rgba(0,0,0,0.1))',
              borderRadius: '20px',
              boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
              cursor: 'pointer',
              fontSize: '13px',
              fontWeight: 600,
              color: '#333',
              transition: 'all 0.2s ease',
            }}
            onMouseEnter={e => {
              e.currentTarget.style.transform = 'translateY(-1px)'
              e.currentTarget.style.boxShadow = '0 6px 16px rgba(0,0,0,0.12)'
            }}
            onMouseLeave={e => {
              e.currentTarget.style.transform = 'translateY(0)'
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.08)'
            }}
          >
            <span>{roleIcons[role]}</span>
            <span>{roleLabels[role]}</span>
            <span style={{ fontSize: '10px', opacity: 0.6 }}>▼</span>
          </button>

          {/* Dropdown Menu */}
          {open && (
            <div style={{
              position: 'absolute',
              top: 'calc(100% + 8px)',
              left: 0,
              width: '260px',
              background: 'var(--bg-card, #ffffff)',
              border: '1px solid var(--border-light, rgba(0,0,0,0.1))',
              borderRadius: '16px',
              boxShadow: 'var(--shadow-lg, 0 10px 25px rgba(0,0,0,0.15))',
              padding: '12px',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
              animation: 'slideUp 0.2s ease-out',
            }}>
              <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-tertiary, #999)', padding: '2px 8px 6px', borderBottom: '1px solid var(--border-light, rgba(0,0,0,0.05))' }}>
                DEMO 身份模拟切换器
              </div>

              {/* Role Options */}
              {(['student', 'enterprise', 'admin'] as const).map((r) => (
                <button
                  key={r}
                  onClick={() => handleRoleChange(r)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                    padding: '10px 12px',
                    background: role === r ? 'var(--bg-hover, rgba(0,0,0,0.05))' : 'transparent',
                    border: 'none',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    textAlign: 'left',
                    fontSize: '13px',
                    fontWeight: role === r ? 700 : 500,
                    color: role === r ? 'var(--accent-teal, #14b8a6)' : 'var(--text-primary, #333)',
                    transition: 'background 0.2s',
                  }}
                  onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-hover, rgba(0,0,0,0.03))')}
                  onMouseLeave={e => (e.currentTarget.style.background = role === r ? 'var(--bg-hover, rgba(0,0,0,0.05))' : 'transparent')}
                >
                  <span style={{ fontSize: '16px' }}>{roleIcons[r]}</span>
                  <span style={{ flex: 1 }}>{roleLabels[r]}</span>
                  {role === r && <span style={{ fontSize: '12px' }}>✓</span>}
                </button>
              ))}

              {/* Config Fields for IDs */}
              {role === 'student' && (
                <div style={{
                  marginTop: '4px',
                  padding: '8px',
                  background: 'var(--bg-hover, rgba(0,0,0,0.02))',
                  borderRadius: '8px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 4,
                }}>
                  <label style={{ fontSize: '11px', color: 'var(--text-secondary, #666)', fontWeight: 600 }}>
                    模拟学生 ID:
                  </label>
                  <input
                    type="text"
                    value={mockStudentId}
                    onChange={(e) => setMockStudentId(e.target.value)}
                    style={{
                      padding: '4px 8px',
                      borderRadius: '6px',
                      border: '1px solid var(--border-light, #ddd)',
                      fontSize: '12px',
                      outline: 'none',
                      background: 'var(--bg-card, #fff)',
                      color: 'var(--text-primary, #333)',
                    }}
                  />
                </div>
              )}

              {role === 'enterprise' && (
                <div style={{
                  marginTop: '4px',
                  padding: '8px',
                  background: 'var(--bg-hover, rgba(0,0,0,0.02))',
                  borderRadius: '8px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 4,
                }}>
                  <label style={{ fontSize: '11px', color: 'var(--text-secondary, #666)', fontWeight: 600 }}>
                    模拟企业 ID:
                  </label>
                  <input
                    type="text"
                    value={mockEnterpriseId}
                    onChange={(e) => setMockEnterpriseId(e.target.value)}
                    style={{
                      padding: '4px 8px',
                      borderRadius: '6px',
                      border: '1px solid var(--border-light, #ddd)',
                      fontSize: '12px',
                      outline: 'none',
                      background: 'var(--bg-card, #fff)',
                      color: 'var(--text-primary, #333)',
                    }}
                  />
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </>
  )
}
