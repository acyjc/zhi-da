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
  theme: 'light' | 'dark'
  role: 'student' | 'enterprise' | 'admin' | null
  currentStudentId: string | number
  currentEnterpriseId: string
  setStudent: (student: Student | null) => void
  setJobs: (jobs: Job[]) => void
  setDiagnosisResult: (result: DiagnosisResult | null) => void
  setDiagnosisHistory: (history: DiagnosisResult[]) => void
  setIsLoading: (loading: boolean) => void
  setProgress: (progress: { stage: string; progress: number; message: string }) => void
  setTriggeredReEvaluate: (triggered: boolean) => void
  setTheme: (theme: 'light' | 'dark') => void
  setRole: (role: 'student' | 'enterprise' | 'admin' | null) => void
  setCurrentStudentId: (id: string | number) => void
  setCurrentEnterpriseId: (id: string) => void
  logout: () => void
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
  theme: 'light',
  role: null,
  currentStudentId: '',
  currentEnterpriseId: '',
  setStudent: (student) => {
    if (student) {
      localStorage.setItem('student_id', String(student.id))
      localStorage.setItem('zhida_student_id', String(student.id))
      localStorage.setItem('student_data', JSON.stringify(student))
      set({ student, currentStudentId: student.id })
    } else {
      localStorage.removeItem('student_id')
      localStorage.removeItem('zhida_student_id')
      localStorage.removeItem('student_data')
      set({ student, currentStudentId: '' })
    }
  },
  setJobs: (jobs) => set({ jobs }),
  setDiagnosisResult: (result) => set({ diagnosisResult: result }),
  setDiagnosisHistory: (history) => set({ diagnosisHistory: history }),
  setIsLoading: (loading) => set({ isLoading: loading }),
  setProgress: (progress) => set({ progress }),
  setTriggeredReEvaluate: (triggered) => set({ triggeredReEvaluate: triggered }),
  setTheme: (theme) => {
    localStorage.setItem('theme', theme)
    document.documentElement.classList.toggle('dark', theme === 'dark')
    document.body.classList.toggle('dark', theme === 'dark')
    set({ theme })
  },
  setRole: (role) => {
    if (role) {
      localStorage.setItem('zhida_role', role)
    } else {
      localStorage.removeItem('zhida_role')
    }
    set({ role })
  },
  setCurrentStudentId: (id) => {
    localStorage.setItem('zhida_student_id', String(id))
    localStorage.setItem('student_id', String(id))
    set({ currentStudentId: id })
  },
  setCurrentEnterpriseId: (id) => {
    localStorage.setItem('zhida_enterprise_id', id)
    set({ currentEnterpriseId: id })
  },
  logout: () => {
    localStorage.removeItem('zhida_token')
    localStorage.removeItem('zhida_role')
    localStorage.removeItem('zhida_student_id')
    localStorage.removeItem('zhida_enterprise_id')
    localStorage.removeItem('zhida_admin_account')
    localStorage.removeItem('student_id')
    localStorage.removeItem('student_data')
    localStorage.removeItem('mock_role')
    localStorage.removeItem('mock_student_id')
    localStorage.removeItem('mock_enterprise_id')
    set({ role: null, currentStudentId: '', currentEnterpriseId: '' })
  },
  hydrateFromStorage: () => {
    // Restore theme
    const storedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null
    if (storedTheme) {
      document.documentElement.classList.toggle('dark', storedTheme === 'dark')
      document.body.classList.toggle('dark', storedTheme === 'dark')
      set({ theme: storedTheme })
    } else {
      set({ theme: 'light' })
    }
    // Restore student
    const stored = localStorage.getItem('student_data')
    if (stored && !get().student) {
      try {
        const student = JSON.parse(stored)
        set({ student })
      } catch {
        localStorage.removeItem('student_data')
      }
    }
    // Restore role and IDs (no legacy mock_* fallback).
    const storedRole = localStorage.getItem('zhida_role') as 'student' | 'enterprise' | 'admin' | null
    if (storedRole) {
      set({ role: storedRole })
    }
    const storedStudentId = localStorage.getItem('zhida_student_id') || localStorage.getItem('student_id')
    if (storedStudentId) {
      set({ currentStudentId: storedStudentId })
    } else if (get().student) {
      set({ currentStudentId: get().student!.id })
    }
    const storedEnterpriseId = localStorage.getItem('zhida_enterprise_id')
    if (storedEnterpriseId) {
      set({ currentEnterpriseId: storedEnterpriseId })
    }
  },
}))
