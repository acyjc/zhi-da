// 诊断解释 Tab——整合 MatchTab（岗位匹配分析）和 AdviceTab（职业建议）
import type { FC } from 'react'
import type { DiagnosisResult, GapDetail, RecommendedJob } from '../../types'
import MatchTab from '../../components/diagnosis/MatchTab'
import AdviceTab from '../../components/diagnosis/AdviceTab'

interface DiagnosisTabProps {
  diagnosisResult: DiagnosisResult
  previousScore?: number
}

const DiagnosisTab: FC<DiagnosisTabProps> = ({ diagnosisResult, previousScore }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xl)' }}>
      <MatchTab
        matchScore={diagnosisResult.match_score}
        previousScore={previousScore}
        dimensionScores={diagnosisResult.dimension_scores}
        top5Jobs={diagnosisResult.top5_jobs}
        gapDetails={diagnosisResult.gap_details}
        explanations={diagnosisResult.explanations}
      />
      <AdviceTab
        careerAdvice={diagnosisResult.career_advice}
        aiReasoning={diagnosisResult.ai_reasoning}
        recommendedDirections={diagnosisResult.top5_jobs?.slice(0, 3).map((j: RecommendedJob) => j.title)}
      />
    </div>
  )
}

export default DiagnosisTab
