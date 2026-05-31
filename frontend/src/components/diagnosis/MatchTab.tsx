// 岗位匹配 Tab——ECharts 仪表盘 + 四维匹配度卡 + TOP5 岗位进度条 + GapBar 差距分析
import type { FC } from 'react'
import type { GapDetail } from '../../types'
import MatchGauge from '../charts/MatchGauge'
import GapBar from '../charts/GapBar'

interface Props {
  matchScore: number
  previousScore?: number
  dimensionScores: Record<string, number>
  top5Jobs: any[]
  gapDetails: GapDetail[]
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

const MatchTab: FC<Props> = ({ matchScore, previousScore, dimensionScores, top5Jobs, gapDetails }) => {
  const gapBarData = gapDetails.map(g => ({ skill: g.skill, current: g.current, required: g.required }))

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24, alignItems: 'center' }}>
      {/* 综合匹配度仪表盘 */}
      <div style={{ padding: '16px 0 8px', width: 220, height: 200 }}>
        <MatchGauge score={matchScore} previousScore={previousScore} />
      </div>

      {/* 四维匹配度卡片(4列) */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: 12,
        width: '100%',
      }}>
        {Object.entries(dimLabels).map(([key, label]) => {
          const score = dimensionScores[key] ?? 0
          const color = dimColors[key] ?? 'var(--accent-blue)'
          return (
            <div
              key={key}
              style={{
                padding: 14,
                borderRadius: 10,
                border: '1px solid var(--border-light)',
                background: 'var(--bg-card)',
                textAlign: 'center',
              }}
            >
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 6 }}>{label}</div>
              <div style={{ fontSize: 28, fontFamily: "Rajdhani, sans-serif", fontWeight: 700, color, lineHeight: 1 }}>
                {(score * 100).toFixed(0)}%
              </div>
            </div>
          )
        })}
      </div>

      {/* TOP5 岗位排行 */}
      {top5Jobs.length > 0 && (
        <div style={{ width: '100%' }}>
          <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginBottom: 10, letterSpacing: '1px', textTransform: 'uppercase' }}>
            TOP5 匹配岗位
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {top5Jobs.map((job, i) => {
              const jScore = typeof job.score === 'number' ? job.score : 0
              const jPct = jScore * 100
              const barColor = jPct >= 70 ? 'var(--accent-green)' : jPct >= 40 ? 'var(--accent-amber)' : 'var(--accent-blue)'
              return (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 14px', borderRadius: 8, border: '1px solid var(--border-light)', background: 'var(--bg-card)' }}>
                  <span style={{ width: 24, height: 24, borderRadius: 6, background: 'var(--bg-hover)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)' }}>{i + 1}</span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>{job.title} {job.company && <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>@{job.company}</span>}</div>
                    <div style={{ height: 4, borderRadius: 2, background: 'var(--border-light)', overflow: 'hidden' }}>
                      <div style={{ height: '100%', borderRadius: 2, width: `${jPct}%`, background: barColor, transition: 'width 0.8s ease' }} />
                    </div>
                  </div>
                  <span style={{ fontSize: 14, fontWeight: 700, color: barColor, fontFamily: "Rajdhani, sans-serif", minWidth: 44, textAlign: 'right' }}>{jPct.toFixed(0)}%</span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* 差距分析柱状图 */}
      {gapBarData.length > 0 && (
        <div style={{ width: '100%' }}>
          <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginBottom: 10, letterSpacing: '1px', textTransform: 'uppercase' }}>差距分析</div>
          <div style={{ width: '100%', minHeight: gapBarData.length * 50 }}>
            <GapBar data={gapBarData} />
          </div>
        </div>
      )}
    </div>
  )
}

export default MatchTab
