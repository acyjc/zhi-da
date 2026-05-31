// 可折叠推理面板——展示 AI 建议的推理依据和置信度条(琥珀→绿色渐变)
import { useState, type FC } from 'react'

interface Props {
  reasoning: Record<string, { basis: string; confidence: number }>
}

const AIReasoning: FC<Props> = ({ reasoning }) => {
  const [expanded, setExpanded] = useState(false)
  const entries = Object.entries(reasoning)

  return (
    <div style={{
      border: '1px solid var(--border-light)',
      borderRadius: 8,
      overflow: 'hidden',
      background: 'var(--bg-card)',
    }}>
      <button
        onClick={() => setExpanded(!expanded)}
        style={{
          width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '12px 16px', background: 'var(--bg-hover)',
          border: 'none', cursor: 'pointer', color: 'var(--text-primary)',
          fontFamily: 'var(--font-display)', fontSize: 15, fontWeight: 600,
          letterSpacing: '0.5px',
        }}
      >
        <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--accent-violet)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm-1 5h2v6h-2zm1 8h0"/>
            <circle cx="12" cy="19" r="1" fill="var(--accent-violet)" stroke="none"/>
          </svg>
          AI 推理依据
        </span>
        <svg
          width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--text-secondary)"
          strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
          style={{ transform: expanded ? 'rotate(180deg)' : 'rotate(0)', transition: 'transform 0.3s ease' }}
        >
          <polyline points="6 9 12 15 18 9"/>
        </svg>
      </button>
      <div style={{
        maxHeight: expanded ? 600 : 0,
        overflow: 'hidden',
        transition: 'max-height 0.35s ease',
      }}>
        <div style={{ padding: '12px 16px 16px', display: 'flex', flexDirection: 'column', gap: 14 }}>
          {entries.map(([key, item], i) => (
            <div key={i}>
              <div style={{ fontSize: 13, color: 'var(--text-primary)', fontWeight: 600, marginBottom: 4 }}>
                {key}
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: 8 }}>
                {item.basis}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{
                  flex: 1, height: 4, borderRadius: 2, background: 'var(--border-light)',
                  overflow: 'hidden',
                }}>
                  <div style={{
                    height: '100%', borderRadius: 2,
                    width: `${item.confidence * 100}%`,
                    background: item.confidence >= 0.7
                      ? 'var(--accent-green)'
                      : item.confidence >= 0.4
                        ? 'var(--accent-amber)'
                        : 'var(--accent-rose)',
                    transition: 'width 0.6s ease',
                  }}/>
                </div>
                <span style={{
                  fontSize: 11, color: 'var(--text-tertiary)',
                  fontFamily: 'var(--font-mono)', minWidth: 36, textAlign: 'right',
                }}>
                  {(item.confidence * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default AIReasoning
