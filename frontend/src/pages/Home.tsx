// 职达首页——左侧大标题排版 + 右侧抽象几何图形 + 底部功能导航条
import { useNavigate } from 'react-router-dom'
import { useEffect, useState } from 'react'

// 五大核心功能介绍
const features = [
  { label: '能力画像', accent: 'var(--accent-blue)' },
  { label: '岗位匹配', accent: 'var(--accent-teal)' },
  { label: '成长路径', accent: 'var(--accent-amber)' },
  { label: '职业建议', accent: 'var(--accent-violet)' },
  { label: '动态追踪', accent: 'var(--accent-rose)' },
]

// 右侧浮动几何图形配置——半透明圆/椭圆，三种异步漂移动画
const shapes = [
  { size: 180, x: 160, y: 80, color: 'rgba(91,123,181,0.12)', rx: 90 },
  { size: 120, x: 280, y: 200, color: 'rgba(90,158,143,0.10)', rx: 60 },
  { size: 96, x: 100, y: 260, color: 'rgba(196,148,74,0.08)', rx: 48 },
  { size: 200, x: 220, y: 20, color: 'rgba(139,126,200,0.07)', rx: 100 },
  { size: 64, x: 340, y: 300, color: 'rgba(196,122,139,0.09)', rx: 32 },
  { size: 140, x: 50, y: 140, color: 'rgba(91,123,181,0.06)', rx: 70 },
]

export default function Home() {
  const navigate = useNavigate()
  const [hasExistingSession, setHasExistingSession] = useState(false)

  useEffect(() => {
    const sid = localStorage.getItem('student_id')
    if (sid) setHasExistingSession(true)
  }, [])

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-page)', overflow: 'hidden' }}>
      {/* 顶部导航栏 */}
      <nav style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '20px 56px', position: 'relative', zIndex: 100,
      }}>
        <div style={{ fontFamily: 'var(--font-display)', fontSize: 24, fontWeight: 700, letterSpacing: '0.06em', color: 'var(--text-primary)' }}>
          职达
        </div>
        <button className="btn btn-primary" onClick={() => navigate('/input')} style={{ padding: '10px 28px', fontSize: 15, borderRadius: 'var(--radius-md)' }}>
          开始诊断
        </button>
      </nav>

      {/* 主视觉区：标题 + 描述 + CTA 按钮 */}
      <section style={{
        display: 'flex', alignItems: 'center', minHeight: 'calc(100vh - 76px)', flexWrap: 'wrap',
        maxWidth: 1200, margin: '0 auto', padding: '0 56px', position: 'relative',
      }}>
        {/* Left: Typography */}
        <div style={{ flex: '0 0 480px', zIndex: 10, paddingRight: 40, maxWidth: '100%' }}>
          <h1 style={{
            fontFamily: 'var(--font-display)', fontSize: 'clamp(40px, 8vw, 80px)', fontWeight: 700,
            lineHeight: 1.05, letterSpacing: '0.02em', marginBottom: 20,
            color: 'var(--text-primary)',
            animation: 'fadeIn 0.8s ease-out',
          }}>
            你的职业<br />成长伙伴
          </h1>

          <p style={{
            fontSize: 17, lineHeight: 1.8, color: 'var(--text-secondary)',
            maxWidth: 380, marginBottom: 40, fontWeight: 400,
            animation: 'slideUp 0.8s ease-out 0.15s both',
          }}>
            上传简历，AI 为你生成能力画像、岗位匹配与成长路径
          </p>

          <div style={{ animation: 'slideUp 0.8s ease-out 0.3s both' }}>
            <button
              className="btn btn-primary btn-lg"
              onClick={() => navigate('/input')}
              style={{ fontSize: 17, padding: '16px 40px', borderRadius: 12 }}
            >
              上传简历，开始诊断
            </button>
          </div>
          {hasExistingSession && (
            <div style={{ marginTop: 12, animation: 'slideUp 0.8s ease-out 0.4s both' }}>
              <button
                className="btn btn-ghost"
                onClick={() => navigate('/dashboard')}
                style={{ fontSize: 14, padding: '10px 24px' }}
              >
                继续上次诊断 →
              </button>
            </div>
          )}
        </div>

        {/* Right: Abstract Geometry */}
        <div style={{
          flex: 1, position: 'relative', height: 520, minWidth: 300,
          animation: 'fadeIn 1s ease-out 0.3s both',
        }}>
          <style>{`
            @keyframes floatShape1 { 0%,100% { transform: translate(0,0); } 33% { transform: translate(8px,-12px); } 66% { transform: translate(-4px,8px); } }
            @keyframes floatShape2 { 0%,100% { transform: translate(0,0); } 33% { transform: translate(-10px,6px); } 66% { transform: translate(6px,-10px); } }
            @keyframes floatShape3 { 0%,100% { transform: translate(0,0); } 33% { transform: translate(4px,-8px); } 66% { transform: translate(-8px,4px); } }
          `}</style>
          {shapes.map((s, i) => (
            <div key={i} style={{
              position: 'absolute',
              left: s.x, top: s.y,
              width: s.size, height: s.size,
              borderRadius: `${s.rx}px`,
              background: s.color,
              animation: `floatShape${(i % 3) + 1} ${6 + i * 1.5}s ease-in-out infinite`,
            }} />
          ))}

          {/* Central accent circle */}
          <div style={{
            position: 'absolute', left: 180, top: 110, width: 160, height: 160,
            borderRadius: '50%',
            border: '1.5px solid rgba(91,123,181,0.25)',
            animation: 'floatShape2 8s ease-in-out infinite',
          }} />
          <div style={{
            position: 'absolute', left: 196, top: 126, width: 128, height: 128,
            borderRadius: '50%',
            border: '1px solid rgba(90,158,143,0.2)',
            animation: 'floatShape1 7s ease-in-out infinite 1s',
          }} />
          <div style={{
            position: 'absolute', left: 212, top: 142, width: 96, height: 96,
            borderRadius: '50%',
            background: 'rgba(91,123,181,0.06)',
            border: '1px solid rgba(196,148,74,0.15)',
            animation: 'floatShape3 9s ease-in-out infinite 2s',
          }} />
        </div>
      </section>

      {/* 功能标签导航条，hover 变色 */}
      <div style={{
        display: 'flex', justifyContent: 'center', gap: 0,
        padding: '0 56px 80px', maxWidth: 1200, margin: '0 auto',
        animation: 'slideUp 0.8s ease-out 0.6s both',
      }}>
        {features.map((f, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center' }}>
            {i > 0 && (
              <span style={{
                width: 4, height: 4, borderRadius: '50%',
                background: 'var(--border-light)', margin: '0 20px',
              }} />
            )}
            <a
              href="/input"
              style={{
                textDecoration: 'none', color: 'var(--text-secondary)',
                fontSize: 14, fontWeight: 500, transition: 'color 0.25s',
                whiteSpace: 'nowrap',
              }}
              onMouseEnter={e => { e.currentTarget.style.color = f.accent }}
              onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-secondary)' }}
            >
              {f.label}
            </a>
          </div>
        ))}
      </div>
    </div>
  )
}
