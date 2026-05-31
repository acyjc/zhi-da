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
  const reader = response.body?.getReader()
  if (!reader) throw new Error('No response body')
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
          } else if (onProgress) {
            onProgress(data.stage, data.progress, data.message)
          }
        } catch {
        }
      }
    }
  }
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
