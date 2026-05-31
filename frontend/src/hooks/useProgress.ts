// 学习进度 Hook——完成任务标记、进度列表加载、技能值同步更新
import { useState, useCallback } from 'react'
import { useAppStore } from '../stores/appStore'
import { completeTask, getProgress } from '../services/api'

export function useProgress() {
  const { student, setStudent } = useAppStore()
  const [completingTaskId, setCompletingTaskId] = useState<string | null>(null)
  const [progressList, setProgressList] = useState<any[]>([])

  const loadProgress = useCallback(async () => {
    if (!student) return
    const data = await getProgress(student.id)
    setProgressList(data)
    return data
  }, [student])

  const handleTaskComplete = useCallback(async (taskId: string, evidence: string = '已完成') => {
    if (!student) return { success: false }
    setCompletingTaskId(taskId)
    try {
      const result = await completeTask({
        student_id: student.id,
        task_id: taskId,
        evidence,
      })
      if (result.success && student) {
        setStudent({ ...student, tech_skills: result.skill_updates ?
          Object.entries(result.skill_updates).reduce((acc, [k, v]: [string, any]) => {
            acc[k] = v.after; return acc
          }, { ...student.tech_skills }) : student.tech_skills
        })
        await loadProgress()
      }
      return result
    } finally {
      setCompletingTaskId(null)
    }
  }, [student, setStudent, loadProgress])

  return { handleTaskComplete, loadProgress, progressList, completingTaskId }
}
