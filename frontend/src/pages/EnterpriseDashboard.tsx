import { useState, useEffect } from 'react'
import { useAppStore } from '../stores/appStore'
import ReactECharts from 'echarts-for-react'
import { FileText, Users, Building2 } from 'lucide-react'
import {
  getEnterpriseProfile,
  updateEnterpriseProfile,
  getEnterpriseJobs,
  createEnterpriseJob,
  getEnterpriseJobDetail,
  updateEnterpriseJob,
  parseJobAbilityModel,
  submitJobReview,
  getEnterpriseCandidates,
  getEnterpriseCandidateDetail
} from '../services/api'

interface JobPost {
  id: string
  enterprise_id: string
  title: string
  category: string
  description: string
  requirements_text: string
  status: 'draft' | 'pending_review' | 'approved' | 'rejected' | 'disabled'
  review_reason?: string
  created_at: string
}

interface AbilityModel {
  tech_skills: Record<string, number>
  soft_skills: Record<string, number>
  domain_knowledge: Record<string, number>
  project_exp: Array<{ name: string; description: string }>
  weight_config: { tech_skills: number; soft_skills: number; domain_knowledge: number }
}

export default function EnterpriseDashboard() {
  const { theme, mockEnterpriseId } = useAppStore()
  const [activeTab, setActiveTab] = useState<'profile' | 'jobs' | 'candidates'>('jobs')

  // Theme states
  const isDark = theme === 'dark'

  // Profile states
  const [profile, setProfile] = useState<any>(null)
  const [isEditingProfile, setIsEditingProfile] = useState(false)
  const [profileForm, setProfileForm] = useState({
    name: '',
    industry: '',
    description: '',
    contact_name: '',
    contact_email: ''
  })
  const [profileLoading, setProfileLoading] = useState(false)

  // Jobs states
  const [jobs, setJobs] = useState<JobPost[]>([])
  const [selectedJob, setSelectedJob] = useState<JobPost | null>(null)
  const [selectedJobModel, setSelectedJobModel] = useState<AbilityModel | null>(null)
  const [jobsLoading, setJobsLoading] = useState(false)
  const [detailLoading, setDetailLoading] = useState(false)

  // Job edit form states
  const [isEditingJob, setIsEditingJob] = useState(false)
  const [isCreatingJob, setIsCreatingJob] = useState(false)
  const [jobForm, setJobForm] = useState({
    title: '',
    category: '',
    description: '',
    requirements_text: ''
  })

  // Action loading states
  const [parsingJobId, setParsingJobId] = useState<string | null>(null)
  const [submittingJobId, setSubmittingJobId] = useState<string | null>(null)

  // Candidates states
  const [candidates, setCandidates] = useState<any[]>([])
  const [candidatesLoading, setCandidatesLoading] = useState(false)
  const [selectedCandidate, setSelectedCandidate] = useState<any | null>(null)
  const [candDetailLoading, setCandDetailLoading] = useState(false)
  const [showCandModal, setShowCandModal] = useState(false)

  // Load profile
  const loadProfile = async () => {
    setProfileLoading(true)
    try {
      const data = await getEnterpriseProfile(mockEnterpriseId)
      setProfile(data)
      setProfileForm({
        name: data.name || '',
        industry: data.industry || '',
        description: data.description || '',
        contact_name: data.contact_name || '',
        contact_email: data.contact_email || ''
      })
    } catch (err) {
      console.error('Failed to load profile', err)
    } finally {
      setProfileLoading(false)
    }
  }

  // Load jobs list
  const loadJobs = async (selectId?: string) => {
    setJobsLoading(true)
    try {
      const data = await getEnterpriseJobs(mockEnterpriseId)
      setJobs(data)
      if (data.length > 0) {
        const toSelect = selectId ? data.find((j: any) => j.id === selectId) : data[0]
        if (toSelect) {
          handleSelectJob(toSelect)
        }
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

  // Load candidate list
  const loadCandidates = async () => {
    setCandidatesLoading(true)
    try {
      const data = await getEnterpriseCandidates(mockEnterpriseId)
      setCandidates(data)
    } catch (err) {
      console.error('Failed to load candidates', err)
    } finally {
      setCandidatesLoading(false)
    }
  }

  // Effect to load data on tab change or tenant identity swap
  useEffect(() => {
    if (activeTab === 'profile') {
      loadProfile()
    } else if (activeTab === 'jobs') {
      loadJobs()
    } else if (activeTab === 'candidates') {
      loadCandidates()
    }
  }, [activeTab, mockEnterpriseId])

  // Select job item and fetch ability model
  const handleSelectJob = async (job: JobPost) => {
    setSelectedJob(job)
    setIsEditingJob(false)
    setIsCreatingJob(false)
    setDetailLoading(true)
    try {
      const res = await getEnterpriseJobDetail(job.id, mockEnterpriseId)
      setSelectedJobModel(res.ability_model)
    } catch (err) {
      console.error('Failed to load job details', err)
      setSelectedJobModel(null)
    } finally {
      setDetailLoading(false)
    }
  }

  // Profile save
  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault()
    setProfileLoading(true)
    try {
      const updated = await updateEnterpriseProfile(mockEnterpriseId, profileForm)
      setProfile(updated)
      setIsEditingProfile(false)
    } catch (err) {
      alert('更新企业资料失败')
    } finally {
      setProfileLoading(false)
    }
  }

  // Job creation trigger
  const handleStartCreateJob = () => {
    setIsCreatingJob(true)
    setIsEditingJob(false)
    setSelectedJob(null)
    setSelectedJobModel(null)
    setJobForm({
      title: '',
      category: '后端开发',
      description: '',
      requirements_text: ''
    })
  }

  // Job edit trigger
  const handleStartEditJob = () => {
    if (!selectedJob) return
    setIsEditingJob(true)
    setIsCreatingJob(false)
    setJobForm({
      title: selectedJob.title || '',
      category: selectedJob.category || '',
      description: selectedJob.description || '',
      requirements_text: selectedJob.requirements_text || ''
    })
  }

  // Job save
  const handleSaveJob = async (e: React.FormEvent) => {
    e.preventDefault()
    setJobsLoading(true)
    try {
      if (isCreatingJob) {
        const newJob = await createEnterpriseJob(mockEnterpriseId, {
          ...jobForm,
          status: 'draft' // default to draft, require AI parsing before submission
        })
        setIsCreatingJob(false)
        await loadJobs(newJob.id)
      } else if (isEditingJob && selectedJob) {
        const updated = await updateEnterpriseJob(selectedJob.id, mockEnterpriseId, {
          ...jobForm,
          status: selectedJob.status === 'rejected' ? 'draft' : selectedJob.status
        })
        setIsEditingJob(false)
        await loadJobs(updated.id)
      }
    } catch (err) {
      alert('保存岗位失败')
    } finally {
      setJobsLoading(false)
    }
  }

  // AI JD Modeling
  const handleParseAbilityModel = async (jobId: string) => {
    setParsingJobId(jobId)
    try {
      const model = await parseJobAbilityModel(jobId, mockEnterpriseId)
      setSelectedJobModel(model)
      alert('AI 岗位能力模型解析成功！已更新雷达矩阵指标。')
    } catch (err: any) {
      alert(`AI 解析失败: ${err.message || err}`)
    } finally {
      setParsingJobId(null)
    }
  }

  // Submit job for review
  const handleSubmitReview = async (jobId: string) => {
    setSubmittingJobId(jobId)
    try {
      const updated = await submitJobReview(jobId, mockEnterpriseId)
      setSelectedJob(updated)
      // refresh jobs list to show status updates
      setJobs(prev => prev.map(j => j.id === jobId ? { ...j, status: 'pending_review' } : j))
      alert('岗位已成功提交学校管理员审核！')
    } catch (err: any) {
      alert(`提交审核失败: ${err.message || err}`)
    } finally {
      setSubmittingJobId(null)
    }
  }

  // View candidate details and render double radar charts
  const handleViewCandidate = async (candidate: any) => {
    setCandDetailLoading(true)
    try {
      const detail = await getEnterpriseCandidateDetail(candidate.student_id, candidate.auth_id, mockEnterpriseId)
      setSelectedCandidate(detail)
      setShowCandModal(true)
    } catch (err) {
      alert('获取候选人详细画像失败')
    } finally {
      setCandDetailLoading(false)
    }
  }

  // Generate ECharts option for student-vs-job double line radar chart
  const getDoubleRadarOption = () => {
    if (!selectedCandidate) return {}

    const jobAbility = selectedCandidate.diagnosis.ai_reasoning?.job_ability_model || selectedCandidate.diagnosis.ai_reasoning?.ability_model || {}
    const studentSkills = selectedCandidate.student
    const diag = selectedCandidate.diagnosis

    // Merge skills from job model to form indicators
    const reqTech = jobAbility.tech_skills || {}
    const reqSoft = jobAbility.soft_skills || {}
    const reqDomain = jobAbility.domain_knowledge || {}

    // Fallback if empty
    const indicatorList = [
      ...Object.keys(reqTech).map(k => ({ name: k, max: 100, category: 'tech', val: reqTech[k] })),
      ...Object.keys(reqSoft).map(k => ({ name: k, max: 100, category: 'soft', val: reqSoft[k] })),
      ...Object.keys(reqDomain).map(k => ({ name: k, max: 100, category: 'domain', val: reqDomain[k] })),
    ]

    // If no specific model targets, use standard 4 dimensions
    if (indicatorList.length === 0) {
      const dimScores = diag.dimension_scores || {}
      return {
        backgroundColor: 'transparent',
        tooltip: { trigger: 'item' },
        legend: { data: ['学生画像'], bottom: 0, textStyle: { color: isDark ? '#a0a5b5' : '#6e6e73' } },
        radar: {
          indicator: [
            { name: '技术技能', max: 100 },
            { name: '项目经验', max: 100 },
            { name: '软技能', max: 100 },
            { name: '领域知识', max: 100 }
          ],
          splitArea: { show: false }
        },
        series: [{
          type: 'radar',
          data: [{
            value: [dimScores.tech_skills || 0, dimScores.project_exp || 0, dimScores.soft_skills || 0, dimScores.domain_knowledge || 0],
            name: '学生画像',
            areaStyle: { color: 'rgba(90, 158, 143, 0.3)' },
            lineStyle: { color: '#5a9e8f' }
          }]
        }]
      }
    }

    // Limit to top 6-8 indicators to avoid messy chart
    const indicators = indicatorList.slice(0, 8)

    // Map student's score for each indicator
    const studentValues = indicators.map(ind => {
      let score = 0
      const name = ind.name.toLowerCase()
      if (ind.category === 'tech') {
        const studentTech = diag.ai_reasoning?.student_profile?.tech_skills || studentSkills.tech_skills || {}
        const matchKey = Object.keys(studentTech).find(k => k.toLowerCase() === name)
        score = matchKey ? studentTech[matchKey] : 0
      } else if (ind.category === 'soft') {
        const studentSoft = diag.ai_reasoning?.student_profile?.soft_skills || studentSkills.soft_skills || {}
        const matchKey = Object.keys(studentSoft).find(k => k.toLowerCase() === name)
        score = matchKey ? studentSoft[matchKey] : 0
      } else {
        const studentDomain = diag.ai_reasoning?.student_profile?.domain_knowledge || studentSkills.domain_knowledge || {}
        const matchKey = Object.keys(studentDomain).find(k => k.toLowerCase() === name)
        score = matchKey ? studentDomain[matchKey] : 0
      }
      return score || 0
    })

    const jobValues = indicators.map(ind => ind.val)

    return {
      color: ['#5a9e8f', '#8b7ec8'],
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: isDark ? 'rgba(22, 24, 29, 0.95)' : 'rgba(248, 247, 244, 0.95)',
        borderColor: isDark ? '#2c2f3a' : '#e8e5df',
        textStyle: { color: isDark ? '#f5f6f9' : '#1d1d1f', fontSize: 13 },
      },
      legend: {
        data: ['学生掌握能力', '岗位特征要求'],
        bottom: 0,
        textStyle: { color: isDark ? '#a0a5b5' : '#6e6e73', fontSize: 12 }
      },
      radar: {
        center: ['50%', '45%'],
        radius: '60%',
        indicator: indicators.map(i => ({ name: i.name, max: 100 })),
        axisName: {
          color: isDark ? '#a0a5b5' : '#6e6e73',
          fontSize: 11,
          borderRadius: 3,
          padding: [2, 4],
        },
        splitArea: {
          areaStyle: {
            color: isDark
              ? ['rgba(255, 255, 255, 0.01)', 'rgba(255, 255, 255, 0.02)']
              : ['rgba(0, 0, 0, 0.02)', 'rgba(0, 0, 0, 0.005)']
          }
        },
        splitLine: { lineStyle: { color: isDark ? '#2c2f3a' : '#e8e5df' } },
        axisLine: { lineStyle: { color: isDark ? '#2c2f3a' : '#e8e5df' } }
      },
      series: [
        {
          type: 'radar',
          data: [
            {
              value: studentValues,
              name: '学生掌握能力',
              symbol: 'circle',
              symbolSize: 5,
              areaStyle: { color: 'rgba(90, 158, 143, 0.25)' },
              lineStyle: { width: 2 }
            },
            {
              value: jobValues,
              name: '岗位特征要求',
              symbol: 'none',
              lineStyle: { type: 'dashed', width: 1.5 },
              areaStyle: { color: 'rgba(139, 126, 200, 0.08)' }
            }
          ]
        }
      ]
    }
  }

  // Generate ECharts option for Gap analysis bar chart
  const getGapBarOption = () => {
    if (!selectedCandidate) return {}

    const gaps = selectedCandidate.diagnosis.gap_details || []
    if (gaps.length === 0) return {}

    // Sort gaps to show largest gaps first
    const sortedGaps = [...gaps].slice(0, 6).reverse()

    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        backgroundColor: isDark ? 'rgba(22, 24, 29, 0.95)' : 'rgba(248, 247, 244, 0.95)',
        borderColor: isDark ? '#2c2f3a' : '#e8e5df',
        textStyle: { color: isDark ? '#f5f6f9' : '#1d1d1f' }
      },
      grid: {
        left: '3%',
        right: '8%',
        bottom: '3%',
        top: '5%',
        containLabel: true
      },
      xAxis: {
        type: 'value',
        max: 100,
        min: -100,
        splitLine: { lineStyle: { color: isDark ? '#2c2f3a' : '#e8e5df' } },
        axisLabel: { color: isDark ? '#a0a5b5' : '#6e6e73' }
      },
      yAxis: {
        type: 'category',
        data: sortedGaps.map(g => g.skill_name || g.name),
        axisLine: { lineStyle: { color: isDark ? '#2c2f3a' : '#e8e5df' } },
        axisLabel: { color: isDark ? '#a0a5b5' : '#6e6e73', fontSize: 11 }
      },
      series: [
        {
          name: '能力差距',
          type: 'bar',
          data: sortedGaps.map(g => {
            const val = g.gap || (g.student_score - g.required_score) || 0
            return {
              value: val,
              itemStyle: {
                color: val >= 0 ? '#6ba87a' : '#c47a8b',
                borderRadius: [0, 4, 4, 0]
              }
            }
          }),
          label: {
            show: true,
            position: 'inside',
            formatter: (params: any) => (params.value > 0 ? `+${params.value}` : params.value)
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
            职达 · 企业端
          </div>
          <div className="portal-sidebar-sub">
            岗位发布与授权筛选中心
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="portal-sidebar-nav">
          {[
            { id: 'jobs', label: '在招岗位管理', icon: <FileText size={18} /> },
            { id: 'candidates', label: '候选人匹配', icon: <Users size={18} /> },
            { id: 'profile', label: '企业资料编辑', icon: <Building2 size={18} /> },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id as any)}
              className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
              style={activeTab === item.id ? { color: 'var(--accent-teal)' } : undefined}
            >
              {item.icon}
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="portal-sidebar-footer">
          <div style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>当前企业编号 (Mock ID):</div>
          <div style={{ fontSize: 12, fontWeight: 700, fontFamily: 'var(--font-mono)' }}>{mockEnterpriseId}</div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="portal-main">
        <header className="portal-header">
          <div>
            <h1>
              {activeTab === 'profile' && '企业资料编辑'}
              {activeTab === 'jobs' && '在招岗位管理'}
              {activeTab === 'candidates' && '已授权候选人列表'}
            </h1>
            <p>
              {activeTab === 'profile' && '完善企业详细信息以向全校展示'}
              {activeTab === 'jobs' && '发布招聘岗位并由 AI 自动解析岗位能力特征模型'}
              {activeTab === 'candidates' && '按匹配度排序查看已授权候选人画像及技能差距'}
            </p>
          </div>
          {activeTab === 'jobs' && !isEditingJob && !isCreatingJob && (
            <button className="btn btn-primary" onClick={handleStartCreateJob} style={{ background: 'var(--accent-teal)' }}>
              + 发布新岗位
            </button>
          )}
        </header>

        {/* Tab content 1: Profile */}
        {activeTab === 'profile' && (
          <div className="glass-panel" style={{
            padding: 30,
            borderRadius: 16,
            background: 'var(--bg-card)',
            border: '1px solid var(--border-light)',
            boxShadow: 'var(--shadow-sm)',
            maxWidth: 680,
          }}>
            {profileLoading ? (
              <div style={{ textAlign: 'center', padding: 20 }}>加载中...</div>
            ) : isEditingProfile ? (
              <form onSubmit={handleSaveProfile} style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  <label style={{ fontSize: 13, fontWeight: 600 }}>企业名称 *</label>
                  <input
                    type="text"
                    required
                    value={profileForm.name}
                    onChange={e => setProfileForm({ ...profileForm, name: e.target.value })}
                    style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid var(--border-light)', background: 'var(--bg-page)', color: 'var(--text-primary)', outline: 'none' }}
                  />
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  <label style={{ fontSize: 13, fontWeight: 600 }}>所属行业</label>
                  <input
                    type="text"
                    value={profileForm.industry}
                    onChange={e => setProfileForm({ ...profileForm, industry: e.target.value })}
                    style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid var(--border-light)', background: 'var(--bg-page)', color: 'var(--text-primary)', outline: 'none' }}
                  />
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  <label style={{ fontSize: 13, fontWeight: 600 }}>企业介绍</label>
                  <textarea
                    rows={4}
                    value={profileForm.description}
                    onChange={e => setProfileForm({ ...profileForm, description: e.target.value })}
                    style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid var(--border-light)', background: 'var(--bg-page)', color: 'var(--text-primary)', outline: 'none', resize: 'vertical' }}
                  />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    <label style={{ fontSize: 13, fontWeight: 600 }}>联系人姓名</label>
                    <input
                      type="text"
                      value={profileForm.contact_name}
                      onChange={e => setProfileForm({ ...profileForm, contact_name: e.target.value })}
                      style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid var(--border-light)', background: 'var(--bg-page)', color: 'var(--text-primary)', outline: 'none' }}
                    />
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    <label style={{ fontSize: 13, fontWeight: 600 }}>联系人邮箱</label>
                    <input
                      type="email"
                      value={profileForm.contact_email}
                      onChange={e => setProfileForm({ ...profileForm, contact_email: e.target.value })}
                      style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid var(--border-light)', background: 'var(--bg-page)', color: 'var(--text-primary)', outline: 'none' }}
                    />
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 12, marginTop: 10 }}>
                  <button type="submit" className="btn btn-primary" style={{ background: 'var(--accent-teal)' }}>保存资料</button>
                  <button type="button" className="btn btn-ghost" onClick={() => setIsEditingProfile(false)}>取消</button>
                </div>
              </form>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
                <div style={{ borderBottom: '1px solid var(--border-light)', paddingBottom: 16 }}>
                  <h2 style={{ fontSize: 20, fontWeight: 700, margin: 0 }}>{profile?.name || '新企业'}</h2>
                  <span style={{ fontSize: 12, color: 'var(--accent-teal)', fontWeight: 600, display: 'inline-block', marginTop: 4 }}>
                    📍 {profile?.industry || '未填写行业'}
                  </span>
                </div>
                <div>
                  <h4 style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 6 }}>企业简介</h4>
                  <p style={{ fontSize: 14, lineHeight: 1.6, color: 'var(--text-primary)', whiteSpace: 'pre-wrap' }}>
                    {profile?.description || '暂无企业介绍信息，点击编辑进行完善。'}
                  </p>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, background: 'var(--bg-hover)', padding: 16, borderRadius: 10 }}>
                  <div>
                    <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>联系人</span>
                    <div style={{ fontSize: 14, fontWeight: 600, marginTop: 2 }}>{profile?.contact_name || '未填写'}</div>
                  </div>
                  <div>
                    <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>联系邮箱</span>
                    <div style={{ fontSize: 14, fontWeight: 600, marginTop: 2 }}>{profile?.contact_email || '未填写'}</div>
                  </div>
                </div>
                <div>
                  <button className="btn btn-ghost" onClick={() => setIsEditingProfile(true)}>编辑企业资料</button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Tab content 2: Jobs Listing & AI model parsing */}
        {activeTab === 'jobs' && (
          <div style={{ display: 'flex', gap: 28, height: '620px', alignItems: 'stretch' }}>
            {/* Left Column: Job List */}
            <div className="glass-panel" style={{
              width: 320,
              background: 'var(--bg-card)',
              border: '1px solid var(--border-light)',
              borderRadius: 16,
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden'
            }}>
              <div style={{ padding: 16, borderBottom: '1px solid var(--border-light)', fontWeight: 700, fontSize: 14 }}>
                岗位列表 ({jobs.length})
              </div>
              <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
                {jobsLoading ? (
                  <div style={{ textAlign: 'center', padding: 20, color: 'var(--text-tertiary)' }}>加载中...</div>
                ) : jobs.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-tertiary)', fontSize: 13 }}>
                    🏢 暂无发布岗位，请点击右上角发布。
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
                          borderLeft: isActive ? '3px solid var(--accent-teal)' : 'none',
                          transition: 'all 0.2s',
                        }}
                      >
                        <div style={{ fontWeight: 600, fontSize: 14, color: isActive ? 'var(--accent-teal)' : 'var(--text-primary)' }}>{job.title}</div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 }}>
                          <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{job.category}</span>
                          <span className={`badge ${
                            job.status === 'approved' ? 'badge-green' :
                            job.status === 'pending_review' ? 'badge-amber' :
                            job.status === 'rejected' ? 'badge-rose' :
                            'badge-gray'
                          }`}>
                            {job.status === 'approved' && '已发布'}
                            {job.status === 'pending_review' && '审核中'}
                            {job.status === 'rejected' && '已驳回'}
                            {job.status === 'draft' && '草稿'}
                          </span>
                        </div>
                      </div>
                    )
                  })
                )}
              </div>
            </div>

            {/* Right Column: Detail Panel or Create/Edit Form */}
            <div className="glass-panel" style={{
              flex: 1,
              background: 'var(--bg-card)',
              border: '1px solid var(--border-light)',
              borderRadius: 16,
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden'
            }}>
              {isCreatingJob || isEditingJob ? (
                /* Form */
                <form onSubmit={handleSaveJob} style={{ padding: 24, display: 'flex', flexDirection: 'column', gap: 16, overflowY: 'auto', flex: 1 }}>
                  <h3 style={{ fontSize: 16, fontWeight: 700, borderBottom: '1px solid var(--border-light)', paddingBottom: 10, marginBottom: 10 }}>
                    {isCreatingJob ? '发布新岗位招聘' : '编辑岗位信息'}
                  </h3>
                  <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 16 }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                      <label style={{ fontSize: 12, fontWeight: 600 }}>岗位名称 *</label>
                      <input
                        type="text"
                        required
                        placeholder="例如：Go后端开发工程师"
                        value={jobForm.title}
                        onChange={e => setJobForm({ ...jobForm, title: e.target.value })}
                        style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid var(--border-light)', background: 'var(--bg-page)', color: 'var(--text-primary)', outline: 'none', fontSize: 13 }}
                      />
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                      <label style={{ fontSize: 12, fontWeight: 600 }}>岗位类别 *</label>
                      <select
                        value={jobForm.category}
                        onChange={e => setJobForm({ ...jobForm, category: e.target.value })}
                        style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid var(--border-light)', background: 'var(--bg-page)', color: 'var(--text-primary)', outline: 'none', fontSize: 13 }}
                      >
                        <option value="后端开发">后端开发</option>
                        <option value="前端开发">前端开发</option>
                        <option value="人工智能">人工智能</option>
                        <option value="移动端开发">移动端开发</option>
                        <option value="测试与运维">测试与运维</option>
                        <option value="产品与运营">产品与运营</option>
                      </select>
                    </div>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    <label style={{ fontSize: 12, fontWeight: 600 }}>岗位职责介绍</label>
                    <textarea
                      rows={3}
                      placeholder="主要职责描述..."
                      value={jobForm.description}
                      onChange={e => setJobForm({ ...jobForm, description: e.target.value })}
                      style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid var(--border-light)', background: 'var(--bg-page)', color: 'var(--text-primary)', outline: 'none', resize: 'vertical', fontSize: 13 }}
                    />
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    <label style={{ fontSize: 12, fontWeight: 600 }}>技能要求 & 经历要求 JD *</label>
                    <textarea
                      rows={5}
                      required
                      placeholder="请详细填写岗位招聘要求，以便 AI 提取合理的雷达图模型。例如：&#10;1. 熟练掌握 React, TypeScript, TailwindCSS&#10;2. 熟悉 RESTful API 设计与交互数据交互&#10;3. 有完整独立前端项目开发经验优先"
                      value={jobForm.requirements_text}
                      onChange={e => setJobForm({ ...jobForm, requirements_text: e.target.value })}
                      style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid var(--border-light)', background: 'var(--bg-page)', color: 'var(--text-primary)', outline: 'none', resize: 'vertical', fontSize: 13, fontFamily: 'var(--font-mono)' }}
                    />
                  </div>
                  <div style={{ display: 'flex', gap: 12, marginTop: 10 }}>
                    <button type="submit" className="btn btn-primary" style={{ background: 'var(--accent-teal)' }}>保存并进入下一步</button>
                    <button type="button" className="btn btn-ghost" onClick={() => {
                      setIsCreatingJob(false)
                      setIsEditingJob(false)
                      if (jobs.length > 0) handleSelectJob(jobs[0])
                    }}>取消</button>
                  </div>
                </form>
              ) : selectedJob ? (
                /* Details Panel */
                <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
                  {/* Job Header */}
                  <div style={{ padding: '24px 28px', borderBottom: '1px solid var(--border-light)', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <h2 style={{ fontSize: 18, fontWeight: 700, margin: 0 }}>{selectedJob.title}</h2>
                        <span className={`badge ${
                          selectedJob.status === 'approved' ? 'badge-green' :
                          selectedJob.status === 'pending_review' ? 'badge-amber' :
                          selectedJob.status === 'rejected' ? 'badge-rose' :
                          'badge-gray'
                        }`}>
                          {selectedJob.status === 'approved' && '学校已审核通过 · 招聘中'}
                          {selectedJob.status === 'pending_review' && '教务审核中'}
                          {selectedJob.status === 'rejected' && '已驳回'}
                          {selectedJob.status === 'draft' && '草稿阶段 (尚未提交审核)'}
                        </span>
                      </div>
                      <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>岗位品类：{selectedJob.category}</div>
                    </div>
                    {(selectedJob.status === 'draft' || selectedJob.status === 'rejected') && (
                      <button className="btn btn-ghost" onClick={handleStartEditJob} style={{ padding: '6px 12px', fontSize: 12 }}>
                        编辑岗位
                      </button>
                    )}
                  </div>

                  {/* Detail contents */}
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
                        <strong>⚠️ 驳回原因：</strong>{selectedJob.review_reason}
                      </div>
                    )}

                    <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: 28 }}>
                      {/* Left Part: Description & JD */}
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                        <div>
                          <h4 style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 6 }}>岗位简介</h4>
                          <p style={{ fontSize: 13, lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>{selectedJob.description || '暂无简介'}</p>
                        </div>
                        <div>
                          <h4 style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 6 }}>招聘描述与技能要求 (JD)</h4>
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

                      {/* Right Part: Ability Model */}
                      <div>
                        <h4 style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 12 }}>AI 解析能力指标模型</h4>
                        {detailLoading ? (
                          <div style={{ padding: '40px 0', textAlign: 'center', color: 'var(--text-tertiary)' }}>获取指标模型中...</div>
                        ) : !selectedJobModel ? (
                          <div style={{
                            padding: 20,
                            borderRadius: 10,
                            border: '1px dashed var(--border-light)',
                            textAlign: 'center',
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            gap: 10
                          }}>
                            <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>您尚未提取该岗位的能力指标特征</span>
                            <button
                              onClick={() => handleParseAbilityModel(selectedJob.id)}
                              disabled={parsingJobId === selectedJob.id}
                              className="btn btn-primary"
                              style={{ padding: '6px 14px', fontSize: 12, background: 'var(--accent-teal)' }}
                            >
                              {parsingJobId === selectedJob.id ? '大模型提取中...' : '💡 智能体提取能力指标'}
                            </button>
                          </div>
                        ) : (
                          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                            {/* Skills progress lines */}
                            <div>
                              <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 6 }}>技术技能要求</div>
                              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                                {Object.entries(selectedJobModel.tech_skills).map(([skill, val]) => (
                                  <div key={skill} style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }}>
                                      <span>{skill}</span>
                                      <span style={{ fontWeight: 600 }}>{val}分</span>
                                    </div>
                                    <div style={{ height: 4, width: '100%', background: 'var(--bg-hover)', borderRadius: 2 }}>
                                      <div style={{ height: '100%', width: `${val}%`, background: 'var(--accent-teal)', borderRadius: 2 }} />
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>

                            <div>
                              <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 6 }}>领域知识要求</div>
                              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                                {Object.entries(selectedJobModel.domain_knowledge).map(([dom, val]) => (
                                  <div key={dom} style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }}>
                                      <span>{dom}</span>
                                      <span style={{ fontWeight: 600 }}>{val}分</span>
                                    </div>
                                    <div style={{ height: 4, width: '100%', background: 'var(--bg-hover)', borderRadius: 2 }}>
                                      <div style={{ height: '100%', width: `${val}%`, background: 'var(--accent-blue)', borderRadius: 2 }} />
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>

                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.2fr', gap: 12, background: 'var(--bg-hover)', padding: 12, borderRadius: 8, fontSize: 11 }}>
                              <div>
                                <strong style={{ color: 'var(--text-secondary)' }}>核心软技能：</strong>
                                <div style={{ marginTop: 4 }}>
                                  {Object.keys(selectedJobModel.soft_skills).join(' / ') || '未提取'}
                                </div>
                              </div>
                              <div>
                                <strong style={{ color: 'var(--text-secondary)' }}>核心项目经历要求：</strong>
                                <div style={{ marginTop: 4, maxHeight: '60px', overflowY: 'auto' }}>
                                  {selectedJobModel.project_exp.map((p, idx) => (
                                    <div key={idx} style={{ color: 'var(--text-primary)', marginBottom: 2 }}>
                                      • {p.name}
                                    </div>
                                  )) || '无'}
                                </div>
                              </div>
                            </div>

                            {/* Weight Configuration */}
                            <div style={{ background: 'var(--bg-hover)', padding: 10, borderRadius: 8, display: 'flex', justifyContent: 'space-around', fontSize: 11 }}>
                              <div>💻 技术权重: <strong>{Math.round((selectedJobModel.weight_config?.tech_skills || 0) * 100)}%</strong></div>
                              <div>📈 知识权重: <strong>{Math.round((selectedJobModel.weight_config?.domain_knowledge || 0) * 100)}%</strong></div>
                              <div>🤝 软技能权重: <strong>{Math.round((selectedJobModel.weight_config?.soft_skills || 0) * 100)}%</strong></div>
                            </div>

                            {/* Re-parse buttons */}
                            <button
                              onClick={() => handleParseAbilityModel(selectedJob.id)}
                              disabled={parsingJobId === selectedJob.id}
                              className="btn btn-ghost"
                              style={{ width: '100%', padding: '6px 12px', fontSize: 12, borderStyle: 'dashed' }}
                            >
                              {parsingJobId === selectedJob.id ? '大模型重新提取中...' : '重新进行 AI 解析建模'}
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Actions Footer */}
                  {selectedJobModel && (selectedJob.status === 'draft' || selectedJob.status === 'rejected') && (
                    <div style={{ padding: '16px 28px', borderTop: '1px solid var(--border-light)', background: 'var(--bg-hover)', display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
                      <span style={{ fontSize: 12, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center' }}>
                        对指标模型满意后，即可提交学校审核：
                      </span>
                      <button
                        onClick={() => handleSubmitReview(selectedJob.id)}
                        disabled={submittingJobId === selectedJob.id}
                        className="btn btn-primary"
                        style={{ padding: '8px 20px', background: 'var(--accent-teal)' }}
                      >
                        {submittingJobId === selectedJob.id ? '提交中...' : '🚀 提交学校教务审核'}
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <div style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', color: 'var(--text-tertiary)', flexDirection: 'column', gap: 12 }}>
                  <span style={{ fontSize: 40 }}>📄</span>
                  <span>请在左侧选择一个在招岗位或创建新岗位。</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab content 3: Candidates list */}
        {activeTab === 'candidates' && (
          <div className="glass-panel" style={{
            padding: 24,
            borderRadius: 16,
            background: 'var(--bg-card)',
            border: '1px solid var(--border-light)',
            boxShadow: 'var(--shadow-sm)',
          }}>
            {candidatesLoading ? (
              <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-tertiary)' }}>加载中...</div>
            ) : candidates.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 60, color: 'var(--text-tertiary)', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
                <span style={{ fontSize: 40 }}>👥</span>
                <span style={{ fontSize: 14 }}>暂无学生授权其 AI 画像到您的在招岗位。</span>
                <span style={{ fontSize: 12, color: 'var(--text-tertiary)', maxWidth: 460 }}>
                  学生在学生端完成 AI 画像诊断后，如果选择了您的岗位作为诊断目标，可以主动选择“授权”将画像公开给您查看。
                </span>
              </div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table className="data-table">
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border-light)', color: 'var(--text-secondary)' }}>
                      <th style={{ padding: '12px 16px' }}>候选人姓名</th>
                      <th style={{ padding: '12px 16px' }}>年级专业</th>
                      <th style={{ padding: '12px 16px' }}>申请岗位</th>
                      <th style={{ padding: '12px 16px', textAlign: 'center' }}>岗位匹配度</th>
                      <th style={{ padding: '12px 16px' }}>授权时间</th>
                      <th style={{ padding: '12px 16px', textAlign: 'right' }}>操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    {candidates.map((cand) => {
                      const pct = Math.round(cand.match_score * 100)
                      return (
                        <tr key={cand.auth_id} style={{ borderBottom: '1px solid var(--border-light)' }}>
                          <td style={{ padding: '16px 16px', fontWeight: 600 }}>{cand.student_name}</td>
                          <td style={{ padding: '16px 16px' }}>{cand.student_grade} · {cand.student_major}</td>
                          <td style={{ padding: '16px 16px' }}>{cand.job_title}</td>
                          <td style={{ padding: '16px 16px', textAlign: 'center' }}>
                            <span style={{
                              fontWeight: 700,
                              fontSize: 14,
                              color: pct >= 80 ? 'var(--accent-green)' : pct >= 60 ? 'var(--accent-amber)' : 'var(--accent-rose)'
                            }}>{pct}%</span>
                          </td>
                          <td style={{ padding: '16px 16px', color: 'var(--text-secondary)', fontSize: 12 }}>
                            {cand.auth_date ? new Date(cand.auth_date).toLocaleDateString() : '-'}
                          </td>
                          <td style={{ padding: '16px 16px', textAlign: 'right' }}>
                            <button
                              className="btn btn-ghost"
                              onClick={() => handleViewCandidate(cand)}
                              disabled={candDetailLoading}
                              style={{ padding: '4px 12px', fontSize: 12, border: '1px solid var(--accent-teal)', color: 'var(--accent-teal)' }}
                            >
                              查看对比报告
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
      </main>

      {/* Candidate comparison drawer/modal */}
      {showCandModal && selectedCandidate && (
        <div className="modal-overlay">
          <div className="modal-panel">
            {/* Modal Header */}
            <div style={{
              padding: '20px 30px',
              borderBottom: '1px solid var(--border-light)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div>
                <h3 style={{ fontSize: 18, fontWeight: 700, margin: 0 }}>
                  候选人匹配对比报告：{selectedCandidate.student.name}
                </h3>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>
                  针对岗位：<strong>{selectedCandidate.job.title}</strong> | 匹配评分：
                  <strong style={{ color: 'var(--accent-teal)', fontSize: 14 }}>
                    {Math.round(selectedCandidate.diagnosis.match_score * 100)}%
                  </strong>
                </div>
              </div>
              <button
                onClick={() => setShowCandModal(false)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  fontSize: 24,
                  cursor: 'pointer',
                  color: 'var(--text-secondary)'
                }}
              >
                &times;
              </button>
            </div>

            {/* Modal Scroll Content */}
            <div style={{ flex: 1, overflowY: 'auto', padding: 30, display: 'flex', flexDirection: 'column', gap: 24 }}>
              {/* Top Details grid */}
              <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: 24 }}>
                {/* Profile detail */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  <div style={{ background: 'var(--bg-hover)', padding: 18, borderRadius: 12 }}>
                    <h4 style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 10 }}>教育与岗位背景</h4>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, fontSize: 13 }}>
                      <div>年级门类: <strong>{selectedCandidate.student.grade}</strong></div>
                      <div>专业方向: <strong>{selectedCandidate.student.major}</strong></div>
                      <div>意向求职: <strong>{selectedCandidate.student.target_job}</strong></div>
                    </div>
                  </div>

                  <div>
                    <h4 style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 6 }}>项目经历对比</h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                      {selectedCandidate.student.project_exp.length === 0 ? (
                        <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>简历中无提取项目经验</span>
                      ) : (
                        selectedCandidate.student.project_exp.map((p: any, idx: number) => (
                          <div key={idx} style={{ border: '1px solid var(--border-light)', padding: 10, borderRadius: 8, fontSize: 12 }}>
                            <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{p.name}</div>
                            <div style={{ color: 'var(--text-secondary)', marginTop: 4 }}>{p.description}</div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </div>

                {/* AI Rationale & Advice */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  <div style={{ border: '1px solid var(--accent-teal)', background: 'rgba(90, 158, 143, 0.05)', padding: 18, borderRadius: 12 }}>
                    <h4 style={{ fontSize: 13, fontWeight: 700, color: 'var(--accent-teal)', marginBottom: 8 }}>💡 AI 岗位画像匹配依据</h4>
                    <p style={{ fontSize: 12, lineHeight: 1.6, color: 'var(--text-primary)', whiteSpace: 'pre-wrap' }}>
                      {selectedCandidate.diagnosis.ai_reasoning?.reasoning ||
                       selectedCandidate.diagnosis.ai_reasoning?.match_analysis ||
                       selectedCandidate.diagnosis.career_advice ||
                       'AI 推荐语加载中...'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Middle Charts: Radar Chart & Gap chart */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, borderTop: '1px solid var(--border-light)', paddingTop: 24 }}>
                <div style={{ height: '320px', display: 'flex', flexDirection: 'column' }}>
                  <h4 style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 10, textAlign: 'center' }}>
                    技能匹配雷达对比图
                  </h4>
                  <div style={{ flex: 1 }}>
                    <ReactECharts option={getDoubleRadarOption()} style={{ height: '100%', width: '100%' }} />
                  </div>
                </div>

                <div style={{ height: '320px', display: 'flex', flexDirection: 'column' }}>
                  <h4 style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 10, textAlign: 'center' }}>
                    核心指标能力差距分析
                  </h4>
                  <div style={{ flex: 1 }}>
                    <ReactECharts option={getGapBarOption()} style={{ height: '100%', width: '100%' }} />
                  </div>
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div style={{
              padding: '16px 30px',
              borderTop: '1px solid var(--border-light)',
              background: 'var(--bg-hover)',
              display: 'flex',
              justifyContent: 'flex-end'
            }}>
              <button className="btn btn-primary" onClick={() => setShowCandModal(false)} style={{ background: 'var(--accent-teal)' }}>
                关闭报告
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
