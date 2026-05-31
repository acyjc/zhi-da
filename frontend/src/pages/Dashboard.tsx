// 一站式诊断看板——SSE 流式诊断 + 6 个 Tab 结果展示 + 侧边导航 + 导出工具
import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppStore } from '../stores/appStore'
import { startDiagnosis, reEvaluate, getDiagnosisHistory, getStudent } from '../services/api'
import type { DiagnosisResult, AbilityProfile, AbilityDimension } from '../types'
import ProgressSteps from '../components/shared/ProgressSteps'
import ReEvaluatePrompt from '../components/shared/ReEvaluatePrompt'
import ExportToolbar from '../components/export/ExportToolbar'
import ProfileTab from '../components/diagnosis/ProfileTab'
import MatchTab from '../components/diagnosis/MatchTab'
import PathTab from '../components/diagnosis/PathTab'
import AdviceTab from '../components/diagnosis/AdviceTab'
import RecommendTab from '../components/diagnosis/RecommendTab'
import GrowthTab from '../components/diagnosis/GrowthTab'

type TabKey = 'profile' | 'match' | 'path' | 'advice' | 'recommend' | 'growth'

// 六个分析维度的 Tab 定义
const TABS: { key: TabKey; label: string }[] = [
  { key: 'profile', label: '能力画像' },
  { key: 'match', label: '岗位匹配' },
  { key: 'path', label: '成长路径' },
  { key: 'advice', label: '职业建议' },
  { key: 'recommend', label: '就业推荐' },
  { key: 'growth', label: '成长追踪' },
]

// 从后端返回数据构建前端需要的 AbilityProfile 结构
const buildProfile = (result: any, studentData?: any): AbilityProfile => {
  if (result?.ability_profile) return result.ability_profile
  if (result?.profile) return result.profile

  interface SkillItem { name: string; score: number; level: string }

  const makeDim = (key: string): AbilityDimension => {
    const score = result?.dimension_scores?.[key] ?? 0
    const skills = studentData?.[key] ?? {}
    const subItems: SkillItem[] = Object.entries(skills).map(([name, val]) => ({
      name,
      score: typeof val === 'number' ? Math.round(val) : 60,
      level: typeof val === 'number' ? (val >= 80 ? '精通' : val >= 60 ? '熟练' : '了解') : '了解',
    }))
    return { weight: score, sub_items: subItems }
  }

  return {
    tech_skills: makeDim('tech_skills'),
    project_exp: makeDim('project_exp'),
    soft_skills: makeDim('soft_skills'),
    domain_knowledge: makeDim('domain_knowledge'),
  }
}

