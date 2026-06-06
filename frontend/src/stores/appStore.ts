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
  role: 'student' | 'enterprise' | 'admin'
  mockStudentId: string
  mockEnterpriseId: string
  setStudent: (student: Student | null) => void
  setJobs: (jobs: Job[]) => void
  setDiagnosisResult: (result: DiagnosisResult | null) => void
  setDiagnosisHistory: (history: DiagnosisResult[]) => void
  setIsLoading: (loading: boolean) => void
  setProgress: (progress: { stage: string; progress: number; message: string }) => void
  setTriggeredReEvaluate: (triggered: boolean) => void
  setTheme: (theme: 'light' | 'dark') => void
  setRole: (role: 'student' | 'enterprise' | 'admin') => void
  setMockStudentId: (id: string) => void
  setMockEnterpriseId: (id: string) => void
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
  role: 'student',
  mockStudentId: '1',
  mockEnterpriseId: '1',
  setStudent: (student) => {
    if (student) {
      localStorage.setItem('student_id', student.id)
      localStorage.setItem('student_data', JSON.stringify(student))
      // Align mockStudentId when student changes
      localStorage.setItem('mock_student_id', student.id)
      set({ student, mockStudentId: student.id })
    } else {
      localStorage.removeItem('student_id')
      localStorage.removeItem('student_data')
      set({ student })
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
    localStorage.setItem('mock_role', role)
    set({ role })
  },
  setMockStudentId: (id) => {
    localStorage.setItem('mock_student_id', id)
    set({ mockStudentId: id })
  },
  setMockEnterpriseId: (id) => {
    localStorage.setItem('mock_enterprise_id', id)
    set({ mockEnterpriseId: id })
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
    // Restore role & mock IDs
    const storedRole = localStorage.getItem('mock_role') as 'student' | 'enterprise' | 'admin' | null
    if (storedRole) {
      set({ role: storedRole })
    }
    const storedStudentId = localStorage.getItem('mock_student_id')
    if (storedStudentId) {
      set({ mockStudentId: storedStudentId })
    } else if (get().student) {
      set({ mockStudentId: get().student!.id })
    }
    const storedEnterpriseId = localStorage.getItem('mock_enterprise_id')
    if (storedEnterpriseId) {
      set({ mockEnterpriseId: storedEnterpriseId })
    }
  },
}))
