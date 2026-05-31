// 信息输入页——步骤1上传简历→AI解析→步骤2确认补全→提交
import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppStore } from '../stores/appStore'
import { createStudent, updateStudent, listJobs } from '../services/api'
import axios from 'axios'

const API_BASE = '/api'
// 允许上传的文件 MIME 类型
const ALLOWED_TYPES = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']
const MAX_SIZE_MB = 10

async function parseResume(text: string) {
  const res = await axios.post(`${API_BASE}/resume/parse`, { resume_text: text })
  return res.data
}

async function uploadResumeFile(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  const res = await axios.post(`${API_BASE}/resume/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}

const skillLevels = [
  { value: 90, label: '精通 (90)' }, { value: 80, label: '熟练 (80)' },
  { value: 70, label: '良好 (70)' }, { value: 60, label: '了解 (60)' },
  { value: 40, label: '入门 (40)' }, { value: 20, label: '接触过 (20)' },
]

const gradeOptions = ['大一', '大二', '大三', '大四', '研一', '研二', '研三']

// 默认软技能兜底值，解析失败时使用
const DEFAULT_SOFT_SKILLS: Record<string, number> = { '沟通表达': 60, '团队协作': 60, '学习能力': 60 }

interface ParsedData {
  name: string; grade: string; major: string; target_job: string;
  tech_skills: Record<string, number>; soft_skills: Record<string, number>;
  domain_knowledge: Record<string, number>; project_exp: any[];
  summary: string;
}

const initialParsed: ParsedData = {
  name: '', grade: '', major: '', target_job: '',
  tech_skills: {}, soft_skills: {}, domain_knowledge: {}, project_exp: [], summary: '',
}

function humanFileSize(bytes: number) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

export default function ProfileInput() {
  const navigate = useNavigate()
  const { setStudent, setJobs, setDiagnosisResult, student: existingStudent } = useAppStore()
  const [step, setStep] = useState<'upload' | 'review' | 'submitting'>('upload')
  const [resumeText, setResumeText] = useState('')
  const [resumeFile, setResumeFile] = useState<File | null>(null)
  const [fileError, setFileError] = useState('')
  const [parsing, setParsing] = useState(false)
  const [parseError, setParseError] = useState('')
  const [parsed, setParsed] = useState<ParsedData>(initialParsed)
  const [error, setError] = useState('')
  const [jobOptions, setJobOptions] = useState<string[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)
  const newSkillRef = useRef<HTMLInputElement>(null)
  const newSkillLevelRef = useRef<HTMLSelectElement>(null)

  useEffect(() => {
    listJobs()
      .then(jobs => setJobOptions(jobs.map((j: any) => j.title)))
      .catch(() => { console.warn('加载岗位列表失败，使用空列表') })
  }, [])

  useEffect(() => {
    if (existingStudent && step === 'upload') {
      setParsed({
        name: existingStudent.name || '',
        grade: existingStudent.grade || '',
        major: existingStudent.major || '',
        target_job: existingStudent.target_job || '',
        tech_skills: existingStudent.tech_skills || {},
        soft_skills: existingStudent.soft_skills || {},
        domain_knowledge: existingStudent.domain_knowledge || {},
        project_exp: existingStudent.project_exp || [],
        summary: '',
      })
      setResumeText(existingStudent.resume_text || '')
      setStep('review')
    }
  }, [])

  // 文件拖拽/选择处理——校验类型、大小、内容长度
  const handleFileDrop = (files: FileList) => {
    const file = files[0]
    if (!file) return
    setFileError('')

    if (!ALLOWED_TYPES.includes(file.type) && file.type !== '') {
      setFileError('不支持的文件类型，请上传 PDF、DOCX 或 TXT 格式')
      return
    }
    if (file.size > MAX_SIZE_MB * 1048576) {
      setFileError(`文件过大（${humanFileSize(file.size)}），请上传小于 ${MAX_SIZE_MB}MB 的文件`)
      return
    }

    setResumeFile(file)
  }

  // 调用后端 AI 解析简历，失败时使用默认软技能
  const handleParse = async () => {
    if (!resumeText.trim() && !resumeFile) { setParseError('请先上传简历文件或粘贴简历内容'); return }
    setParsing(true)
    setParseError('')
    try {
      let result
      if (resumeFile) {
        result = await uploadResumeFile(resumeFile)
      } else {
        result = await parseResume(resumeText)
      }
      const hasData = result.name || Object.keys(result.tech_skills || {}).length > 0
      if (!hasData) {
        setParseError('未从简历中提取到有效信息，请手动填写或重新上传')
      }
      setParsed({
        ...result,
        soft_skills: Object.keys(result.soft_skills || {}).length > 0
          ? result.soft_skills
          : { ...DEFAULT_SOFT_SKILLS },
      })
      setStep('review')
    } catch (e: any) {
      const msg = e?.response?.data?.detail || e?.response?.data?.error || e?.message || 'AI解析失败'
      setParseError(`${msg}，请手动填写下方信息`)
      setParsed(p => ({ ...p, soft_skills: { ...DEFAULT_SOFT_SKILLS } }))
      setStep('review')
    } finally {
      setParsing(false)
    }
  }

  const handleSkipParse = () => {
    setParsed(p => ({
      ...p,
      soft_skills: { ...DEFAULT_SOFT_SKILLS },
      tech_skills: Object.keys(p.tech_skills).length === 0 ? { 'Python': 60, 'SQL': 50 } : p.tech_skills,
    }))
    setStep('review')
  }

  const updateParsed = (field: keyof ParsedData, value: any) => {
    setParsed(prev => ({ ...prev, [field]: value }))
  }

  // 手动添加技能到列表
  const addSkill = () => {
    const name = newSkillRef.current?.value.trim()
    const level = Number(newSkillLevelRef.current?.value ?? 60)
    if (name) {
      updateParsed('tech_skills', { ...parsed.tech_skills, [name]: level })
      if (newSkillRef.current) newSkillRef.current.value = ''
    }
  }

  // 提交学生信息并跳转到 Dashboard
  const handleSubmit = async () => {
    const name = parsed.name.trim()
    if (!name) { setError('请填写姓名'); return }
    if (!parsed.target_job) { setError('请选择目标岗位'); return }

    setError('')
    setStep('submitting')
    try {
      let student
      if (existingStudent?.id) {
        student = await updateStudent(existingStudent.id, {
          name, grade: parsed.grade, major: parsed.major, target_job: parsed.target_job,
          tech_skills: parsed.tech_skills, soft_skills: parsed.soft_skills,
          domain_knowledge: parsed.domain_knowledge,
          project_exp: parsed.project_exp, resume_text: resumeText,
        })
      } else {
        student = await createStudent({
          name, grade: parsed.grade, major: parsed.major, target_job: parsed.target_job,
          tech_skills: parsed.tech_skills, soft_skills: parsed.soft_skills,
          domain_knowledge: parsed.domain_knowledge,
          project_exp: parsed.project_exp, resume_text: resumeText,
        })
      }
      setStudent(student)
      localStorage.setItem('student_id', student.id)
      const jobs = await listJobs()
      setJobs(jobs)
      setDiagnosisResult(null)
      navigate('/dashboard')
    } catch (e: any) {
      const msg = e?.response?.data?.detail || e?.message || '提交失败，请检查网络连接后重试'
      setError(msg)
      setStep('review')
    }
  }

  // 步骤指示器标签
  const stepLabels = ['上传简历', '确认信息']

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-page)', padding: '32px 24px' }}>
      <div style={{ maxWidth: 720, margin: '0 auto' }}>
        <button className="btn btn-ghost" onClick={() => navigate('/')} style={{ marginBottom: 28, padding: '8px 18px', fontSize: 13 }}>
          ← 返回首页
        </button>

        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 32, fontWeight: 700, marginBottom: 6 }}>
            开启你的成长诊断
          </h2>
          <p style={{ color: 'var(--text-tertiary)', fontSize: 14 }}>上传简历，AI自动解析 → 确认信息 → 一键诊断</p>
        </div>

        <div style={{ display: 'flex', justifyContent: 'center', gap: 60, marginBottom: 28 }}>
          {stepLabels.map((label, i) => {
            const stepKey = i === 0 ? 'upload' : 'review'
            const isActive = step === stepKey || (stepKey === 'review' && step === 'submitting')
            const isDone = step === 'submitting' && stepKey === 'upload'
            const isCurrent = step === stepKey
            return (
              <div key={stepKey} style={{ display: 'flex', alignItems: 'center', gap: 8, opacity: isActive ? 1 : 0.35, transition: 'opacity 0.3s' }}>
                <div style={{
                  width: 28, height: 28, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 13, fontWeight: 700,
                  background: isDone || (stepKey === 'review' && step === 'submitting') ? 'var(--accent-green)' : isCurrent ? 'var(--accent-blue)' : 'var(--border-light)',
                  color: isDone || isCurrent || (stepKey === 'review' && step === 'submitting') ? '#fff' : 'var(--text-tertiary)',
                }}>
                  {isDone || (stepKey === 'upload' && step === 'submitting') ? '✓' : i + 1}
                </div>
                <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-secondary)' }}>{label}</span>
              </div>
            )
          })}
        </div>

        {/* 上传简历步骤——拖拽/粘贴简历文件 */}
        {step === 'upload' && (
          <div className="card" style={{ padding: 36, animation: 'fadeIn 0.4s ease-out' }}>
            <h3 className="section-title">上传简历</h3>

            <div style={{ border: `2px dashed var(--border-light)`, borderRadius: 'var(--radius-lg)', padding: '40px 24px', textAlign: 'center', cursor: 'pointer', background: 'var(--bg-hover)', marginBottom: 20, transition: 'border-color 0.15s, background 0.15s' }}
              onClick={() => fileInputRef.current?.click()}
              onDragOver={e => { e.preventDefault(); e.currentTarget.style.borderColor = 'var(--accent-blue)'; e.currentTarget.style.background = 'rgba(91,123,181,0.03)' }}
              onDragLeave={e => { e.currentTarget.style.borderColor = 'var(--border-light)'; e.currentTarget.style.background = 'var(--bg-hover)' }}
              onDrop={e => { e.preventDefault(); e.currentTarget.style.borderColor = 'var(--border-light)'; e.currentTarget.style.background = 'var(--bg-hover)'; if (e.dataTransfer.files.length) handleFileDrop(e.dataTransfer.files) }}
            >
              <div style={{ fontSize: 36, marginBottom: 10, color: 'var(--text-tertiary)' }}>{resumeFile ? '📄' : '📤'}</div>
              <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 4 }}>
                {resumeFile ? `${resumeFile.name}（${humanFileSize(resumeFile.size)}）` : '拖拽简历文件到此处，或点击选择'}
              </p>
              <p style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>支持 PDF / DOCX / TXT，最大 {MAX_SIZE_MB}MB</p>
              <input ref={fileInputRef} type="file" accept=".pdf,.docx,.txt" style={{ display: 'none' }} onChange={e => { if (e.target.files) handleFileDrop(e.target.files) }} />
            </div>

            {fileError && (
              <div style={{ padding: '10px 14px', borderRadius: 'var(--radius-sm)', background: '#fef2f2', border: '1px solid #fecaca', color: '#dc2626', fontSize: 13, marginBottom: 16, animation: 'slideUp 0.2s ease-out' }}>
                ⚠ {fileError}
              </div>
            )}

            <div className="form-group" style={{ marginBottom: 16 }}>
              <label>或直接粘贴简历文本</label>
              <textarea rows={8} placeholder="请在此粘贴你的简历内容..." maxLength={10000} value={resumeText} onChange={e => setResumeText(e.target.value)} />
              <div style={{ textAlign: 'right', color: 'var(--text-tertiary)', fontSize: 12, marginTop: 4 }}>{resumeText.length} / 10000</div>
            </div>

            {parseError && <div style={{ padding: '10px 14px', borderRadius: 'var(--radius-sm)', background: '#fef2f2', border: '1px solid #fecaca', color: '#dc2626', fontSize: 13, marginBottom: 16 }}>{parseError}</div>}

            <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
              <button className="btn btn-ghost" onClick={handleSkipParse}>跳过解析，手动填写</button>
              <button className="btn btn-primary" onClick={handleParse} disabled={parsing} style={{ opacity: parsing ? 0.6 : 1 }}>
                {parsing ? 'AI 解析中...' : 'AI 解析简历 →'}
              </button>
            </div>
          </div>
        )}

        {/* 确认信息步骤——查看 AI 解析结果并手动调整 */}
        {(step === 'review' || step === 'submitting') && (
          <div className="card" style={{ padding: 36, animation: 'fadeIn 0.4s ease-out' }}>
            {parsed.summary && (
              <div style={{ padding: '12px 16px', borderRadius: 'var(--radius-sm)', background: '#eff6ff', border: '1px solid #dbeafe', marginBottom: 24, fontSize: 13, color: 'var(--accent-blue)', lineHeight: 1.6 }}>
                AI 摘要：{parsed.summary}
              </div>
            )}

            <h3 className="section-title">确认基本信息</h3>
            <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
              <div className="form-group" style={{ flex: 1 }}>
                <label>姓名 *</label>
                <input value={parsed.name} onChange={e => updateParsed('name', e.target.value)} placeholder="你的姓名" />
              </div>
              <div className="form-group" style={{ width: 160 }}>
                <label>年级</label>
                <select value={parsed.grade} onChange={e => updateParsed('grade', e.target.value)}>
                  <option value="">选择年级</option>
                  {gradeOptions.map(g => <option key={g} value={g}>{g}</option>)}
                </select>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
              <div className="form-group" style={{ flex: 1 }}>
                <label>专业</label>
                <input value={parsed.major} onChange={e => updateParsed('major', e.target.value)} placeholder="如：计算机科学与技术" />
              </div>
              <div className="form-group" style={{ flex: 1 }}>
                <label>目标岗位 *</label>
                <select value={parsed.target_job} onChange={e => updateParsed('target_job', e.target.value)}>
                  <option value="">选择岗位</option>
                  {jobOptions.map(j => <option key={j} value={j}>{j}</option>)}
                </select>
              </div>
            </div>

            <h3 className="section-title" style={{ marginTop: 28 }}>技能确认</h3>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              {Object.entries(parsed.tech_skills).length === 0 ? (
                <p style={{ fontSize: 13, color: 'var(--text-tertiary)', width: '100%' }}>未解析到技能，请在下方手动添加</p>
              ) : (
                Object.entries(parsed.tech_skills).map(([skill, score]) => (
                  <div key={skill} style={{ display: 'flex', alignItems: 'flex-end', gap: 4 }}>
                    <div className="form-group" style={{ width: 140 }}>
                      <label>{skill}</label>
                      <select value={score} onChange={e => updateParsed('tech_skills', { ...parsed.tech_skills, [skill]: Number(e.target.value) })}>
                        {skillLevels.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                      </select>
                    </div>
                    <button type="button" onClick={() => { const { [skill]: _, ...rest } = parsed.tech_skills; updateParsed('tech_skills', rest) }} style={{ padding: '8px', border: 'none', background: 'transparent', color: 'var(--text-tertiary)', cursor: 'pointer', fontSize: 14, marginBottom: 1 }}>✕</button>
                  </div>
                ))
              )}
            </div>

            <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
              <input ref={newSkillRef} placeholder="添加技能名" style={{ padding: '8px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-light)', fontSize: 13, width: 140, background: 'var(--bg-card)', color: 'var(--text-primary)' }}
                onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addSkill() } }} />
              <select ref={newSkillLevelRef} style={{ padding: '8px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-light)', fontSize: 13, background: 'var(--bg-card)', color: 'var(--text-primary)' }}>
                {skillLevels.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
              </select>
              <button type="button" className="btn btn-ghost" style={{ padding: '8px 16px', fontSize: 12 }} onClick={addSkill}>
                添加
              </button>
            </div>

            <h3 className="section-title" style={{ marginTop: 28 }}>软技能</h3>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              {Object.entries(parsed.soft_skills).length === 0 ? (
                <p style={{ fontSize: 13, color: 'var(--text-tertiary)', width: '100%' }}>未解析到软技能，已为你设置默认值</p>
              ) : (
                Object.entries(parsed.soft_skills).map(([skill, score]) => (
                  <div key={skill} style={{ display: 'flex', alignItems: 'flex-end', gap: 4 }}>
                    <div className="form-group" style={{ width: 140 }}>
                      <label>{skill}</label>
                      <select value={score} onChange={e => updateParsed('soft_skills', { ...parsed.soft_skills, [skill]: Number(e.target.value) })}>
                        {skillLevels.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                      </select>
                    </div>
                    <button type="button" onClick={() => { const { [skill]: _, ...rest } = parsed.soft_skills; updateParsed('soft_skills', rest) }} style={{ padding: '8px', border: 'none', background: 'transparent', color: 'var(--text-tertiary)', cursor: 'pointer', fontSize: 14, marginBottom: 1 }}>✕</button>
                  </div>
                ))
              )}
            </div>

            <h3 className="section-title" style={{ marginTop: 28 }}>项目经历</h3>
            {(parsed.project_exp || []).length === 0 ? (
              <p style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>未解析到项目经历</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {(parsed.project_exp || []).map((proj: any, i: number) => (
                  <div key={i} style={{ padding: '12px 16px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-light)', background: 'var(--bg-hover)' }}>
                    <div style={{ display: 'flex', gap: 12, marginBottom: 6 }}>
                      <input value={proj.name || ''} onChange={e => { const exp = [...parsed.project_exp]; exp[i] = { ...exp[i], name: e.target.value }; updateParsed('project_exp', exp) }} placeholder="项目名称" style={{ flex: 1, padding: '8px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-light)', fontSize: 13, background: 'var(--bg-card)', color: 'var(--text-primary)' }} />
                      <input value={proj.role || ''} onChange={e => { const exp = [...parsed.project_exp]; exp[i] = { ...exp[i], role: e.target.value }; updateParsed('project_exp', exp) }} placeholder="角色" style={{ width: 120, padding: '8px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-light)', fontSize: 13, background: 'var(--bg-card)', color: 'var(--text-primary)' }} />
                    </div>
                    <textarea value={proj.description || ''} onChange={e => { const exp = [...parsed.project_exp]; exp[i] = { ...exp[i], description: e.target.value }; updateParsed('project_exp', exp) }} placeholder="项目描述" rows={2} style={{ width: '100%', padding: '8px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-light)', fontSize: 13, background: 'var(--bg-card)', color: 'var(--text-primary)', resize: 'vertical' }} />
                  </div>
                ))}
              </div>
            )}

            <h3 className="section-title" style={{ marginTop: 28 }}>领域知识</h3>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              {Object.entries(parsed.domain_knowledge).length === 0 ? (
                <p style={{ fontSize: 13, color: 'var(--text-tertiary)', width: '100%' }}>未解析到领域知识</p>
              ) : (
                Object.entries(parsed.domain_knowledge).map(([domain, score]) => (
                  <div key={domain} className="form-group" style={{ width: 160 }}>
                    <label>{domain}</label>
                    <select value={score} onChange={e => updateParsed('domain_knowledge', { ...parsed.domain_knowledge, [domain]: Number(e.target.value) })}>
                      {skillLevels.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                    </select>
                  </div>
                ))
              )}
            </div>

            {error && <div style={{ marginTop: 20, padding: '10px 14px', borderRadius: 'var(--radius-sm)', background: '#fef2f2', border: '1px solid #fecaca', color: '#dc2626', fontSize: 13, animation: 'slideUp 0.2s ease-out' }}>{error}</div>}

            <div style={{ display: 'flex', gap: 12, justifyContent: 'space-between', marginTop: 32 }}>
              <button className="btn btn-ghost" onClick={() => setStep('upload')}>← 重新上传</button>
              <button className="btn btn-primary btn-lg" onClick={handleSubmit} disabled={step === 'submitting'}
                style={{ opacity: step === 'submitting' ? 0.6 : 1, cursor: step === 'submitting' ? 'not-allowed' : 'pointer' }}>
                {step === 'submitting' ? '提交中...' : '确认并开始诊断'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
