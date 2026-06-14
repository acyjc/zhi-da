// 纯 CSS 垂直步骤进度条——已完成/进行中(脉冲动画)/未开始三种状态
import { useAppStore } from '../../stores/appStore'

interface PhaseData {
  goal: string
  weeks: number
  completed: boolean
  current: boolean
}

interface StageProgressProps {
  phases: PhaseData[]
}

const containerStyle: React.CSSProperties = {
  width: '100%',
  background: 'transparent',
  borderRadius: 12,
  padding: '20px 24px',
  boxSizing: 'border-box',
  display: 'flex',
  flexDirection: 'column',
}

const nodeSize = 16
const lineWidth = 2

function getNodeColor(completed: boolean, current: boolean): string {
  if (completed) return 'var(--accent-green)'
  if (current) return 'var(--accent-primary)'
  return 'var(--border-light)'
}

function getNodeBorder(completed: boolean, current: boolean): string {
  if (completed) return 'var(--accent-green)'
  if (current) return 'var(--accent-primary)'
  return 'var(--border-light)'
}

function getLineColor(completed: boolean): string {
  return completed ? 'var(--accent-green)' : 'var(--border-light)'
}

function getTitleColor(completed: boolean, current: boolean): string {
  if (completed) return 'var(--accent-green)'
  if (current) return 'var(--accent-primary)'
  return 'var(--text-secondary)'
}

export default function StageProgress({ phases }: StageProgressProps) {
  const { theme } = useAppStore()
  const isDark = theme === 'dark'

  return (
    <div style={containerStyle}>
      {phases.map((phase, index) => {
        const isLast = index === phases.length - 1
        const nodeColor = getNodeColor(phase.completed, phase.current)
        const nodeBorder = getNodeBorder(phase.completed, phase.current)
        const lineColor = getLineColor(phase.completed)
        const titleColor = getTitleColor(phase.completed, phase.current)

        return (
          <div
            key={index}
            style={{
              display: 'flex',
              flex: isLast ? '0 0 auto' : '1 0 auto',
              minHeight: isLast ? undefined : 60,
            }}
          >
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                width: nodeSize + 8,
                flexShrink: 0,
              }}
            >
              <div
                style={{
                  width: nodeSize,
                  height: nodeSize,
                  borderRadius: '50%',
                  backgroundColor: phase.completed
                    ? nodeColor
                    : 'transparent',
                  border: `2px solid ${nodeBorder}`,
                  boxSizing: 'border-box',
                  position: 'relative',
                  flexShrink: 0,
                  marginTop: 2,
                }}
              >
                {phase.completed && (
                  <svg
                    width={nodeSize}
                    height={nodeSize}
                    viewBox="0 0 16 16"
                    style={{ position: 'absolute', top: -2, left: -2 }}
                  >
                    <path
                      d="M4 8l3 3 5-5"
                      stroke={isDark ? '#16181d' : '#f8f7f4'}
                      strokeWidth="2"
                      fill="none"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                )}
                {phase.current && (
                  <div
                    style={{
                      position: 'absolute',
                      top: -4,
                      left: -4,
                      width: nodeSize + 8,
                      height: nodeSize + 8,
                      borderRadius: '50%',
                      border: `2px solid ${nodeColor}`,
                      opacity: 0.4,
                      animation: 'stage-pulse 2s ease-in-out infinite',
                    }}
                  />
                )}
              </div>
              {!isLast && (
                <div
                  style={{
                    width: lineWidth,
                    flex: 1,
                    backgroundColor: lineColor,
                    marginTop: 4,
                  }}
                />
              )}
            </div>

            <div
              style={{
                marginLeft: 14,
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'flex-start',
                paddingBottom: isLast ? 0 : 12,
              }}
            >
              <span
                style={{
                  fontSize: 14,
                  fontWeight: 600,
                  color: titleColor,
                  lineHeight: 1.4,
                }}
              >
                {phase.goal}
              </span>
              <span
                style={{
                  fontSize: 12,
                  color: 'var(--text-tertiary)',
                  marginTop: 2,
                  fontFamily: "var(--font-display)",
                }}
              >
                {phase.weeks} 周
              </span>
            </div>
          </div>
        )
      })}
      <style>{`
        @keyframes stage-pulse {
          0%, 100% { opacity: 0.4; transform: scale(1); }
          50% { opacity: 0.15; transform: scale(1.2); }
        }
      `}</style>
    </div>
  )
}