export default function Dashboard() {
  const navigate = useNavigate()
  const {
    student,
    diagnosisResult,
    diagnosisHistory,
    isLoading,
    progress,
    setStudent,
    setDiagnosisResult,
    setDiagnosisHistory,
    setIsLoading,
    setProgress,
    hydrateFromStorage,
  } = useAppStore()

  const [activeTab, setActiveTab] = useState<TabKey>('profile')
  const [diagnosing, setDiagnosing] = useState(false)
  const [diagnosisError, setDiagnosisError] = useState(false)
  const [sseSteps, setSseSteps] = useState<{ label: string; status: 'wait' | 'process' | 'finish' | 'error' }[]>([])
  const [showReEval, setShowReEval] = useState(false)
  const [reEvalMsg, setReEvalMsg] = useState('')

  const staticSseSteps = [
    { label: '数据采集', status: 'wait' as const },
    { label: '能力分析', status: 'wait' as const },
    { label: '岗位匹配', status: 'wait' as const },
    { label: '路径规划', status: 'wait' as const },
    { label: '生成建议', status: 'wait' as const },
  ]

  // 执行初诊——SSE 流式接收进度并更新步骤条状态
  const runDiagnosis = useCallback(async () => {
    if (!student) return
    setDiagnosing(true)
    setDiagnosisError(false)
    setIsLoading(true)
    setSseSteps(staticSseSteps.map((s, i) => ({ ...s, status: i === 0 ? 'process' : 'wait' })))

    try {
      const result = await startDiagnosis(student.id, (stage, pct, msg) => {
        setProgress({ stage, progress: pct, message: msg })

        setSseSteps(prev => {
          const idx = prev.findIndex(s => s.label.includes(stage) || stage.includes(s.label))
          if (idx >= 0) {
            return prev.map((s, i) => ({
              ...s,
              status: i < idx ? 'finish' : i === idx ? 'process' : 'wait',
            }))
          }
          return prev
        })
      })

      setSseSteps(staticSseSteps.map(s => ({ ...s, status: 'finish' })))

      const diagResult: DiagnosisResult = {
        id: result.id || result.diagnosis_id || '',
        student_id: student.id,
        version: result.version ?? 1,
        diagnosis_type: result.diagnosis_type || 'full',
        match_score: result.match_score ?? 0,
        dimension_scores: result.dimension_scores ?? {},
        dimension_changes: result.dimension_changes ?? {},
        gap_details: result.gap_details ?? [],
        top5_jobs: result.top5_jobs ?? [],
        growth_path: result.growth_path ?? { phases: [] },
        career_advice: result.career_advice ?? '',
        ai_reasoning: result.ai_reasoning ?? {},
        trigger_event: result.trigger_event || '初始诊断',
        created_at: result.created_at || new Date().toISOString(),
      }

      setDiagnosisResult(diagResult)
      setActiveTab('profile')
    } catch (err) {
      setSseSteps(prev => prev.map(s => ({ ...s, status: s.status === 'process' ? 'error' : s.status })))
      setDiagnosisError(true)
    } finally {
      setIsLoading(false)
      setDiagnosing(false)
    }
  }, [student])

  // 执行再诊断——技能变化后重新评估
  const handleReEvaluate = useCallback(async () => {
    if (!student) return
    setShowReEval(false)
    setDiagnosing(true)
    setIsLoading(true)
    setSseSteps(staticSseSteps.map((s, i) => ({ ...s, status: i === 0 ? 'process' : 'wait' })))

    try {
      const result = await reEvaluate(student.id, '重新诊断', (stage, pct, msg) => {
        setProgress({ stage, progress: pct, message: msg })
        setSseSteps(prev => {
          const idx = prev.findIndex(s => s.label.includes(stage) || stage.includes(s.label))
          if (idx >= 0) {
            return prev.map((s, i) => ({
              ...s,
              status: i < idx ? 'finish' : i === idx ? 'process' : 'wait',
            }))
          }
          return prev
        })
      })

      setSseSteps(staticSseSteps.map(s => ({ ...s, status: 'finish' })))

      const diagResult: DiagnosisResult = {
        id: result.id || result.diagnosis_id || '',
        student_id: student.id,
        version: result.version ?? (diagnosisResult ? diagnosisResult.version + 1 : 1),
        diagnosis_type: result.diagnosis_type || 're_evaluate',
        match_score: result.match_score ?? 0,
        dimension_scores: result.dimension_scores ?? {},
        dimension_changes: result.dimension_changes ?? {},
        gap_details: result.gap_details ?? [],
        top5_jobs: result.top5_jobs ?? [],
        growth_path: result.growth_path ?? { phases: [] },
        career_advice: result.career_advice ?? '',
        ai_reasoning: result.ai_reasoning ?? {},
        trigger_event: result.trigger_event || '重新诊断',
        created_at: result.created_at || new Date().toISOString(),
      }

      if (diagnosisResult) {
        setDiagnosisHistory([...diagnosisHistory, diagnosisResult])
      }
      setDiagnosisResult(diagResult)
      setActiveTab('profile')
    } catch {
      setSseSteps(prev => prev.map(s => ({ ...s, status: s.status === 'process' ? 'error' : s.status })))
    } finally {
      setIsLoading(false)
      setDiagnosing(false)
    }
  }, [student, diagnosisResult, diagnosisHistory])

  // 学生信息就绪后自动触发诊断
  useEffect(() => {
    if (student && !diagnosisResult && !diagnosing) {
      runDiagnosis()
    }
  }, [student, diagnosisResult, diagnosing, runDiagnosis])

  // 诊断完成后加载历史记录
  useEffect(() => {
    if (student && diagnosisResult) {
      getDiagnosisHistory(student.id)
        .then((data: DiagnosisResult[]) => setDiagnosisHistory(data))
        .catch(() => {})
    }
  }, [student, diagnosisResult])

  useEffect(() => {
    if (!student) {
      hydrateFromStorage()
      const storedId = localStorage.getItem('student_id')
      if (storedId) {
        getStudent(storedId).then(data => setStudent(data))
          .then(() => getDiagnosisHistory(storedId))
          .then((history: any[]) => {
            if (history.length > 0) {
              setDiagnosisResult(history[0])
              setDiagnosisHistory(history)
            }
          })
          .catch(() => {
            localStorage.removeItem('student_id')
            localStorage.removeItem('student_data')
          })
      }
    }
  }, [])

  if (!student) {
    return (
      <div style={{
        minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: 'var(--bg-card)',
      }}>
        <div style={{ textAlign: 'center' }}>
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="var(--accent-amber)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <div style={{ marginTop: 16, fontSize: 18, fontWeight: 600, color: 'var(--text-primary)', fontFamily: 'var(--font-display)' }}>
            请先填写个人信息
          </div>
          <div style={{ marginTop: 8, fontSize: 13, color: 'var(--text-secondary)', marginBottom: 24 }}>
            完善你的教育背景和目标岗位，AI 才能为你提供精准诊断
          </div>
          <button
            onClick={() => navigate('/input')}
            style={{
              padding: '10px 32px', borderRadius: 8, border: 'none',
              background: 'var(--accent-blue)', color: '#fff',
              cursor: 'pointer', fontSize: 14, fontWeight: 600,
              fontFamily: 'var(--font-display)', letterSpacing: '0.5px',
              transition: 'all 0.25s ease',
            }}
            onMouseEnter={e => { e.currentTarget.style.boxShadow = '0 0 20px rgba(91,156,245,0.4)'; e.currentTarget.style.transform = 'scale(1.03)' }}
            onMouseLeave={e => { e.currentTarget.style.boxShadow = ''; e.currentTarget.style.transform = '' }}
          >
            前往填写
          </button>
        </div>
      </div>
    )
  }

  const profile = diagnosisResult ? buildProfile(diagnosisResult, student) : null
  const previousScore = diagnosisHistory.length > 0
    ? diagnosisHistory[diagnosisHistory.length - 1].match_score
    : undefined

  // 根据当前状态渲染对应内容——加载中/空状态/Tab 内容
  const renderTabContent = () => {
    if (diagnosing || (isLoading && !diagnosisResult)) {
      return (
        <div style={{ padding: '32px 24px' }}>
          <div style={{
            textAlign: 'center', color: 'var(--text-secondary)',
            fontSize: 14, fontFamily: 'var(--font-display)', marginBottom: 8,
          }}>
            AI 正在分析你的能力画像...
          </div>
          <ProgressSteps steps={sseSteps.length > 0 ? sseSteps : staticSseSteps} />
          {progress.message && (
            <div style={{
              textAlign: 'center', marginTop: 8,
              fontSize: 12, color: 'var(--text-tertiary)',
              fontFamily: 'var(--font-mono)',
            }}>
              {progress.message}
            </div>
          )}
        </div>
      )
    }

    if (diagnosisError) {
      return (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '60px 24px' }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 40, marginBottom: 16 }}>⚠️</div>
            <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', fontFamily: 'var(--font-display)', marginBottom: 8 }}>
              诊断遇到问题
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 24 }}>
              请检查网络连接后重试
            </div>
            <button
              onClick={() => { setDiagnosisError(false); runDiagnosis() }}
              style={{
                padding: '10px 32px', borderRadius: 8, border: 'none',
                background: 'var(--accent-blue)', color: '#fff',
                cursor: 'pointer', fontSize: 14, fontWeight: 600,
                fontFamily: 'var(--font-display)', letterSpacing: '0.5px',
                transition: 'all 0.25s ease',
              }}
              onMouseEnter={e => { e.currentTarget.style.boxShadow = '0 0 20px rgba(91,123,181,0.4)'; e.currentTarget.style.transform = 'scale(1.03)' }}
              onMouseLeave={e => { e.currentTarget.style.boxShadow = ''; e.currentTarget.style.transform = '' }}
            >
              重新诊断
            </button>
          </div>
        </div>
      )
    }

    if (!diagnosisResult) {
      return (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '60px 24px' }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{
              fontSize: 16, fontWeight: 600, color: 'var(--text-primary)',
              fontFamily: 'var(--font-display)', marginBottom: 8,
            }}>
              准备就绪
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 24 }}>
              {student.name}，请点击下方按钮开始 AI 诊断分析
            </div>
            <button
              onClick={runDiagnosis}
              style={{
                padding: '10px 32px', borderRadius: 8, border: 'none',
                background: 'var(--accent-blue)', color: '#fff',
                cursor: 'pointer', fontSize: 14, fontWeight: 600,
                fontFamily: 'var(--font-display)', letterSpacing: '0.5px',
                transition: 'all 0.25s ease',
              }}
              onMouseEnter={e => { e.currentTarget.style.boxShadow = '0 0 20px rgba(91,156,245,0.4)'; e.currentTarget.style.transform = 'scale(1.03)' }}
              onMouseLeave={e => { e.currentTarget.style.boxShadow = ''; e.currentTarget.style.transform = '' }}
            >
              开始诊断
            </button>
          </div>
        </div>
      )
    }

    switch (activeTab) {
      case 'profile':
        return (
          <ProfileTab
            profile={profile!}
            changes={diagnosisResult.dimension_changes}
          />
        )
      case 'match':
        return (
          <MatchTab
            matchScore={diagnosisResult.match_score}
            previousScore={previousScore}
            dimensionScores={diagnosisResult.dimension_scores}
            top5Jobs={diagnosisResult.top5_jobs}
            gapDetails={diagnosisResult.gap_details}
          />
        )
      case 'path':
        return (
          <PathTab
            growthPath={diagnosisResult.growth_path}
            diagnosisId={diagnosisResult.id}
            studentId={student?.id ?? ''}
            onTaskComplete={(taskId) => {
              setReEvalMsg('任务已完成，是否需要重新评估当前能力水平？')
              setShowReEval(true)
            }}
          />
        )
      case 'advice':
        return (
          <AdviceTab
            careerAdvice={diagnosisResult.career_advice}
            aiReasoning={diagnosisResult.ai_reasoning}
            recommendedDirections={diagnosisResult.top5_jobs?.slice(0, 3).map(j => j.title)}
          />
        )
      case 'recommend':
        return (
          <RecommendTab top5Jobs={diagnosisResult.top5_jobs} />
        )
      case 'growth':
        return (
          <GrowthTab
            history={diagnosisHistory.length > 0 ? diagnosisHistory : [diagnosisResult]}
          />
        )
      default:
        return null
    }
  }

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', flexDirection: 'column',
      background: 'var(--bg-card)',
    }}>
      {/* 顶部导航栏——返回、学生信息、重新诊断 */}
      <header style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '12px 24px',
        background: 'var(--bg-hover)',
        borderBottom: '1px solid var(--border-light)',
        flexShrink: 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <button
            onClick={() => navigate('/input')}
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '6px 12px', borderRadius: 6,
              border: '1px solid var(--border-light)',
              background: 'transparent', color: 'var(--text-secondary)',
              cursor: 'pointer', fontSize: 12, fontWeight: 500,
              fontFamily: 'var(--font-display)',
              transition: 'all 0.2s ease',
            }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--accent-blue)'; e.currentTarget.style.color = 'var(--accent-blue)' }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border-light)'; e.currentTarget.style.color = 'var(--text-secondary)' }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="15 18 9 12 15 6"/>
            </svg>
            返回
          </button>
          <span style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', fontFamily: 'var(--font-display)', letterSpacing: '1px' }}>
            职达
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
          <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
            学生：<span style={{ color: 'var(--text-primary)', fontWeight: 600, fontFamily: 'var(--font-display)' }}>{student.name}</span>
          </span>
          <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
            目标：<span style={{ color: 'var(--accent-teal)', fontWeight: 600, fontFamily: 'var(--font-display)' }}>{student.target_job || '未设置'}</span>
          </span>
        </div>
        <button
          onClick={() => { setReEvalMsg('是否基于当前成长数据重新进行诊断评估？'); setShowReEval(true) }}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            padding: '7px 18px', borderRadius: 6,
            border: '1px solid var(--accent-blue)',
            background: 'rgba(91,156,245,0.1)',
            color: 'var(--accent-blue)', cursor: 'pointer',
            fontSize: 12, fontWeight: 600,
            fontFamily: 'var(--font-display)', letterSpacing: '0.5px',
            transition: 'all 0.25s ease',
          }}
          onMouseEnter={e => { e.currentTarget.style.background = 'rgba(91,156,245,0.2)'; e.currentTarget.style.boxShadow = '0 0 14px rgba(91,156,245,0.2)' }}
          onMouseLeave={e => { e.currentTarget.style.background = 'rgba(91,156,245,0.1)'; e.currentTarget.style.boxShadow = '' }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="23 4 23 10 17 10"/>
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
          </svg>
          重新诊断
        </button>
      </header>

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* 左侧 Tab 导航 */}
        <nav style={{
          width: 140, flexShrink: 0, minWidth: 140,
          display: 'flex', flexDirection: 'column',
          borderRight: '1px solid var(--border-light)',
          background: 'var(--bg-hover)',
        }}>
          {TABS.map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              style={{
                textAlign: 'left',
                padding: '14px 16px',
                border: 'none',
                background: activeTab === tab.key ? 'var(--bg-card)' : 'transparent',
                color: activeTab === tab.key ? 'var(--text-primary)' : 'var(--text-tertiary)',
                cursor: 'pointer',
                fontSize: 13,
                fontWeight: activeTab === tab.key ? 600 : 400,
                fontFamily: 'var(--font-display)',
                borderLeft: activeTab === tab.key ? '3px solid var(--accent-blue)' : '3px solid transparent',
                transition: 'all 0.2s ease',
              }}
              onMouseEnter={e => { if (activeTab !== tab.key) { e.currentTarget.style.color = 'var(--text-secondary)'; e.currentTarget.style.background = 'rgba(248, 247, 244,0.6)' } }}
              onMouseLeave={e => { if (activeTab !== tab.key) { e.currentTarget.style.color = 'var(--text-tertiary)'; e.currentTarget.style.background = 'transparent' } }}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        <main style={{
          flex: 1,
          overflow: 'auto',
          padding: '24px',
        }}>
          <div style={{ maxWidth: 1200, margin: '0 auto' }}>
            {renderTabContent()}
          </div>
        </main>
      </div>

      {diagnosisResult && (
        <ExportToolbar studentId={student.id} diagnosisId={diagnosisResult.id} version={diagnosisResult.version} />
      )}

      <ReEvaluatePrompt
        visible={showReEval}
        message={reEvalMsg}
        onReEvaluate={handleReEvaluate}
        onDismiss={() => setShowReEval(false)}
      />
    </div>
  )
}
