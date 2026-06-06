// 成长路径 Tab——PathTimeline 阶段时间线 + TaskCard 任务列表 + 标记完成交互
import { useState, useEffect, type FC } from 'react'
import type { GrowthPhase } from '../../types'
import { completeTask, getProgress } from '../../services/api'
import PathTimeline from '../shared/PathTimeline'
import TaskCard from '../shared/TaskCard'

interface Props {
  growthPath: { phases: GrowthPhase[] }
  diagnosisId: string
  studentId: string
  onTaskComplete: (taskId: string) => void
}

const PathTab: FC<Props> = ({ growthPath, diagnosisId, studentId, onTaskComplete }) => {
  const [activePhase, setActivePhase] = useState(0)
  const [completing, setCompleting] = useState<string | null>(null)
  const [completedTasks, setCompletedTasks] = useState<Set<string>>(new Set())
  const [taskError, setTaskError] = useState<string | null>(null)
  const phases = growthPath.phases ?? []

  // 挂载时从后端加载已完成任务，防止刷新丢失状态
  useEffect(() => {
    if (!studentId) return
    getProgress(studentId).then((tasks: any[]) => {
      if (Array.isArray(tasks)) {
        const done = new Set<string>(
          tasks.filter((t: any) => t.status === 'completed').map((t: any) => t.task_name)
        )
        setCompletedTasks(done)
      }
    }).catch(() => { /* 静默降级，不影响主流程 */ })
  }, [studentId])

  if (phases.length === 0) {
    return (
      <div style={{
        textAlign: 'center', padding: 60,
        color: 'var(--text-tertiary)', fontSize: 14,
      }}>
        暂无成长路径数据
      </div>
    )
  }

  const currentPhaseData = phases[activePhase]
  if (!currentPhaseData) return null

  const handleComplete = async (taskName: string, evidence: string = '') => {
    setCompleting(taskName)
    try {
      await completeTask({
        student_id: studentId,
        task_id: taskName,
        evidence,
      })
      setCompletedTasks(prev => new Set([...prev, taskName]))
      onTaskComplete(taskName)
    } catch (err: any) {
      const msg = err?.response?.data?.error || '操作失败，请重试'
      setTaskError(msg)
      setTimeout(() => setTaskError(null), 4000)
    } finally {
      setCompleting(null)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <PathTimeline
        phases={phases}
        currentPhase={activePhase}
      />

      <div style={{ display: 'flex', gap: 16 }}>
        {/* 阶段导航 */}
        <div style={{
          width: 140,
          flexShrink: 0,
          display: 'flex',
          flexDirection: 'column',
          gap: 6,
        }}>
          {phases.map((phase, i) => (
            <button
              key={i}
              onClick={() => setActivePhase(i)}
              style={{
                textAlign: 'left',
                padding: '10px 12px',
                borderRadius: 6,
                border: '1px solid var(--border-light)',
                background: i === activePhase ? 'var(--bg-hover)' : 'transparent',
                color: i === activePhase ? 'var(--text-primary)' : 'var(--text-tertiary)',
                cursor: 'pointer',
                fontSize: 12,
                fontWeight: i === activePhase ? 600 : 400,
                fontFamily: 'var(--font-display)',
                borderLeft: i === activePhase ? '3px solid var(--accent-blue)' : '3px solid transparent',
                transition: 'all 0.2s ease',
              }}
              onMouseEnter={e => { if (i !== activePhase) { e.currentTarget.style.color = 'var(--text-secondary)'; e.currentTarget.style.background = 'rgba(21,29,53,0.6)' } }}
              onMouseLeave={e => { if (i !== activePhase) { e.currentTarget.style.color = 'var(--text-tertiary)'; e.currentTarget.style.background = 'transparent' } }}
            >
              <div style={{ fontWeight: 700, fontFamily: 'var(--font-mono)', fontSize: 10, marginBottom: 2 }}>
                阶段 {i + 1}
              </div>
              <div>{phase.goal}</div>
              <div style={{ fontSize: 10, color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
                {phase.weeks}周 · {phase.tasks.length}个任务
              </div>
            </button>
          ))}
        </div>
        {/* 任务卡片列表 */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 10 }}>
          {currentPhaseData.tasks.map((task, ti) => {
            const taskId = task.name
            const isCompleted = completedTasks.has(taskId)
            const isLoading = completing === taskId
            return (
              <TaskCard
                key={ti}
                task={task}
                status={isCompleted ? 'completed' : ti === 0 ? 'in_progress' : 'pending'}
                onComplete={(evidence) => handleComplete(taskId, evidence)}
                loading={isLoading}
              />
            )
          })}
        </div>
        {taskError && (
          <div style={{ padding: '10px 14px', borderRadius: 'var(--radius-sm)', background: '#fef2f2', border: '1px solid #fecaca', color: '#dc2626', fontSize: 13, marginTop: 8, animation: 'slideUp 0.2s ease-out' }}>
            ⚠ {taskError}
          </div>
        )}
      </div>
    </div>
  )
}

export default PathTab
