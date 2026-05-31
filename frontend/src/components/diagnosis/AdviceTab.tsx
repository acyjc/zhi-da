// 职业建议 Tab——建议文本 + 推荐方向标签 + AI 推理依据面板
import type { FC } from 'react'
import AIReasoning from '../shared/AIReasoning'

interface Props {
  careerAdvice: string
  aiReasoning: Record<string, any>
  recommendedDirections?: string[]
}

const AdviceTab: FC<Props> = ({ careerAdvice, aiReasoning, recommendedDirections }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div style={{
        position: 'relative',
        padding: '20px 20px 20px 28px',
        borderRadius: 10,
        border: '1px solid var(--border-light)',
        background: 'var(--bg-card)',
      }}>
        <div style={{
          position: 'absolute',
          left: 0,
          top: 12,
          bottom: 12,
          width: 3,
          borderRadius: 2,
          background: 'var(--accent-teal)',
        }} />
        <div style={{
          fontSize: 14,
          color: 'var(--text-primary)',
          lineHeight: 1.9,
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
        }}>
          {careerAdvice || '暂无职业建议'}
        </div>
      </div>

      {recommendedDirections && recommendedDirections.length > 0 && (
        <div>
          <div style={{
            fontSize: 12, color: 'var(--text-tertiary)',
            fontFamily: 'var(--font-display)', letterSpacing: '1px',
            textTransform: 'uppercase', marginBottom: 10,
          }}>
            推荐方向
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {recommendedDirections.map((dir, i) => (
              <span
                key={i}
                style={{
                  padding: '6px 16px',
                  borderRadius: 20,
                  border: '1px solid var(--border-light)',
                  background: 'var(--bg-card)',
                  color: 'var(--accent-teal)',
                  fontSize: 12,
                  fontWeight: 500,
                  fontFamily: 'var(--font-display)',
                }}
              >
                {dir}
              </span>
            ))}
          </div>
        </div>
      )}

      {aiReasoning && Object.keys(aiReasoning).length > 0 && (
        <AIReasoning reasoning={aiReasoning} />
      )}
    </div>
  )
}

export default AdviceTab
