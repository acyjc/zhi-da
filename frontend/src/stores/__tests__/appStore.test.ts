import { describe, it, expect, beforeEach } from 'vitest'
import { useAppStore } from '../appStore'

describe('appStore', () => {
  beforeEach(() => {
    useAppStore.setState({
      student: null,
      jobs: [],
      diagnosisResult: null,
      diagnosisHistory: [],
      isLoading: false,
      progress: { stage: '', progress: 0, message: '' },
      triggeredReEvaluate: false,
    })
    localStorage.clear()
  })

  it('sets student and persists to localStorage', () => {
    const student = { id: 1001, name: '张三', grade: '大三', major: 'CS', target_job: '前端', tech_skills: {}, project_exp: [], soft_skills: {}, domain_knowledge: {}, resume_text: '' } as any
    useAppStore.getState().setStudent(student)
    expect(useAppStore.getState().student).toEqual(student)
    expect(localStorage.getItem('student_id')).toBe('1001')
    expect(JSON.parse(localStorage.getItem('student_data') || '{}').name).toBe('张三')
  })

  it('clears localStorage when student is set to null', () => {
    useAppStore.getState().setStudent(null)
    expect(localStorage.getItem('student_id')).toBeNull()
  })

  it('hydrates student from localStorage', () => {
    const student = { id: 1002, name: '李四', grade: '大四', major: 'SE', target_job: '后端', tech_skills: {}, project_exp: [], soft_skills: {}, domain_knowledge: {}, resume_text: '' } as any
    localStorage.setItem('student_data', JSON.stringify(student))
    useAppStore.getState().hydrateFromStorage()
    expect(useAppStore.getState().student).toEqual(student)
  })

  it('sets diagnosis result correctly', () => {
    const diag = { id: 'd1', student_id: 2001, version: 1, diagnosis_type: 'full', match_score: 0.75, dimension_scores: {}, dimension_changes: {}, gap_details: [], top5_jobs: [], growth_path: { phases: [] }, career_advice: '', ai_reasoning: {}, trigger_event: '', created_at: '' } as any
    useAppStore.getState().setDiagnosisResult(diag)
    expect(useAppStore.getState().diagnosisResult).toEqual(diag)
  })

  it('sets loading and progress state', () => {
    useAppStore.getState().setIsLoading(true)
    expect(useAppStore.getState().isLoading).toBe(true)
    useAppStore.getState().setProgress({ stage: '分析中', progress: 50, message: '正在匹配岗位' })
    expect(useAppStore.getState().progress.stage).toBe('分析中')
  })
})
