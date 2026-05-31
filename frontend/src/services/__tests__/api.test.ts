import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('axios', () => ({
  default: {
    create: () => ({
      post: vi.fn(),
      get: vi.fn(),
      put: vi.fn(),
    }),
  },
}))

describe('API service layer', () => {
  it('exports expected API functions', async () => {
    const api = await import('../api')
    expect(typeof api.createStudent).toBe('function')
    expect(typeof api.getStudent).toBe('function')
    expect(typeof api.updateSkills).toBe('function')
    expect(typeof api.listJobs).toBe('function')
    expect(typeof api.startDiagnosis).toBe('function')
    expect(typeof api.reEvaluate).toBe('function')
    expect(typeof api.completeTask).toBe('function')
    expect(typeof api.getProgress).toBe('function')
    expect(typeof api.getDiagnosisHistory).toBe('function')
  })
})
