// 诊断流程 Hook——封装 SSE 交互逻辑，管理 idle→loading→done→error 状态流转
import { useState, useCallback } from 'react'
import { useAppStore } from '../stores/appStore'
import { startDiagnosis, getDiagnosisHistory } from '../services/api'

export function useDiagnosis() {
  const { student, setDiagnosisResult, setDiagnosisHistory, setIsLoading, setProgress } = useAppStore()
  const [error, setError] = useState<string | null>(null)
  const [stage, setStage] = useState<'idle' | 'loading' | 'done' | 'error'>('idle')

  const runDiagnosis = useCallback(async () => {
    if (!student) return
    setStage('loading')
    setIsLoading(true)
    setError(null)
    try {
      const result = await startDiagnosis(student.id, (s, p, m) => {
        setProgress({ stage: s, progress: p, message: m })
      })
      if (result) {
        setDiagnosisResult(result)
        const history = await getDiagnosisHistory(student.id)
        setDiagnosisHistory(history)
        setStage('done')
      }
    } catch (e: any) {
      setError(e.message || '诊断失败')
      setStage('error')
    } finally {
      setIsLoading(false)
    }
  }, [student, setDiagnosisResult, setDiagnosisHistory, setIsLoading, setProgress])

  return { runDiagnosis, stage, error, retry: runDiagnosis }
}
