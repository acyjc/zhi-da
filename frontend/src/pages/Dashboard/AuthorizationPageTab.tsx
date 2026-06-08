// 岗位授权 Tab——整合 RecommendTab（岗位推荐）和 AuthorizationTab（授权管理）
import type { FC } from 'react'
import type { DiagnosisResult, RecommendedJob, Student } from '../../types'
import RecommendTab from '../../components/diagnosis/RecommendTab'
import AuthorizationTab from '../../components/diagnosis/AuthorizationTab'

interface AuthorizationPageTabProps {
  student: Student
  diagnosisResult: DiagnosisResult
}

const AuthorizationPageTab: FC<AuthorizationPageTabProps> = ({
  student,
  diagnosisResult,
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xl)' }}>
      <RecommendTab top5Jobs={diagnosisResult.top5_jobs} />
      <AuthorizationTab
        student={student}
        diagnosisResult={diagnosisResult}
      />
    </div>
  )
}

export default AuthorizationPageTab
