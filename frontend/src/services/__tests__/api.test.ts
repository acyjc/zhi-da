import { describe, it, expect, vi } from 'vitest'

vi.mock('axios', () => ({
  default: {
    create: () => ({
      post: vi.fn(),
      get: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() },
      },
    }),
  },
}))

describe('API service layer', () => {
  it('exports expected core API functions', async () => {
    const api = await import('../api')
    // Core CRUD
    expect(typeof api.createStudent).toBe('function')
    expect(typeof api.getStudent).toBe('function')
    expect(typeof api.updateStudent).toBe('function')
    expect(typeof api.updateSkills).toBe('function')
    expect(typeof api.listJobs).toBe('function')
    expect(typeof api.getDiagnosisHistory).toBe('function')
    expect(typeof api.getHealthStatus).toBe('function')
  })

  it('exports student extension and enterprise API functions', async () => {
    const api = await import('../api')
    // Student extension
    expect(typeof api.getStudentJobs).toBe('function')
    expect(typeof api.getStudentAuthorizations).toBe('function')
    expect(typeof api.createStudentAuthorization).toBe('function')
    expect(typeof api.deleteStudentAuthorization).toBe('function')
    // Enterprise
    expect(typeof api.getEnterpriseProfile).toBe('function')
    expect(typeof api.getEnterpriseJobs).toBe('function')
    expect(typeof api.getEnterpriseCandidates).toBe('function')
  })

  it('exports admin API functions', async () => {
    const api = await import('../api')
    expect(typeof api.getAdminSummary).toBe('function')
    expect(typeof api.listAdminStudents).toBe('function')
    expect(typeof api.listAdminEnterprises).toBe('function')
    expect(typeof api.listAdminJobs).toBe('function')
  })

  it('exports growth tasks API functions', async () => {
    const api = await import('../api')
    expect(typeof api.getGrowthTasks).toBe('function')
    expect(typeof api.submitTaskEvidence).toBe('function')
    expect(typeof api.getGrowthTaskDetail).toBe('function')
    expect(typeof api.linkTaskReEvaluation).toBe('function')
  })

  it('exports unified Agent API functions', async () => {
    const api = await import('../api')
    expect(typeof api.runStudentAgent).toBe('function')
    expect(typeof api.runStudentAgentStream).toBe('function')
  })

  it('exports auth API functions', async () => {
    const api = await import('../api')
    expect(typeof api.login).toBe('function')
    expect(typeof api.logout).toBe('function')
    expect(typeof api.getAuthToken).toBe('function')
    expect(typeof api.setAuthToken).toBe('function')
    expect(typeof api.clearAuth).toBe('function')
    expect(typeof api.listEnterprisesForLogin).toBe('function')
  })

  it('does NOT export deprecated functions', async () => {
    const api = await import('../api') as Record<string, unknown>
    // These were removed in Phase 2 Convergence cleanup
    expect(api.startDiagnosis).toBeUndefined()
    expect(api.reEvaluate).toBeUndefined()
    expect(api.agentDiagnose).toBeUndefined()
    expect(api.agentAsk).toBeUndefined()
    expect(api.agentPlan).toBeUndefined()
    expect(api.agentReviewTask).toBeUndefined()
    expect(api.readSSE).toBeUndefined()
    // Removed in Phase 3: legacy progress API
    expect(api.completeTask).toBeUndefined()
    expect(api.getProgress).toBeUndefined()
  })
})
