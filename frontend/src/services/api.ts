import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
})

export async function createStudent(data: {
  name: string; grade?: string; major?: string; target_job?: string;
  tech_skills?: Record<string, number>; project_exp?: any[];
  soft_skills?: Record<string, number>; domain_knowledge?: Record<string, number>;
  resume_text?: string;
}) {
  const res = await api.post('/students', data)
  return res.data
}

export async function getStudent(id: string) {
  const res = await api.get(`/students/${id}`)
  return res.data
}

export async function updateStudent(id: string, data: {
  name?: string; grade?: string; major?: string; target_job?: string;
  tech_skills?: Record<string, number>; project_exp?: any[];
  soft_skills?: Record<string, number>; domain_knowledge?: Record<string, number>;
  resume_text?: string;
}) {
  const res = await api.put(`/students/${id}`, data)
  return res.data
}

export async function updateSkills(studentId: string, data: {
  tech_skills?: Record<string, number>
  soft_skills?: Record<string, number>
  domain_knowledge?: Record<string, number>
  project_exp?: any[]
}) {
  const res = await api.put(`/students/${studentId}/skills`, data)
  return res.data
}

export async function listJobs() {
  const res = await api.get('/jobs')
  return res.data
}

async function readSSE(
  url: string,
  body: Record<string, any>,
  onProgress?: (stage: string, progress: number, message: string) => void,
): Promise<any> {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`
    try {
      const errData = await response.json()
      if (errData.detail) detail = errData.detail
      else if (errData.error) detail = errData.error
    } catch {}
    throw new Error(detail)
  }
  const reader = response.body?.getReader()
  if (!reader) throw new Error('服务器未返回数据流')
  const decoder = new TextDecoder()
  let buffer = ''
  let result: any = null
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6))
          if (data.stage === 'result') {
            result = data
          } else if (data.error) {
            throw new Error(data.error)
          } else if (onProgress) {
            onProgress(data.stage, data.progress, data.message)
          }
        } catch (e: any) {
          if (e.message && !e.message.startsWith('Unexpected')) throw e
        }
      }
    }
  }
  if (!result) throw new Error('诊断未返回结果，请确认后端服务是否正常运行')
  return result
}

export async function startDiagnosis(studentId: string, onProgress?: (stage: string, progress: number, message: string) => void) {
  return readSSE('/api/diagnosis/full', { student_id: studentId, mode: 'full' }, onProgress)
}

export async function getDiagnosisHistory(studentId: string) {
  const res = await api.get(`/diagnosis/history/${studentId}`)
  return res.data
}

export async function completeTask(data: { student_id: string; task_id: string; evidence: string }) {
  const res = await api.post('/progress/task-complete', data)
  return res.data
}

export async function getProgress(studentId: string) {
  const res = await api.get(`/progress/${studentId}`)
  return res.data
}

export async function reEvaluate(studentId: string, triggerEvent: string, onProgress?: (stage: string, progress: number, message: string) => void) {
  return readSSE('/api/diagnosis/re-evaluate', { student_id: studentId, trigger_event: triggerEvent }, onProgress)
}

export async function getHealthStatus() {
  const res = await api.get('/health')
  return res.data
}

// ==========================================
// 1. 学生端扩展 API (Student Extension APIs)
// ==========================================
export async function getStudentJobs() {
  const res = await api.get('/student/jobs')
  return res.data
}

export async function getStudentAuthorizations(studentId: string) {
  const res = await api.get('/student/authorizations', { params: { student_id: studentId } })
  return res.data
}

export async function createStudentAuthorization(data: { student_id: string; job_post_id: string; diagnosis_id: string }) {
  const res = await api.post('/student/authorizations', data)
  return res.data
}

export async function deleteStudentAuthorization(authId: string) {
  const res = await api.delete(`/student/authorizations/${authId}`)
  return res.data
}

// ==========================================
// 2. 企业端 API (Enterprise APIs)
// ==========================================
export async function getEnterpriseProfile(enterpriseId: string) {
  const res = await api.get('/enterprise/profile', { params: { enterprise_id: enterpriseId } })
  return res.data
}

export async function updateEnterpriseProfile(enterpriseId: string, data: {
  name: string; industry?: string; description?: string; contact_name?: string; contact_email?: string;
}) {
  const res = await api.put('/enterprise/profile', data, { params: { enterprise_id: enterpriseId } })
  return res.data
}

export async function getEnterpriseJobs(enterpriseId: string) {
  const res = await api.get('/enterprise/jobs', { params: { enterprise_id: enterpriseId } })
  return res.data
}

export async function createEnterpriseJob(enterpriseId: string, data: {
  title: string; category?: string; description?: string; requirements_text?: string; status?: string;
}) {
  const res = await api.post('/enterprise/jobs', data, { params: { enterprise_id: enterpriseId } })
  return res.data
}

export async function getEnterpriseJobDetail(jobId: string, enterpriseId: string) {
  const res = await api.get(`/enterprise/jobs/${jobId}`, { params: { enterprise_id: enterpriseId } })
  return res.data
}

export async function updateEnterpriseJob(jobId: string, enterpriseId: string, data: {
  title: string; category?: string; description?: string; requirements_text?: string; status?: string;
}) {
  const res = await api.put(`/enterprise/jobs/${jobId}`, data, { params: { enterprise_id: enterpriseId } })
  return res.data
}

export async function parseJobAbilityModel(jobId: string, enterpriseId: string) {
  const res = await api.post(`/enterprise/jobs/${jobId}/parse-ability`, {}, { params: { enterprise_id: enterpriseId } })
  return res.data
}

export async function submitJobReview(jobId: string, enterpriseId: string) {
  const res = await api.post(`/enterprise/jobs/${jobId}/submit-review`, {}, { params: { enterprise_id: enterpriseId } })
  return res.data
}

export async function getEnterpriseCandidates(enterpriseId: string) {
  const res = await api.get('/enterprise/candidates', { params: { enterprise_id: enterpriseId } })
  return res.data
}

export async function getEnterpriseCandidateDetail(studentId: string, authId: string, enterpriseId: string) {
  const res = await api.get(`/enterprise/candidates/${studentId}`, { params: { auth_id: authId, enterprise_id: enterpriseId } })
  return res.data
}

// ==========================================
// 3. 学校端/管理员 API (School Admin APIs)
// ==========================================
export async function getAdminSummary() {
  const res = await api.get('/admin/summary')
  return res.data
}

export async function listAdminStudents() {
  const res = await api.get('/admin/students')
  return res.data
}

export async function getAdminStudentDetail(studentId: string) {
  const res = await api.get(`/admin/students/${studentId}`)
  return res.data
}

export async function listAdminEnterprises() {
  const res = await api.get('/admin/enterprises')
  return res.data
}

export async function getAdminEnterpriseDetail(enterpriseId: string) {
  const res = await api.get(`/admin/enterprises/${enterpriseId}`)
  return res.data
}

export async function updateAdminEnterpriseStatus(enterpriseId: string, status: string) {
  const res = await api.put(`/admin/enterprises/${enterpriseId}/status`, { status })
  return res.data
}

export async function listAdminJobs(status?: string) {
  const res = await api.get('/admin/jobs', { params: status ? { status } : {} })
  return res.data
}

export async function getAdminJobDetail(jobId: string) {
  const res = await api.get(`/admin/jobs/${jobId}`)
  return res.data
}

export async function approveAdminJob(jobId: string) {
  const res = await api.post(`/admin/jobs/${jobId}/approve`)
  return res.data
}

export async function rejectAdminJob(jobId: string, reason: string) {
  const res = await api.post(`/admin/jobs/${jobId}/reject`, { reason })
  return res.data
}
