// 成长总览 Tab——整合 ProfileTab（能力画像）和 GrowthTab（成长趋势追踪）
import type { FC } from 'react'
import type { AbilityProfile, Student, DiagnosisResult } from '../../types'
import ProfileTab from '../../components/diagnosis/ProfileTab'
import GrowthTab from '../../components/diagnosis/GrowthTab'
import EmptyState from '../../components/shared/EmptyState'

interface OverviewTabProps {
  profile: AbilityProfile
  dimensionChanges: Record<string, number>
  student: Student
  growthPath: { phases: Array<any> }
  diagnosisHistory: DiagnosisResult[]
}

const OverviewTab: FC<OverviewTabProps> = ({
  profile,
  dimensionChanges,
  student,
  growthPath,
  diagnosisHistory,
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xl)' }}>
      <ProfileTab
        profile={profile}
        changes={dimensionChanges}
        student={student}
      />

      {(!growthPath?.phases || growthPath.phases.length === 0) && (
        <div className="surface-card" style={{ padding: 'var(--space-4)' }}>
          <EmptyState
            icon="📋"
            title="暂无成长任务"
            description="完成诊断后系统会为你生成个性化成长任务"
          />
        </div>
      )}

      <GrowthTab history={diagnosisHistory} />
    </div>
  )
}

export default OverviewTab
