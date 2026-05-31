import { create } from 'zustand'
import type { Student, Job, DiagnosisResult } from '../types'

interface AppState {
  student: Student | null
  jobs: Job[]
  diagnosisResult: DiagnosisResult | null
  diagnosisHistory: DiagnosisResult[]
  isLoading: boolean
  progress: { stage: string; progress: number; message: string }
  triggeredReEvaluate: boolean
  setStudent: (student: Student | null) => void
  setJobs: (jobs: Job[]) => void
  setDiagnosisResult: (result: DiagnosisResult | null) => void
  setDiagnosisHistory: (history: DiagnosisResult[]) => void
  setIsLoading: (loading: boolean) => void
  setProgress: (progress: { stage: string; progress: number; message: string }) => void
  setTriggeredReEvaluate: (triggered: boolean) => void
  hydrateFromStorage: () => void
}

export const useAppStore = create<AppState>((set, get) => ({
  student: null,
  jobs: [],
  diagnosisResult: null,
  diagnosisHistory: [],
  isLoading: false,
  progress: { stage: '', progress: 0, message: '' },
  triggeredReEvaluate: false,
  setStudent: (student) => {
    if (student) {
      localStorage.setItem('student_id', student.id)
      localStorage.setItem('student_data', JSON.stringify(student))
    } else {
      localStorage.removeItem('student_id')
      localStorage.removeItem('student_data')
    }
    set({ student })
  },
  setJobs: (jobs) => set({ jobs }),
  setDiagnosisResult: (result) => set({ diagnosisResult: result }),
  setDiagnosisHistory: (history) => set({ diagnosisHistory: history }),
  setIsLoading: (loading) => set({ isLoading: loading }),
  setProgress: (progress) => set({ progress }),
  setTriggeredReEvaluate: (triggered) => set({ triggeredReEvaluate: triggered }),
  hydrateFromStorage: () => {
    const stored = localStorage.getItem('student_data')
    if (stored && !get().student) {
      try {
        const student = JSON.parse(stored)
        set({ student })
      } catch {
        localStorage.removeItem('student_data')
      }
    }
  },
}))
