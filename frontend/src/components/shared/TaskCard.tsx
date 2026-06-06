// 任务卡片——pending/completed/in_progress 三种状态，支持标记完成操作
import { useState, type FC } from 'react'
import type { PhaseTask } from '../../types'

interface Props {
  task: PhaseTask
  status: 'pending' | 'completed' | 'in_progress'
  onComplete: (evidence?: string) => void
  loading?: boolean
}

const statusConfig: Record<Props['status'], { icon: string; border: string; bg: string; color: string; iconBg: string }> = {
  pending: {
    icon: '',
    border: 'var(--border-light)',
    bg: 'var(--bg-card)',
    color: 'var(--text-tertiary)',
    iconBg: 'transparent',
  },
  completed: {
    icon: '✓',
    border: 'var(--accent-green)',
    bg: 'rgba(107, 168, 122, 0.08)',
    color: 'var(--accent-green)',
    iconBg: 'var(--accent-green)',
  },
  in_progress: {
    icon: '',
    border: 'var(--accent-blue)',
    bg: 'rgba(91, 123, 181, 0.08)',
    color: 'var(--accent-blue)',
    iconBg: 'rgba(91, 123, 181, 0.2)',
  },
}

const TaskCard: FC<Props> = ({ task, status, onComplete, loading }) => {
  const config = statusConfig[status]
  const showButton = status === 'pending' || status === 'in_progress'
  const [evidence, setEvidence] = useState('')

  return (
    <div style={{
      display: 'flex', gap: 14, padding: 16,
      border: `1px solid ${config.border}`,
      borderRadius: 10, background: config.bg,
      transition: 'all 0.25s ease',
      cursor: 'default',
      ...(showButton ? {} : { opacity: 0.7 }),
    }}
    onMouseEnter={e => {
      e.currentTarget.style.transform = 'translateY(-2px)'
      e.currentTarget.style.boxShadow = 'var(--shadow-md)'
      e.currentTarget.style.borderColor = status === 'pending' ? 'var(--text-tertiary)' : config.border
    }}
    onMouseLeave={e => {
      e.currentTarget.style.transform = ''
      e.currentTarget.style.boxShadow = ''
      e.currentTarget.style.borderColor = config.border
    }}
    >
      <div style={{
        width: 36, height: 36, borderRadius: '50%',
        border: `2px solid ${config.border}`,
        background: config.iconBg,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        flexShrink: 0, color: status === 'completed' ? '#fff' : config.color,
        fontWeight: 700, fontSize: 14,
        fontFamily: 'var(--font-mono)',
        animation: status === 'in_progress' ? 'pulseGlow 1.5s ease-in-out infinite' : 'none',
      }}>
        {config.icon}
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', fontFamily: 'var(--font-display)', letterSpacing: '0.3px', marginBottom: 4 }}>
          {task.name}
        </div>
        <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: 8 }}>
          {task.description}
        </div>
        {task.resources.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 6 }}>
            {task.resources.map((res, i) => (
              <a
                key={i}
                href={res}
                target="_blank"
                rel="noreferrer"
                style={{
                  fontSize: 11, color: 'var(--accent-violet)',
                  textDecoration: 'none', padding: '2px 8px',
                  borderRadius: 4, background: 'rgba(139,126,200,0.08)',
                  border: '1px solid rgba(139,126,200,0.2)',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={e => { e.currentTarget.style.background = 'rgba(139,126,200,0.16)'; e.currentTarget.style.borderColor = 'var(--accent-violet)' }}
                onMouseLeave={e => { e.currentTarget.style.background = 'rgba(139,126,200,0.08)'; e.currentTarget.style.borderColor = 'rgba(139,126,200,0.2)' }}
              >
                {res.length > 40 ? res.slice(0, 40) + '...' : res}
              </a>
            ))}
          </div>
        )}
        <div style={{ fontSize: 11, color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
          达标标准：{task.criteria}
        </div>
        {showButton && (
          <div style={{ marginTop: 10 }}>
            <input
              value={evidence}
              onChange={e => setEvidence(e.target.value)}
              placeholder="完成证据（可选）"
              style={{
                width: '100%', padding: '6px 12px', borderRadius: 6,
                border: '1px solid var(--border-light)', fontSize: 12,
                background: 'var(--bg-card)', color: 'var(--text-primary)',
                marginBottom: 8, outline: 'none',
                transition: 'border-color 0.2s, background-color 0.3s, color 0.3s',
              }}
              onFocus={e => (e.currentTarget.style.borderColor = 'var(--accent-blue)')}
              onBlur={e => (e.currentTarget.style.borderColor = 'var(--border-light)')}
            />
            <button
              onClick={() => onComplete(evidence)}
              disabled={loading}
              style={{
                padding: '6px 18px',
                borderRadius: 6,
                border: `1px solid ${status === 'in_progress' ? 'var(--accent-blue)' : 'var(--accent-teal)'}`,
                background: status === 'in_progress'
                  ? 'rgba(91,123,181,0.15)'
                  : 'transparent',
                color: status === 'in_progress' ? 'var(--accent-blue)' : 'var(--accent-teal)',
                cursor: loading ? 'not-allowed' : 'pointer',
                fontSize: 12, fontWeight: 600,
                fontFamily: 'var(--font-display)',
                letterSpacing: '0.5px',
                transition: 'all 0.2s ease',
                opacity: loading ? 0.6 : 1,
              }}
              onMouseEnter={e => {
                if (!loading) { e.currentTarget.style.background = status === 'in_progress' ? 'rgba(91,123,181,0.25)' : 'rgba(90,158,143,0.15)'; e.currentTarget.style.transform = 'scale(1.03)' }
              }}
              onMouseLeave={e => {
                if (!loading) { e.currentTarget.style.background = status === 'in_progress' ? 'rgba(91,123,181,0.15)' : 'transparent'; e.currentTarget.style.transform = '' }
              }}
            >
              {loading ? '处理中...' : '标记完成'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default TaskCard
