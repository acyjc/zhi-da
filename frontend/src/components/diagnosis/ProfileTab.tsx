// 能力画像 Tab——ECharts 雷达图 + 四维分值卡片(2×2网格) + 技能标签云
import type { FC } from 'react'
import type { AbilityProfile } from '../../types'
import RadarChart from '../charts/RadarChart'

interface Props {
  profile: AbilityProfile
  changes?: Record<string, number>
}

const dimLabels: Record<string, string> = {
  tech_skills: '技术能力',
  project_exp: '项目经验',
  soft_skills: '软技能',
  domain_knowledge: '领域知识',
}

const dimColors: Record<string, string> = {
  tech_skills: 'var(--accent-blue)',
  project_exp: 'var(--accent-teal)',
  soft_skills: 'var(--accent-violet)',
  domain_knowledge: 'var(--accent-amber)',
}

const ProfileTab: FC<Props> = ({ profile, changes }) => {
  const dims = ['tech_skills', 'project_exp', 'soft_skills', 'domain_knowledge'] as const

  const radarData = dims.map(dim => ({
    name: dimLabels[dim],
    value: ((profile[dim]?.weight ?? 0) * 100),
  }))

  const allSkills = dims.flatMap(dim => 
    (profile[dim]?.sub_items ?? []).map(skill => ({ ...skill, dim }))
  )

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div style={{ display: 'flex', gap: 32, alignItems: 'flex-start', flexWrap: 'wrap' }}>
        <div style={{
          flex: '0 0 auto',
          background: 'var(--bg-card)',
          borderRadius: 12,
          border: '1px solid var(--border-light)',
          padding: 20,
        }}>
          {/* 雷达图区域 */}
          <RadarChart data={radarData} />
        </div>

        {/* 四维分值卡片网格 */}
        <div style={{
          flex: 1,
          minWidth: 280,
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 12,
        }}>
          {dims.map(dim => {
            const dimData = profile[dim]
            const score = dimData?.weight ?? 0
            const change = changes?.[dim]

            return (
              <div
                key={dim}
                style={{
                  padding: 16,
                  borderRadius: 10,
                  border: '1px solid var(--border-light)',
                  background: 'var(--bg-card)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 6,
                }}
              >
                <div style={{ fontSize: 11, color: 'var(--text-tertiary)', letterSpacing: '1px', textTransform: 'uppercase' }}>
                  {dimLabels[dim]}
                </div>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                  <span style={{
                    fontSize: 36,
                    fontFamily: "Rajdhani, sans-serif",
                    fontWeight: 700,
                    color: dimColors[dim],
                    lineHeight: 1,
                  }}>
                    {(score * 100).toFixed(0)}%
                  </span>
                  {change !== undefined && change !== 0 && (
                    <span style={{
                      fontSize: 13,
                      fontFamily: 'var(--font-mono)',
                      fontWeight: 600,
                      color: change > 0 ? 'var(--accent-green)' : 'var(--accent-rose)',
                    }}>
                      {change > 0 ? '+' : ''}{(change * 100).toFixed(0)}%
                    </span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* 技能标签云 */}
      {allSkills.length > 0 && (
        <div style={{
          padding: 16,
          borderRadius: 10,
          border: '1px solid var(--border-light)',
          background: 'var(--bg-card)',
        }}>
          <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginBottom: 12, letterSpacing: '1px', textTransform: 'uppercase' }}>
            技能标签云
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {allSkills.map((skill, i) => {
              const opacity = 0.3 + (skill.score / 100) * 0.7
              const dimColorMap: Record<string, string> = {
                tech_skills: '91,123,181',
                project_exp: '90,158,143',
                soft_skills: '139,126,200',
                domain_knowledge: '196,148,74',
              }
              const rgb = dimColorMap[skill.dim] || '91,123,181'
              return (
                <span
                  key={i}
                  style={{
                    padding: '4px 12px',
                    borderRadius: 20,
                    fontSize: 12,
                    fontWeight: 500,
                    color: 'var(--text-primary)',
                    background: `rgba(${rgb},${opacity * 0.25})`,
                    border: `1px solid rgba(${rgb},${opacity * 0.4})`,
                  }}
                >
                  {skill.name}
                  <span style={{ marginLeft: 6, fontSize: 10, color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
                    {skill.score}
                  </span>
                </span>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

export default ProfileTab
