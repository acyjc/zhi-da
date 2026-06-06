// 水平步骤条——wait/process(脉冲动画)/finish/error 四种状态，连接线渐变
import type { FC } from 'react'

interface Step {
  label: string
  status: 'wait' | 'process' | 'finish' | 'error'
}

interface Props {
  steps: Step[]
}

const statusColors: Record<Step['status'], { bg: string; border: string; text: string }> = {
  wait: { bg: 'transparent', border: 'var(--text-tertiary)', text: 'var(--text-tertiary)' },
  process: { bg: 'rgba(91,123,181,0.15)', border: 'var(--accent-blue)', text: 'var(--accent-blue)' },
  finish: { bg: 'rgba(107,168,122,0.15)', border: 'var(--accent-green)', text: 'var(--accent-green)' },
  error: { bg: 'rgba(196,122,139,0.15)', border: 'var(--accent-rose)', text: 'var(--accent-rose)' },
}

const StatusIcon: FC<{ status: Step['status'] }> = ({ status }) => {
  const base: React.CSSProperties = {
    width: 32, height: 32, borderRadius: '50%', display: 'flex',
    alignItems: 'center', justifyContent: 'center', flexShrink: 0,
    fontWeight: 600, fontSize: 14, fontFamily: 'var(--font-mono)',
    border: `2px solid ${statusColors[status].border}`,
    background: statusColors[status].bg,
    color: statusColors[status].text,
    transition: 'all 0.3s ease',
  }
  if (status === 'finish') return <div style={base}>✓</div>
  if (status === 'error') return <div style={base}>✕</div>
  if (status === 'process') return (
    <div style={{ ...base, animation: 'pulseGlow 1.5s ease-in-out infinite' }} />
  )
  return <div style={base} />
}

const ConnectLine: FC<{ status: Exclude<Step['status'], 'error'> }> = ({ status }) => {
  const bg = status === 'finish' ? 'var(--accent-green)' : status === 'process' ? 'var(--accent-blue)' : 'var(--text-tertiary)'
  return (
    <div style={{
      flex: 1, height: 2, minWidth: 24, margin: '0 4px',
      background: bg, transition: 'background 0.4s ease',
    }} />
  )
}

const ProgressSteps: FC<Props> = ({ steps }) => {
  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'center', padding: '32px 16px', gap: 0 }}>
      {steps.map((step, i) => {
        const isLast = i === steps.length - 1
        return (
          <div key={i} style={{ display: 'flex', alignItems: 'flex-start', flex: isLast ? '0 0 auto' : 1 }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8, minWidth: 64 }}>
              <StatusIcon status={step.status} />
              <span style={{
                fontSize: 12, color: step.status === 'wait' ? 'var(--text-tertiary)' : 'var(--text-secondary)',
                textAlign: 'center', lineHeight: 1.4, fontFamily: 'var(--font-display)',
                fontWeight: step.status === 'process' ? 600 : 400,
              }}>
                {step.label}
              </span>
            </div>
            {!isLast && (
              <ConnectLine status={step.status === 'error' ? 'wait' : step.status as Exclude<Step['status'], 'error'>} />
            )}
          </div>
        )
      })}
    </div>
  )
}

export default ProgressSteps
