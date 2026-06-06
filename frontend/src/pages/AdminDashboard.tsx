import { useState, useEffect } from 'react'
import { useAppStore } from '../stores/appStore'
import {
  getAdminSummary,
  listAdminStudents,
  getAdminStudentDetail,
  listAdminEnterprises,
  updateAdminEnterpriseStatus,
  listAdminJobs,
  approveAdminJob,
  rejectAdminJob,
  getAdminJobDetail
} from '../services/api'
import ReactECharts from 'echarts-for-react'
import { BarChart3, GraduationCap, Building2, ShieldCheck } from 'lucide-react'

export default function AdminDashboard() {
  const { theme } = useAppStore()
  const [activeTab, setActiveTab] = useState<'stats' | 'students' | 'enterprises' | 'jobs'>('stats')

  const isDark = theme === 'dark'

  // Stats states
  const [summary, setSummary] = useState<any>(null)
  const [statsLoading, setStatsLoading] = useState(false)

  // Students states
  const [students, setStudents] = useState<any[]>([])
  const [studentsLoading, setStudentsLoading] = useState(false)
  const [selectedStudent, setSelectedStudent] = useState<any | null>(null)
  const [studentDetailLoading, setStudentDetailLoading] = useState(false)
  const [showStudentModal, setShowStudentModal] = useState(false)

  // Enterprises states
  const [enterprises, setEnterprises] = useState<any[]>([])
  const [enterprisesLoading, setEnterprisesLoading] = useState(false)
  const [updatingEntId, setUpdatingEntId] = useState<string | null>(null)

  // Jobs audit states
  const [jobs, setJobs] = useState<any[]>([])
  const [jobsLoading, setJobsLoading] = useState(false)
  const [selectedJob, setSelectedJob] = useState<any | null>(null)
  const [selectedJobModel, setSelectedJobModel] = useState<any | null>(null)
  const [auditLoading, setAuditLoading] = useState(false)
  const [auditFilter, setAuditFilter] = useState<string>('pending_review')

  // Reject modal states
  const [showRejectModal, setShowRejectModal] = useState(false)
  const [rejectReason, setRejectReason] = useState('')
  const [rejectJobId, setRejectJobId] = useState('')

  // Load summary stats
  const loadSummary = async () => {
    setStatsLoading(true)
    try {
      const data = await getAdminSummary()
      setSummary(data)
    } catch (err) {
      console.error('Failed to load summary', err)
    } finally {
      setStatsLoading(false)
    }
  }

  // Load students list
  const loadStudents = async () => {
    setStudentsLoading(true)
    try {
      const data = await listAdminStudents()
      setStudents(data)
    } catch (err) {
      console.error('Failed to load students', err)
    } finally {
      setStudentsLoading(false)
    }
  }

  // Load enterprises list
  const loadEnterprises = async () => {
    setEnterprisesLoading(true)
    try {
      const data = await listAdminEnterprises()
      setEnterprises(data)
    } catch (err) {
      console.error('Failed to load enterprises', err)
    } finally {
      setEnterprisesLoading(false)
    }
  }

  // Load jobs audit list
  const loadJobs = async (filter?: string) => {
    setJobsLoading(true)
    try {
      const data = await listAdminJobs(filter || auditFilter)
      setJobs(data)
      if (data.length > 0) {
        handleSelectJob(data[0])
      } else {
        setSelectedJob(null)
        setSelectedJobModel(null)
      }
    } catch (err) {
      console.error('Failed to load jobs', err)
    } finally {
      setJobsLoading(false)
    }
  }

  // Effect to load data based on active tab
  useEffect(() => {
    if (activeTab === 'stats') {
      loadSummary()
    } else if (activeTab === 'students') {
      loadStudents()
    } else if (activeTab === 'enterprises') {
      loadEnterprises()
    } else if (activeTab === 'jobs') {
      loadJobs(auditFilter)
    }
  }, [activeTab, auditFilter])

  // Select job and load detail/ability model
  const handleSelectJob = async (job: any) => {
    setSelectedJob(job)
    try {
      const fetchDetail = await getAdminJobDetail(job.id)
      setSelectedJobModel(fetchDetail.ability_model)
    } catch (err) {
      console.error('Failed to load job model', err)
      setSelectedJobModel(null)
    }
  }

  // Student detail viewing
  const handleViewStudent = async (studentId: string) => {
    setStudentDetailLoading(true)
    try {
      const detail = await getAdminStudentDetail(studentId)
      setSelectedStudent(detail)
      setShowStudentModal(true)
    } catch (err) {
      alert('获取学生详细档案失败')
    } finally {
      setStudentDetailLoading(false)
    }
  }

  // Toggle Enterprise Status
  const handleToggleEnterpriseStatus = async (entId: string, currentStatus: string) => {
    setUpdatingEntId(entId)
    const nextStatus = currentStatus === 'active' ? 'disabled' : 'active'
    try {
      await updateAdminEnterpriseStatus(entId, nextStatus)
      setEnterprises(prev => prev.map(e => e.id === entId ? { ...e, status: nextStatus } : e))
    } catch (err) {
      alert('修改企业状态失败')
    } finally {
      setUpdatingEntId(null)
    }
  }

  // Approve Job
  const handleApproveJob = async (jobId: string) => {
    setAuditLoading(true)
    try {
      await approveAdminJob(jobId)
      alert('岗位审核通过！学生端现可选择此岗位进行诊断匹配。')
      loadJobs()
    } catch (err) {
      alert('岗位审批操作失败')
    } finally {
      setAuditLoading(false)
    }
  }

  // Open reject dialog
  const handleStartRejectJob = (jobId: string) => {
    setRejectJobId(jobId)
    setRejectReason('')
    setShowRejectModal(true)
  }

  // Confirm Reject
  const handleConfirmReject = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!rejectReason.trim()) return
    setAuditLoading(true)
    setShowRejectModal(false)
    try {
      await rejectAdminJob(rejectJobId, rejectReason)
      alert('岗位已驳回，请通过其他方式通知企业修改。')
      loadJobs()
    } catch (err) {
      alert('岗位驳回操作失败')
    } finally {
      setAuditLoading(false)
    }
  }

  // ECharts line options for Student Diagnostic Score history
  const getStudentGrowthOption = () => {
    if (!selectedStudent || selectedStudent.diagnoses.length === 0) return {}

    const diags = [...selectedStudent.diagnoses].reverse() // show crono order

    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => `版本: ${params[0].name}<br/>匹配度分数: <b>${params[0].value}%</b>`,
        backgroundColor: isDark ? 'rgba(22, 24, 29, 0.95)' : 'rgba(248, 247, 244, 0.95)',
        borderColor: isDark ? '#2c2f3a' : '#e8e5df',
        textStyle: { color: isDark ? '#f5f6f9' : '#1d1d1f' }
      },
      xAxis: {
        type: 'category',
        data: diags.map(d => `V${d.version}`),
        boundaryGap: false,
        axisLine: { lineStyle: { color: isDark ? '#2c2f3a' : '#e8e5df' } },
        axisLabel: { color: isDark ? '#a0a5b5' : '#6e6e73' }
      },
      yAxis: {
        type: 'value',
        max: 100,
        min: 0,
        splitLine: { lineStyle: { color: isDark ? '#2c2f3a' : '#e8e5df' } },
        axisLabel: { color: isDark ? '#a0a5b5' : '#6e6e73' }
      },
      series: [
        {
          name: '匹配分数',
          type: 'line',
          data: diags.map(d => Math.round(d.match_score * 100)),
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          lineStyle: { color: '#5b7bb5', width: 3 },
          itemStyle: { color: '#5b7bb5' },
          areaStyle: {
            color: new (window as any).echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(91, 123, 181, 0.4)' },
              { offset: 1, color: 'rgba(91, 123, 181, 0.01)' }
            ])
          }
        }
      ]
    }
  }

  return (
    <div className="portal-shell">
      {/* Sidebar */}
      <aside className="portal-sidebar">
        <div>
          <div className="portal-sidebar-brand">
            职达 · 学校端
          </div>
          <div className="portal-sidebar-sub">
            教务双选网络管理中心
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="portal-sidebar-nav">
          {[
            { id: 'stats', label: '数据大厅统计', icon: <BarChart3 size={18} /> },
            { id: 'students', label: '全校学生档案', icon: <GraduationCap size={18} /> },
            { id: 'enterprises', label: '合作企业入驻', icon: <Building2 size={18} /> },
            { id: 'jobs', label: '企业岗位审核', icon: <ShieldCheck size={18} /> },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id as any)}
              className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
              style={activeTab === item.id ? { color: 'var(--accent-amber)' } : undefined}
            >
              {item.icon}
              <span>{item.label}</span>
            </button>
          ))}
        </nav>
      </aside>

      {/* Main Content Area */}
      <main className="portal-main">
        <header className="portal-header">
          <div>
            <h1>
              {activeTab === 'stats' && '基础统计大厅'}
              {activeTab === 'students' && '学生档案追踪'}
              {activeTab === 'enterprises' && '合作企业管理'}
              {activeTab === 'jobs' && '企业招聘审核'}
            </h1>
            <p>
              {activeTab === 'stats' && '查看并分析全校学生参与双选与 AI 诊断的总体指标'}
              {activeTab === 'students' && '查看已进行诊断的毕业生列表及其详细匹配画像'}
              {activeTab === 'enterprises' && '核对和切换入驻企业的合作状态'}
              {activeTab === 'jobs' && '教务处审核企业岗位，结合 AI 能力特征模型判定合理性'}
            </p>
          </div>
        </header>

        {/* Tab content 1: Stats summary */}
        {activeTab === 'stats' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
            {statsLoading ? (
              <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-tertiary)' }}>获取统计中...</div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 20 }}>
                {/* Metric 1 */}
                <div className="metric-card">
                  <span className="metric-label">诊断学生总数</span>
                  <span className="metric-value" style={{ color: 'var(--accent-blue)' }}>
                    {summary?.total_students || 0}人
                  </span>
                </div>
                {/* Metric 2 */}
                <div className="metric-card">
                  <span className="metric-label">入驻企业数</span>
                  <span className="metric-value" style={{ color: 'var(--accent-teal)' }}>
                    {summary?.total_enterprises || 0}家
                  </span>
                </div>
                {/* Metric 3 */}
                <div className="metric-card">
                  <span className="metric-label">在招岗位总数</span>
                  <span className="metric-value" style={{ color: 'var(--accent-amber)' }}>
                    {summary?.total_jobs || 0}个
                  </span>
                </div>
                {/* Metric 4 */}
                <div className="metric-card">
                  <span className="metric-label">待审核岗位数</span>
                  <span className="metric-value" style={{ color: 'var(--accent-rose)' }}>
                    {summary?.pending_jobs || 0}个
                  </span>
                </div>
              </div>
            )}

            <div className="glass-panel" style={{ padding: 30, borderRadius: 16, background: 'var(--bg-card)', border: '1px solid var(--border-light)', display: 'flex', flexDirection: 'column', gap: 14 }}>
              <h3 style={{ fontSize: 15, fontWeight: 700 }}>双选协同系统运行说明</h3>
              <p style={{ fontSize: 13, lineHeight: 1.7, color: 'var(--text-secondary)' }}>
                本平台作为一个<strong>三端协同网路</strong>，教务管理员在此模块对发布职位进行把关。企业发布职位后，将由 <strong>JobAbilityAgent</strong> 智能自动解析提炼该职位所需的核心能力与经历（前端能力、后端能力、知识、软实力等指标），学校管理员可在“企业岗位审核”列表查看该提取是否合理，点击通过后，学生即可针对性评估该企业岗位的匹配度并授权。
              </p>
            </div>
          </div>
        )}

        {/* Tab content 2: Students list */}
        {activeTab === 'students' && (
          <div className="glass-panel" style={{ padding: 24, borderRadius: 16, background: 'var(--bg-card)', border: '1px solid var(--border-light)' }}>
            {studentsLoading ? (
              <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-tertiary)' }}>数据加载中...</div>
            ) : students.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-tertiary)' }}>🎓 暂无学生完成简历上传或 AI 诊断。</div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>学生姓名</th>
                      <th>年级专业</th>
                      <th>目标求职岗位</th>
                      <th style={{ textAlign: 'center' }}>诊断版本数</th>
                      <th style={{ textAlign: 'center' }}>最新匹配分</th>
                      <th style={{ textAlign: 'right' }}>操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    {students.map((student) => {
                      const score = student.latest_score ? Math.round(student.latest_score * 100) : null
                      return (
                        <tr key={student.id}>
                          <td style={{ fontWeight: 600 }}>{student.name}</td>
                          <td>{student.grade} · {student.major}</td>
                          <td>{student.target_job || '未设定'}</td>
                          <td style={{ textAlign: 'center' }}>{student.diagnosis_count}次</td>
                          <td style={{ textAlign: 'center' }}>
                            {score !== null ? (
                              <span style={{
                                fontWeight: 700,
                                color: score >= 80 ? 'var(--accent-green)' : score >= 60 ? 'var(--accent-amber)' : 'var(--accent-rose)'
                              }}>{score}%</span>
                            ) : (
                              <span style={{ color: 'var(--text-tertiary)' }}>未诊断</span>
                            )}
                          </td>
                          <td style={{ textAlign: 'right' }}>
                            <button
                              className="btn btn-ghost"
                              onClick={() => handleViewStudent(student.id)}
                              disabled={studentDetailLoading}
                              style={{ padding: '4px 12px', fontSize: 12, border: '1px solid var(--accent-amber)', color: 'var(--accent-amber)' }}
                            >
                              查看档案
                            </button>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Tab content 3: Enterprises Cooperating */}
        {activeTab === 'enterprises' && (
          <div className="glass-panel" style={{ padding: 24, borderRadius: 16, background: 'var(--bg-card)', border: '1px solid var(--border-light)' }}>
            {enterprisesLoading ? (
              <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-tertiary)' }}>企业加载中...</div>
            ) : enterprises.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-tertiary)' }}>暂无入驻企业。</div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>企业名称</th>
                      <th>所属行业</th>
                      <th>对接联系人</th>
                      <th>联系邮箱</th>
                      <th style={{ textAlign: 'center' }}>状态</th>
                      <th style={{ textAlign: 'right' }}>操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    {enterprises.map((ent) => {
                      const isActive = ent.status === 'active'
                      return (
                        <tr key={ent.id}>
                          <td style={{ fontWeight: 600 }}>{ent.name}</td>
                          <td>{ent.industry || '未填写'}</td>
                          <td>{ent.contact_name || '未填写'}</td>
                          <td>{ent.contact_email || '未填写'}</td>
                          <td style={{ textAlign: 'center' }}>
                            <span className={isActive ? 'badge badge-green' : 'badge badge-rose'}>
                              {isActive ? '合作中' : '已禁用'}
                            </span>
                          </td>
                          <td style={{ textAlign: 'right' }}>
                            <button
                              className="btn btn-ghost"
                              onClick={() => handleToggleEnterpriseStatus(ent.id, ent.status)}
                              disabled={updatingEntId === ent.id}
                              style={{
                                padding: '4px 12px',
                                fontSize: 12,
                                border: `1px solid ${isActive ? 'var(--accent-rose)' : 'var(--accent-green)'}`,
                                color: isActive ? 'var(--accent-rose)' : 'var(--accent-green)'
                              }}
                            >
                              {updatingEntId === ent.id ? '处理中...' : isActive ? '禁用企业' : '启用企业'}
                            </button>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Tab content 4: Jobs Audit review flow */}
        {activeTab === 'jobs' && (
          <div style={{ display: 'flex', gap: 28, height: '620px', alignItems: 'stretch' }}>
            {/* Left Column: Job posts list with filter status */}
            <div className="glass-panel" style={{
              width: 320,
              background: 'var(--bg-card)',
              border: '1px solid var(--border-light)',
              borderRadius: 16,
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden'
            }}>
              <div style={{ padding: 12, borderBottom: '1px solid var(--border-light)', display: 'flex', gap: 6 }}>
                {(['pending_review', 'approved', 'rejected'] as const).map(f => (
                  <button
                    key={f}
                    onClick={() => setAuditFilter(f)}
                    style={{
                      flex: 1,
                      padding: '6px 4px',
                      fontSize: 11,
                      border: 'none',
                      borderRadius: 6,
                      cursor: 'pointer',
                      background: auditFilter === f ? 'var(--bg-hover)' : 'transparent',
                      color: auditFilter === f ? 'var(--accent-amber)' : 'var(--text-secondary)',
                      fontWeight: auditFilter === f ? 700 : 500,
                    }}
                  >
                    {f === 'pending_review' && '待审核'}
                    {f === 'approved' && '已通过'}
                    {f === 'rejected' && '已驳回'}
                  </button>
                ))}
              </div>
              <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
                {jobsLoading ? (
                  <div style={{ textAlign: 'center', padding: 20, color: 'var(--text-tertiary)' }}>加载中...</div>
                ) : jobs.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-tertiary)', fontSize: 13 }}>
                    🛡️ 当前状态无岗位记录。
                  </div>
                ) : (
                  jobs.map((job) => {
                    const isActive = selectedJob?.id === job.id
                    return (
                      <div
                        key={job.id}
                        onClick={() => handleSelectJob(job)}
                        style={{
                          padding: '16px 20px',
                          borderBottom: '1px solid var(--border-light)',
                          cursor: 'pointer',
                          background: isActive ? 'var(--bg-hover)' : 'transparent',
                          borderLeft: isActive ? '3px solid var(--accent-amber)' : 'none',
                          transition: 'all 0.2s',
                        }}
                      >
                        <div style={{ fontWeight: 600, fontSize: 14, color: isActive ? 'var(--accent-amber)' : 'var(--text-primary)' }}>{job.title}</div>
                        <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 6 }}>发布企业：{job.enterprise_name}</div>
                      </div>
                    )
                  })
                )}
              </div>
            </div>

            {/* Right Column: Audit Panel details */}
            <div className="glass-panel" style={{
              flex: 1,
              background: 'var(--bg-card)',
              border: '1px solid var(--border-light)',
              borderRadius: 16,
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden'
            }}>
              {selectedJob ? (
                <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
                  {/* Job Header */}
                  <div style={{ padding: '24px 28px', borderBottom: '1px solid var(--border-light)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <h2 style={{ fontSize: 18, fontWeight: 700, margin: 0 }}>{selectedJob.title}</h2>
                      <span className={
                        selectedJob.status === 'approved' ? 'badge badge-green' :
                        selectedJob.status === 'pending_review' ? 'badge badge-amber' :
                        selectedJob.status === 'rejected' ? 'badge badge-rose' :
                        'badge badge-gray'
                      }>
                        {selectedJob.status === 'approved' && '已通过审核'}
                        {selectedJob.status === 'pending_review' && '等待学校审核'}
                        {selectedJob.status === 'rejected' && '已驳回'}
                      </span>
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>
                      发布企业：<strong>{selectedJob.enterprise_name}</strong> | 岗位品类：{selectedJob.category}
                    </div>
                  </div>

                  {/* Details Scroll */}
                  <div style={{ flex: 1, overflowY: 'auto', padding: '24px 28px', display: 'flex', flexDirection: 'column', gap: 24 }}>
                    {selectedJob.status === 'rejected' && selectedJob.review_reason && (
                      <div style={{
                        background: 'rgba(196, 122, 139, 0.08)',
                        border: '1px solid rgba(196, 122, 139, 0.2)',
                        padding: '12px 16px',
                        borderRadius: 8,
                        color: 'var(--accent-rose)',
                        fontSize: 13
                      }}>
                        <strong>⚠️ 驳回原委描述：</strong>{selectedJob.review_reason}
                      </div>
                    )}

                    <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: 28 }}>
                      {/* Left: Description */}
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                        <div>
                          <h4 style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 6 }}>职位JD描述信息</h4>
                          <pre style={{
                            padding: 14,
                            borderRadius: 8,
                            background: 'var(--bg-hover)',
                            border: '1px solid var(--border-light)',
                            fontSize: 12,
                            lineHeight: 1.5,
                            whiteSpace: 'pre-wrap',
                            fontFamily: 'var(--font-mono)',
                            color: 'var(--text-primary)'
                          }}>{selectedJob.requirements_text}</pre>
                        </div>
                      </div>

                      {/* Right: AI parsed model check */}
                      <div>
                        <h4 style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 12 }}>AI 解析建模合理性核查</h4>
                        {!selectedJobModel ? (
                          <div style={{ padding: 20, textAlign: 'center', border: '1px dashed var(--border-light)', borderRadius: 10, color: 'var(--text-tertiary)', fontSize: 12 }}>
                            该岗位暂无提取的能力模型。企业端保存 JD 后，需由企业端触发 AI 解析建模。
                          </div>
                        ) : (
                          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                            <div>
                              <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 6 }}>技术技能要求</div>
                              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                {Object.entries(selectedJobModel.tech_skills || {}).map(([skill, val]: any) => (
                                  <div key={skill} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, background: 'var(--bg-hover)', padding: '4px 8px', borderRadius: 4 }}>
                                    <span>{skill}</span>
                                    <span style={{ fontWeight: 600 }}>{val}分</span>
                                  </div>
                                ))}
                              </div>
                            </div>

                            <div>
                              <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 6 }}>领域知识要求</div>
                              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                {Object.entries(selectedJobModel.domain_knowledge || {}).map(([dom, val]: any) => (
                                  <div key={dom} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, background: 'var(--bg-hover)', padding: '4px 8px', borderRadius: 4 }}>
                                    <span>{dom}</span>
                                    <span style={{ fontWeight: 600 }}>{val}分</span>
                                  </div>
                                ))}
                              </div>
                            </div>

                            <div style={{ fontSize: 11, background: 'var(--bg-hover)', padding: 10, borderRadius: 8 }}>
                              <div>💻 技术权重: <strong>{Math.round((selectedJobModel.weight_config?.tech_skills || 0) * 100)}%</strong></div>
                              <div style={{ marginTop: 2 }}>📈 知识权重: <strong>{Math.round((selectedJobModel.weight_config?.domain_knowledge || 0) * 100)}%</strong></div>
                              <div style={{ marginTop: 2 }}>🤝 软技能权重: <strong>{Math.round((selectedJobModel.weight_config?.soft_skills || 0) * 100)}%</strong></div>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Audit Footer actions */}
                  {selectedJob.status === 'pending_review' && (
                    <div style={{ padding: '16px 28px', borderTop: '1px solid var(--border-light)', background: 'var(--bg-hover)', display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
                      <button
                        onClick={() => handleStartRejectJob(selectedJob.id)}
                        disabled={auditLoading}
                        className="btn btn-ghost"
                        style={{ border: '1px solid var(--accent-rose)', color: 'var(--accent-rose)' }}
                      >
                        驳回岗位申请
                      </button>
                      <button
                        onClick={() => handleApproveJob(selectedJob.id)}
                        disabled={auditLoading}
                        className="btn btn-primary"
                        style={{ background: 'var(--accent-amber)' }}
                      >
                        {auditLoading ? '处理中...' : '✅ 审核通过发布'}
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <div style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', color: 'var(--text-tertiary)', flexDirection: 'column', gap: 12 }}>
                  <span style={{ fontSize: 40 }}>🛡️</span>
                  <span>请在左侧选择需要审核或查看的岗位。</span>
                </div>
              )}
            </div>
          </div>
        )}
      </main>

      {/* Student detail view modal */}
      {showStudentModal && selectedStudent && (
        <div className="modal-overlay">
          <div className="modal-panel animate-slide-up" style={{
            width: '90%',
            maxWidth: '850px',
            height: '80vh',
            overflow: 'hidden'
          }}>
            <div style={{ padding: '20px 30px', borderBottom: '1px solid var(--border-light)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ fontSize: 18, fontWeight: 700, margin: 0 }}>学生综合成长档案：{selectedStudent.student.name}</h3>
                <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                  {selectedStudent.student.grade} · {selectedStudent.student.major} | 目标求职岗位：{selectedStudent.student.target_job || '未设定'}
                </span>
              </div>
              <button onClick={() => setShowStudentModal(false)} style={{ background: 'transparent', border: 'none', fontSize: 24, cursor: 'pointer', color: 'var(--text-secondary)' }}>
                &times;
              </button>
            </div>

            <div style={{ flex: 1, overflowY: 'auto', padding: 30, display: 'flex', flexDirection: 'column', gap: 28 }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.2fr', gap: 28 }}>
                {/* Left: diagnoses trend */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                  <h4 style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-secondary)' }}>AI 诊断匹配分数变化趋势</h4>
                  {selectedStudent.diagnoses.length === 0 ? (
                    <div style={{ padding: 40, border: '1px dashed var(--border-light)', borderRadius: 10, textAlign: 'center', fontSize: 12, color: 'var(--text-tertiary)' }}>
                      学生暂无诊断记录
                    </div>
                  ) : (
                    <div style={{ height: '220px', background: 'var(--bg-hover)', borderRadius: 12, padding: 10 }}>
                      <ReactECharts option={getStudentGrowthOption()} style={{ height: '100%', width: '100%' }} />
                    </div>
                  )}
                </div>

                {/* Right: authorizations */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                  <h4 style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-secondary)' }}>学生主动授权记录 ({selectedStudent.authorizations.length})</h4>
                  <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 10, maxHeight: '240px' }}>
                    {selectedStudent.authorizations.length === 0 ? (
                      <div style={{ padding: 40, border: '1px dashed var(--border-light)', borderRadius: 10, textAlign: 'center', fontSize: 12, color: 'var(--text-tertiary)' }}>
                        该学生尚未向任何企业授权画像数据。
                      </div>
                    ) : (
                      selectedStudent.authorizations.map((auth: any) => (
                        <div key={auth.id} style={{ border: '1px solid var(--border-light)', borderRadius: 8, padding: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 12 }}>
                          <div>
                            <div style={{ fontWeight: 600 }}>{auth.job_title}</div>
                            <div style={{ color: 'var(--text-secondary)', marginTop: 2 }}>意向企业：{auth.enterprise_name}</div>
                          </div>
                          <div style={{ textAlign: 'right' }}>
                            <span className={auth.status === 'active' ? 'badge badge-green' : 'badge badge-gray'}>
                              {auth.status === 'active' ? '授权中' : '已撤销'}
                            </span>
                            <div style={{ color: 'var(--text-tertiary)', fontSize: 10, marginTop: 4 }}>
                              {auth.created_at ? new Date(auth.created_at).toLocaleDateString() : ''}
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            </div>

            <div style={{ padding: '16px 30px', borderTop: '1px solid var(--border-light)', background: 'var(--bg-hover)', display: 'flex', justifyContent: 'flex-end' }}>
              <button className="btn btn-primary" onClick={() => setShowStudentModal(false)} style={{ background: 'var(--accent-amber)' }}>
                关闭档案
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Reject Reason input dialog */}
      {showRejectModal && (
        <div className="modal-overlay">
          <div className="modal-panel" style={{
            width: '90%',
            maxWidth: '450px',
            padding: 24,
            gap: 16
          }}>
            <h3 style={{ fontSize: 15, fontWeight: 700, margin: 0 }}>填写驳回审核原因</h3>
            <form onSubmit={handleConfirmReject} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <textarea
                required
                rows={4}
                placeholder="请详细描述驳回原因，例如：JD 格式不完整，或提取的技术指标要求与行业常规不符，请重新编辑后再提交。"
                value={rejectReason}
                onChange={e => setRejectReason(e.target.value)}
                style={{ padding: 12, borderRadius: 8, border: '1px solid var(--border-light)', background: 'var(--bg-page)', color: 'var(--text-primary)', fontSize: 13, outline: 'none', resize: 'vertical' }}
              />
              <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
                <button type="button" className="btn btn-ghost" onClick={() => setShowRejectModal(false)}>取消</button>
                <button type="submit" className="btn btn-primary" style={{ background: 'var(--accent-rose)' }}>确认驳回</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
