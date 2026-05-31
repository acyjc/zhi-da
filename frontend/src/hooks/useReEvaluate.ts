// 再评估 Hook——封装再诊断 SSE 交互，控制提示弹窗显隐
import { useState, useCallback } from 'react'
import { useAppStore } from '../stores/appStore'
import { reEvaluate, getDiagnosisHistory } from '../services/api'

export function useReEvaluate() {
  const { student, setDiagnosisResult, setDiagnosisHistory, setIsLoading, setProgress } = useAppStore()
  const [showPrompt, setShowPrompt] = useState(false)
  const [promptMessage, setPromptMessage] = useState('')

  const triggerReEvaluate = useCallback(async (triggerEvent: string) => {
    if (!student) return
    setIsLoading(true)
    setShowPrompt(false)
    try {
      const result = await reEvaluate(student.id, triggerEvent, (s, p, m) => {
        setProgress({ stage: s, progress: p, message: m })
      })
      if (result) {
        setDiagnosisResult(result)
        const history = await getDiagnosisHistory(student.id)
        setDiagnosisHistory(history)
      }
    } finally {
      setIsLoading(false)
    }
  }, [student, setDiagnosisResult, setDiagnosisHistory, setIsLoading, setProgress])

  const showReEvaluatePrompt = useCallback((message: string) => {
    setPromptMessage(message)
    setShowPrompt(true)
  }, [])

  return { triggerReEvaluate, showReEvaluatePrompt, showPrompt, setShowPrompt, promptMessage }
}
