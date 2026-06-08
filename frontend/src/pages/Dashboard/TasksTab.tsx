// 成长任务 Tab——封装 PathTab（成长路径与任务管理）
import type { FC } from 'react'
import type { GrowthPhase } from '../../types'
import PathTab from '../../components/diagnosis/PathTab'

interface TasksTabProps {
  growthPath: { phases: GrowthPhase[] }
  diagnosisId: string
  studentId: string | number
  onTaskComplete: (taskId: string) => void
  onReEvaluateComplete: (newDiagnosisId: string) => void
}

const TasksTab: FC<TasksTabProps> = ({
  growthPath,
  diagnosisId,
  studentId,
  onTaskComplete,
  onReEvaluateComplete,
}) => {
  return (
    <PathTab
      growthPath={growthPath}
      diagnosisId={diagnosisId}
      studentId={studentId}
      onTaskComplete={onTaskComplete}
      onReEvaluateComplete={onReEvaluateComplete}
    />
  )
}

export default TasksTab
