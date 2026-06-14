// 就业推荐 Tab——岗位推荐卡片，含圆形进度、推荐理由、匹配/缺失技能
import type { FC } from 'react'
import type { RecommendedJob } from '../../types'

interface Props {
  top5Jobs: RecommendedJob[]
}

const rankBadgeColors: Record<number, string> = {
  1: 'var(--accent-warning)',
  2: '#c0c0c0',
  3: '#cd7f32',
  4: 'var(--accent-primary)',
  5: 'var(--accent-primary)',
}

const RecommendTab: FC<Props> = ({ top5Jobs }) => {
  if (!top5Jobs || top5Jobs.length === 0) {
    return (
      <div style={{
        textAlign: 'center', padding: 60,
        color: 'var(--text-tertiary)', fontSize: 14,
      }}>
        暂无岗位推荐数据
      </div>
    )
  }

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
      gap: 16,
    }}>
      {top5Jobs.map((job, i) => {
        const rank = i + 1
        // 兼容 match_score 和旧的 score 字段
        const pct = ((job.match_score ?? (job as any).score ?? 0)) * 100
        const color = pct >= 70 ? 'var(--accent-success)' : pct >= 40 ? 'var(--accent-warning)' : 'var(--accent-primary)'
        const circumference = 2 * Math.PI * 28
        const offset = circumference - (pct / 100) * circumference

        return (
          <div
            key={job.job_id || i}
            style={{
              padding: 18,
              borderRadius: 12,
              border: '1px solid var(--border-light)',
              background: 'var(--bg-card)',
              transition: 'all 0.3s ease',
              cursor: 'default',
            }}
            onMouseEnter={e => {
              e.currentTarget.style.transform = 'translateY(-4px)'
              e.currentTarget.style.boxShadow = `0 8px 24px rgba(0,113,227,0.12)`
              e.currentTarget.style.borderColor = 'var(--accent-primary)'
            }}
            onMouseLeave={e => {
              e.currentTarget.style.transform = ''
              e.currentTarget.style.boxShadow = ''
              e.currentTarget.style.borderColor = 'var(--border-light)'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
              <div
                style={{
                  width: 32, height: 32, borderRadius: 8,
                  background: rankBadgeColors[rank] || 'var(--text-tertiary)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontWeight: 700, fontSize: 14, color: '#fff',
                  fontFamily: 'var(--font-mono)',
                }}
              >
                {rank}
              </div>
              <div style={{ position: 'relative', width: 64, height: 64 }}>
                <svg width="64" height="64" viewBox="0 0 64 64">
                  <circle cx="32" cy="32" r="28" fill="none" stroke="var(--border-light)" strokeWidth="4" />
                  <circle
                    cx="32" cy="32" r="28"
                    fill="none"
                    stroke={color}
                    strokeWidth="4"
                    strokeLinecap="round"
                    strokeDasharray={circumference}
                    strokeDashoffset={offset}
                    transform="rotate(-90 32 32)"
                    style={{ transition: 'stroke-dashoffset 0.8s ease' }}
                  />
                </svg>
                <div style={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  fontSize: 13,
                  fontFamily: "var(--font-display)",
                  fontWeight: 700,
                  color,
                }}>
                  {pct.toFixed(0)}%
                </div>
              </div>
            </div>
            <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', fontFamily: 'var(--font-display)', marginBottom: 4 }}>
              {job.title}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', marginBottom: 10 }}>
              {job.company || '知名企业'}
            </div>

            {/* 推荐理由 */}
            {job.reason && (
              <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: 8, padding: '6px 10px', borderLeft: '2px solid var(--accent-primary)', background: 'var(--bg-hover)', borderRadius: '0 4px 4px 0' }}>
                {job.reason}
              </div>
            )}

            {/* 匹配技能 */}
            {job.matched_skills && job.matched_skills.length > 0 && (
              <div style={{ marginBottom: 6 }}>
                <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginBottom: 3 }}>匹配技能</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                  {job.matched_skills.map(s => (
                    <span key={s} style={{ fontSize: 10, padding: '2px 7px', borderRadius: 4, background: 'rgba(52,199,89,0.15)', color: 'var(--accent-success)' }}>{s}</span>
                  ))}
                </div>
              </div>
            )}

            {/* 缺失技能 */}
            {job.missing_skills && job.missing_skills.length > 0 && (
              <div style={{ marginBottom: 8 }}>
                <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginBottom: 3 }}>待提升</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                  {job.missing_skills.map(s => (
                    <span key={s} style={{ fontSize: 10, padding: '2px 7px', borderRadius: 4, background: 'rgba(255,149,0,0.15)', color: 'var(--accent-warning)' }}>{s}</span>
                  ))}
                </div>
              </div>
            )}

            <div style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              匹配度 <span style={{ color, fontWeight: 600, fontFamily: 'var(--font-mono)' }}>{pct.toFixed(0)}%</span>，
              {pct >= 70
                ? '高度匹配，建议重点关注该岗位'
                : pct >= 40
                  ? '中等匹配，可针对性提升短板'
                  : '较低匹配，建议优先夯实基础能力'}
            </div>

            {/* 置信度 */}
            {job.confidence !== undefined && (
              <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginTop: 4 }}>
                置信度 {(job.confidence * 100).toFixed(0)}%
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

export default RecommendTab
