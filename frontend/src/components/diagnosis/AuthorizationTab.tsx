import { useState, useEffect } from 'react'
import {
  getStudentJobs,
  getStudentAuthorizations,
  createStudentAuthorization,
  deleteStudentAuthorization
} from '../../services/api'

interface AuthorizationTabProps {
  student: any
  diagnosisResult: any
}

export default function AuthorizationTab({ student, diagnosisResult }: AuthorizationTabProps) {
  const [jobs, setJobs] = useState<any[]>([])
  const [auths, setAuths] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [actionId, setActionId] = useState<string | null>(null)

  const loadData = async () => {
    setLoading(true)
    try {
      // Fetch available approved jobs
      const jobsData = await getStudentJobs()
      setJobs(jobsData)

      // Fetch student authorizations
      if (student?.id) {
        const authsData = await getStudentAuthorizations(student.id)
        setAuths(authsData)
      }
    } catch (err) {
      console.error('Failed to load authorization data', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [student?.id])

  const handleAuthorize = async (job: any) => {
    if (!student?.id || !diagnosisResult?.id) return
    // 授权前二次确认，明确告知共享范围
    const confirmed = window.confirm(
      `确认将 V${diagnosisResult.version} 版本的能力画像数据授权给「${job.enterprise_name}」的「${job.title}」岗位？\n\n` +
      `共享内容包括：四维能力评分、技能标签、匹配度分析。\n` +
      `注意：后续再诊断不会自动更新此授权数据，需手动重新授权。`
    )
    if (!confirmed) return
    setActionId(job.id)
    try {
      await createStudentAuthorization({
        student_id: student.id,
        job_post_id: job.id,
        diagnosis_id: diagnosisResult.id
      })
      
      // Dispatch event to SalaryCat mascot
      const ev = new CustomEvent('salarycat-message', {
        detail: `恭喜你！当前版本能力画像已成功授权给「${job.enterprise_name}」的「${job.title}」岗位，企业HR稍后即可在工作台查阅您的匹配详情喵~ 😿`
      })
      window.dispatchEvent(ev)
      
      await loadData()
    } catch (err: any) {
      alert(`授权失败: ${err.message || err}`)
    } finally {
      setActionId(null)
    }
  }

  const handleRevoke = async (auth: any) => {
    setActionId(auth.id)
    try {
      await deleteStudentAuthorization(auth.id)

      // Dispatch event to SalaryCat mascot
      const ev = new CustomEvent('salarycat-message', {
        detail: `已成功撤销对「${auth.enterprise_name} - ${auth.job_title}」岗位的画像数据授权。该企业HR将不再能够查阅您的诊断匹配指标喵。`
      })
      window.dispatchEvent(ev)

      await loadData()
    } catch (err: any) {
      alert(`撤销授权失败: ${err.message || err}`)
    } finally {
      setActionId(null)
    }
  }

  if (!diagnosisResult) {
    return (
      <div className="glass-panel" style={{
        padding: 40,
        borderRadius: 16,
        background: 'var(--bg-card)',
        border: '1px solid var(--border-light)',
        textAlign: 'center',
        color: 'var(--text-secondary)'
      }}>
        <span style={{ fontSize: 40, marginBottom: 16, display: 'block' }}>⚠️</span>
        <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>请先完成 AI 职业诊断</h3>
        <p style={{ fontSize: 13, color: 'var(--text-tertiary)', marginTop: 8 }}>
          进行简历上传并完成职业能力测评后，才可以向入驻企业进行双选精准授权。
        </p>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Overview stats */}
      <div className="glass-panel" style={{
        padding: '20px 24px',
        borderRadius: 12,
        background: 'var(--bg-card)',
        border: '1px solid var(--border-light)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: 16
      }}>
        <div>
          <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>当前诊断版本</span>
          <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginTop: 2 }}>
            V{diagnosisResult.version} （目标岗位：{diagnosisResult.top5_jobs?.[0]?.title || student.target_job}）
          </div>
        </div>
        <div>
          <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>核心匹配得分</span>
          <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--accent-blue)', marginTop: 2 }}>
            {Math.round(diagnosisResult.match_score * 100)}分
          </div>
        </div>
        <div>
          <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>已授权岗位数</span>
          <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--accent-teal)', marginTop: 2 }}>
            {auths.filter(a => a.status === 'active').length}个
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: 28 }}>
        {/* Left: Available approved enterprise jobs */}
        <div className="glass-panel" style={{
          padding: 24,
          borderRadius: 16,
          background: 'var(--bg-card)',
          border: '1px solid var(--border-light)',
          display: 'flex',
          flexDirection: 'column',
          gap: 16
        }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, margin: 0 }}>可投递/授权的企业招聘岗位</h3>
          
          {loading ? (
            <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-tertiary)' }}>获取岗位中...</div>
          ) : jobs.length === 0 ? (
            <div style={{ padding: 30, border: '1px dashed var(--border-light)', borderRadius: 10, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>
              🏢 学校双选网络暂无审核通过的企业在招岗位。
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12, maxHeight: '420px', overflowY: 'auto' }}>
              {jobs.map((job) => {
                const currentAuth = auths.find(a => a.job_title === job.title && a.enterprise_name === job.enterprise_name)
                const isAuthActive = currentAuth?.status === 'active'
                
                return (
                  <div key={job.id} style={{
                    border: '1px solid var(--border-light)',
                    borderRadius: 10,
                    padding: 16,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 10,
                    background: isAuthActive ? 'rgba(90, 158, 143, 0.02)' : 'transparent',
                    borderColor: isAuthActive ? 'var(--accent-teal)' : 'var(--border-light)',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div>
                        <div style={{ fontWeight: 600, fontSize: 14 }}>{job.title}</div>
                        <div style={{ fontSize: 12, color: 'var(--accent-teal)', fontWeight: 600, marginTop: 4 }}>
                          🏢 {job.enterprise_name} | {job.category}
                        </div>
                      </div>
                      
                      {isAuthActive ? (
                        <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 8, background: 'rgba(90, 158, 143, 0.15)', color: 'var(--accent-teal)', fontWeight: 600 }}>
                          已授权画像
                        </span>
                      ) : (
                        <button
                          onClick={() => handleAuthorize(job)}
                          disabled={actionId === job.id}
                          className="btn btn-primary"
                          style={{ padding: '6px 12px', fontSize: 12, background: 'var(--accent-blue)' }}
                        >
                          {actionId === job.id ? '授权中...' : '授权画像'}
                        </button>
                      )}
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                      <strong>岗位描述：</strong>{job.description || '暂无描述信息'}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Right: Active Authorizations tracking */}
        <div className="glass-panel" style={{
          padding: 24,
          borderRadius: 16,
          background: 'var(--bg-card)',
          border: '1px solid var(--border-light)',
          display: 'flex',
          flexDirection: 'column',
          gap: 16
        }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, margin: 0 }}>已授权简历与诊断记录</h3>
          
          {loading ? (
            <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-tertiary)' }}>获取记录中...</div>
          ) : auths.length === 0 ? (
            <div style={{ padding: 30, border: '1px dashed var(--border-light)', borderRadius: 10, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>
              😿 您尚未对任何岗位进行数据授权。
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12, maxHeight: '420px', overflowY: 'auto' }}>
              {auths.map((auth) => (
                <div key={auth.id} style={{
                  border: '1px solid var(--border-light)',
                  borderRadius: 10,
                  padding: 14,
                  fontSize: 12
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 600, fontSize: 13 }}>{auth.job_title}</span>
                    <span style={{
                      fontSize: 10,
                      padding: '2px 6px',
                      borderRadius: 6,
                      background: auth.status === 'active' ? 'rgba(90, 158, 143, 0.12)' : 'rgba(128,128,128,0.12)',
                      color: auth.status === 'active' ? 'var(--accent-teal)' : 'var(--text-secondary)'
                    }}>
                      {auth.status === 'active' ? '授权中' : '已撤销'}
                    </span>
                  </div>
                  <div style={{ color: 'var(--text-secondary)', marginTop: 4 }}>意向企业：{auth.enterprise_name}</div>
                  <div style={{ color: 'var(--text-tertiary)', marginTop: 2 }}>绑定画像版本：V{auth.diagnosis_version} (匹配分: {Math.round(auth.match_score * 100)}%)</div>
                  
                  {auth.status === 'active' && (
                    <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 10 }}>
                      <button
                        onClick={() => handleRevoke(auth)}
                        disabled={actionId === auth.id}
                        className="btn btn-ghost"
                        style={{ padding: '3px 8px', fontSize: 11, border: '1px solid var(--accent-rose)', color: 'var(--accent-rose)' }}
                      >
                        {actionId === auth.id ? '撤销中...' : '撤销授权'}
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
