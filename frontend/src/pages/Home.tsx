// 职达三端协同入口——多端导航大厅
import { useNavigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { useAppStore } from '../stores/appStore'
import ThemeToggle from '../components/shared/ThemeToggle'
import { GraduationCap, Briefcase, Shield, Target } from 'lucide-react'

export default function Home() {
  const navigate = useNavigate()
  const [hasExistingSession, setHasExistingSession] = useState(false)
  const { hydrateFromStorage, setRole } = useAppStore()

  useEffect(() => {
    hydrateFromStorage()
    const sid = localStorage.getItem('student_id')
    if (sid) setHasExistingSession(true)
  }, [])

  const enterPortal = (role: 'student' | 'enterprise' | 'admin') => {
    setRole(role)
    if (role === 'student') {
      const sid = localStorage.getItem('student_id')
      if (sid) {
        navigate('/student/dashboard')
      } else {
        navigate('/student/input')
      }
    } else if (role === 'enterprise') {
      navigate('/enterprise')
    } else if (role === 'admin') {
      navigate('/admin')
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--bg-page)',
      transition: 'background-color 0.3s, color 0.3s',
      color: 'var(--text-primary)',
      display: 'flex',
      flexDirection: 'column',
    }}>
      {/* Header Navigation */}
      <nav style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '24px 56px',
      }}>
        <div style={{
          fontFamily: 'var(--font-display)',
          fontSize: 24,
          fontWeight: 800,
          letterSpacing: '0.04em',
          color: 'var(--text-primary)',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}>
          <Target size={24} />
          <span>职达 AI</span>
        </div>

        <ThemeToggle />
      </nav>

      {/* Main Layout */}
      <main style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px 48px 80px',
      }}>
        {/* Portal Title */}
        <div style={{ textAlign: 'center', marginBottom: 48, animation: 'slideUp 0.6s ease-out' }}>
          <h1 style={{
            fontSize: 'clamp(28px, 4vw, 42px)',
            fontWeight: 800,
            lineHeight: 1.2,
            letterSpacing: '-0.02em',
            margin: '0 0 12px 0',
            background: 'linear-gradient(135deg, var(--text-primary) 30%, var(--accent-teal) 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}>
            职达三端协同平台
          </h1>
          <p style={{
            fontSize: 'clamp(14px, 1.8vw, 16px)',
            color: 'var(--text-secondary)',
            maxWidth: 600,
            margin: '0 auto',
            lineHeight: 1.6,
          }}>
            基于 AI 职业成长智能体的精准校企协同闭环服务系统
          </p>
        </div>

        {/* Portal Grid */}
        <div style={{
          display: 'flex',
          gap: 24,
          width: '100%',
          maxWidth: 1120,
          flexWrap: 'wrap',
          justifyContent: 'center',
          animation: 'slideUp 0.8s ease-out 0.1s both',
        }}>
          {/* Card 1: Student */}
          <div
            className="glass-panel portal-card portal-card-student"
            onClick={() => enterPortal('student')}
            style={{
              flex: '1 1 320px',
              maxWidth: 360,
              padding: '40px 32px',
              borderRadius: 20,
              background: 'var(--bg-card)',
              border: '1px solid var(--border-light)',
              boxShadow: 'var(--shadow-sm)',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              gap: 20,
            }}
          >
            <div style={{
              width: 56, height: 56, borderRadius: 16,
              background: 'rgba(91, 123, 181, 0.1)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: 'var(--accent-blue)',
            }}>
              <GraduationCap size={26} />
            </div>
            <div>
              <h3 style={{ fontSize: 19, fontWeight: 700, margin: '0 0 8px 0', color: 'var(--text-primary)' }}>学生端 (Student)</h3>
              <p style={{ fontSize: 13, lineHeight: 1.7, color: 'var(--text-secondary)', margin: 0 }}>
                上传简历，通过 AI 深度解析诊断，生成全维度能力画像，获取岗位匹配与成长学习路径，并可一键授权画像给意向招聘岗位。
              </p>
            </div>
            <div style={{
              marginTop: 'auto',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              fontSize: 14,
              fontWeight: 700,
              color: 'var(--accent-blue)',
            }}>
              <span>{hasExistingSession ? '继续上次诊断' : '开始 AI 职业诊断'}</span>
              <span>→</span>
            </div>
          </div>

          {/* Card 2: Enterprise */}
          <div
            className="glass-panel portal-card portal-card-enterprise"
            onClick={() => enterPortal('enterprise')}
            style={{
              flex: '1 1 320px',
              maxWidth: 360,
              padding: '40px 32px',
              borderRadius: 20,
              background: 'var(--bg-card)',
              border: '1px solid var(--border-light)',
              boxShadow: 'var(--shadow-sm)',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              gap: 20,
            }}
          >
            <div style={{
              width: 56, height: 56, borderRadius: 16,
              background: 'rgba(20, 184, 166, 0.1)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: 'var(--accent-teal)',
            }}>
              <Briefcase size={26} />
            </div>
            <div>
              <h3 style={{ fontSize: 19, fontWeight: 700, margin: '0 0 8px 0', color: 'var(--text-primary)' }}>企业端 (Enterprise)</h3>
              <p style={{ fontSize: 13, lineHeight: 1.7, color: 'var(--text-secondary)', margin: 0 }}>
                入驻学校双选网络，提交招聘岗位并由 AI 自动提取 JD 技能要求特征，查看获得已授权学生的能力画像，快速匹配精准人才。
              </p>
            </div>
            <div style={{
              marginTop: 'auto',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              fontSize: 14,
              fontWeight: 700,
              color: 'var(--accent-teal)',
            }}>
              <span>进入企业工作台</span>
              <span>→</span>
            </div>
          </div>

          {/* Card 3: School Admin */}
          <div
            className="glass-panel portal-card portal-card-admin"
            onClick={() => enterPortal('admin')}
            style={{
              flex: '1 1 320px',
              maxWidth: 360,
              padding: '40px 32px',
              borderRadius: 20,
              background: 'var(--bg-card)',
              border: '1px solid var(--border-light)',
              boxShadow: 'var(--shadow-sm)',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              gap: 20,
            }}
          >
            <div style={{
              width: 56, height: 56, borderRadius: 16,
              background: 'rgba(245, 158, 11, 0.1)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: 'var(--accent-amber)',
            }}>
              <Shield size={26} />
            </div>
            <div>
              <h3 style={{ fontSize: 19, fontWeight: 700, margin: '0 0 8px 0', color: 'var(--text-primary)' }}>学校后台 (Admin)</h3>
              <p style={{ fontSize: 13, lineHeight: 1.7, color: 'var(--text-secondary)', margin: 0 }}>
                教务管理端。审核入驻企业名单与发布的岗位详情，审核 AI 岗位能力建模合理性，统计并跟踪全校学生的诊断画像指标及进展。
              </p>
            </div>
            <div style={{
              marginTop: 'auto',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              fontSize: 14,
              fontWeight: 700,
              color: 'var(--accent-amber)',
            }}>
              <span>进入教务后台</span>
              <span>→</span>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
