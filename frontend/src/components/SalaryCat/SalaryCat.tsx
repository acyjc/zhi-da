// 职达小喵桌宠——纯CSS橙色虎斑猫 + 点击展开LLM对话面板
import { useState, useRef, useEffect } from 'react'
import axios from 'axios'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

const QUICK_REPLIES = [
  '怎么提升Python技能？',
  '我的简历怎么写？',
  '适合做什么岗位？',
  '面试要注意什么？',
]

export default function SalaryCat() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: '你好喵~ 我是职达小喵！有什么职业成长的问题可以问我喵~' },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [blinking, setBlinking] = useState(false)
  const messagesEnd = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const interval = setInterval(() => {
      setBlinking(true)
      setTimeout(() => setBlinking(false), 150)
    }, 3000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async (text: string) => {
    if (!text.trim() || loading) return
    const userMsg: Message = { role: 'user', content: text }
    const newMessages = [...messages, userMsg]
    setMessages(newMessages)
    setInput('')
    setLoading(true)
    try {
      const res = await axios.post('/api/chat', {
        messages: newMessages.map(m => ({ role: m.role, content: m.content })),
      })
      setMessages(prev => [...prev, { role: 'assistant', content: res.data.reply }])
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: '喵…网络不太好，稍后再试试吧~' }])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send(input)
    }
  }

  return (
    <>
      {/* 对话面板——消息列表+快捷提问+输入框 */}
      {open && (
        <div style={{
          position: 'fixed', bottom: 120, right: 24, width: 'min(340px, calc(100vw - 48px))', height: 440, zIndex: 9998,
          background: 'var(--bg-card)', borderRadius: 18, border: '1px solid var(--border-light)',
          boxShadow: 'var(--shadow-md)', display: 'flex', flexDirection: 'column',
          overflow: 'hidden', animation: 'slideUp 0.3s ease-out',
        }}>
          {/* Header */}
          <div style={{
            padding: '14px 18px', borderBottom: '1px solid var(--border-light)',
            background: 'linear-gradient(135deg, #fef7ed, #fff8f0)',
            display: 'flex', alignItems: 'center', gap: 10,
          }}>
            <div style={{ width: 36, height: 36, borderRadius: '50%', background: '#f5a623', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 20, flexShrink: 0 }}>
              🐱
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 700, fontSize: 15, color: 'var(--text-primary)' }}>职达小喵</div>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>你的职业成长伙伴</div>
            </div>
            <button onClick={() => setOpen(false)} style={{ background: 'none', border: 'none', fontSize: 18, cursor: 'pointer', color: 'var(--text-tertiary)', padding: 4 }}>
              ✕
            </button>
          </div>

          {/* Messages */}
          <div style={{ flex: 1, overflow: 'auto', padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 10 }}>
            {messages.map((msg, i) => (
              <div key={i} style={{
                display: 'flex', alignItems: 'flex-end', gap: 8,
                flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
              }}>
                {msg.role === 'assistant' && (
                  <div style={{ width: 28, height: 28, borderRadius: '50%', background: '#fef7ed', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, flexShrink: 0, border: '1px solid #f0d9a0' }}>
                    🐱
                  </div>
                )}
                <div style={{
                  maxWidth: '80%', padding: '10px 14px', borderRadius: msg.role === 'user' ? '14px 14px 4px 14px' : '14px 14px 14px 4px',
                  background: msg.role === 'user' ? 'var(--accent-blue)' : '#f8f7f4',
                  color: msg.role === 'user' ? '#fff' : 'var(--text-primary)',
                  fontSize: 13, lineHeight: 1.6, wordBreak: 'break-word',
                }}>
                  {msg.content}
                </div>
              </div>
            ))}
            {loading && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{ width: 28, height: 28, borderRadius: '50%', background: '#fef7ed', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, border: '1px solid #f0d9a0' }}>🐱</div>
                <div style={{ display: 'flex', gap: 4, padding: '10px 14px', background: '#f8f7f4', borderRadius: '14px 14px 14px 4px' }}>
                  {[0, 1, 2].map(i => (
                    <div key={i} style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--text-tertiary)', animation: `blink 1.4s ${i * 0.2}s infinite` }} />
                  ))}
                  <style>{`@keyframes blink { 0%,80%,100% { opacity: 0.2 } 40% { opacity: 1 } }`}</style>
                </div>
              </div>
            )}
            <div ref={messagesEnd} />
          </div>

          {/* 快捷问题按钮 */}
          {messages.length <= 1 && (
            <div style={{ padding: '0 16px 8px', display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {QUICK_REPLIES.map(q => (
                <button key={q} onClick={() => send(q)}
                  style={{ padding: '4px 10px', borderRadius: 12, border: '1px solid var(--border-light)', background: '#fff', cursor: 'pointer', fontSize: 12, color: 'var(--text-secondary)', whiteSpace: 'nowrap', transition: 'border-color 0.2s' }}
                  onMouseEnter={e => (e.currentTarget.style.borderColor = 'var(--accent-amber)')}
                  onMouseLeave={e => (e.currentTarget.style.borderColor = 'var(--border-light)')}
                >{q}</button>
              ))}
            </div>
          )}

          {/* Input */}
          <div style={{ padding: '10px 14px', borderTop: '1px solid var(--border-light)', display: 'flex', gap: 8 }}>
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="问问小喵..."
              style={{ flex: 1, border: '1px solid var(--border-light)', borderRadius: 20, padding: '8px 14px', fontSize: 13, outline: 'none', background: '#fafaf8', color: 'var(--text-primary)', }}
              onFocus={e => (e.target.style.borderColor = 'var(--accent-amber)')}
              onBlur={e => (e.target.style.borderColor = 'var(--border-light)')}
            />
            <button onClick={() => send(input)} disabled={loading || !input.trim()}
              style={{ width: 36, height: 36, borderRadius: '50%', border: 'none', background: input.trim() ? 'var(--accent-amber)' : 'var(--border-light)', color: '#fff', fontSize: 16, cursor: input.trim() ? 'pointer' : 'default', display: 'flex', alignItems: 'center', justifyContent: 'center', transition: 'background 0.2s', flexShrink: 0 }}>
              ➤
            </button>
          </div>
        </div>
      )}

      {/* Cat Button */}
      <div onClick={() => setOpen(!open)} title="点击和职达小喵聊天" style={{ position: 'fixed', bottom: 24, right: 24, zIndex: 9999, cursor: 'pointer', userSelect: 'none' }}>
        {/* 猫身动画：浮动/呼吸/眨眼/耳朵抽动/尾巴摇摆 */}
        <style>{`
          @keyframes catBounce { 0%,100% { transform: translateY(0); } 30% { transform: translateY(-8px); } 50% { transform: translateY(0); } 70% { transform: translateY(-4px); } }
          @keyframes catSleep { 0%,100% { transform: translateY(0) scale(1); } 50% { transform: translateY(2px) scale(0.97); } }
          @keyframes earTwitch { 0%,90%,100% { transform: rotate(0deg); } 95% { transform: rotate(-8deg); } }
          @keyframes tailWag { 0%,100% { transform: rotate(0deg); } 25% { transform: rotate(15deg); } 75% { transform: rotate(-15deg); } }
          @keyframes catFloat { 0%,100% { transform: translateY(0) rotate(0deg); } 25% { transform: translateY(-3px) rotate(1deg); } 75% { transform: translateY(-3px) rotate(-1deg); } }
          .cat-wrapper:hover .cat-body { animation: catBounce 0.6s ease-in-out !important; }
          .cat-wrapper:hover { filter: drop-shadow(0 0 12px rgba(245,166,35,0.3)); }
        `}</style>

        <div className="cat-wrapper" style={{ width: 80, height: 80, position: 'relative', animation: 'catFloat 4s ease-in-out infinite' }}>
          {/* Body shadow */}
          <div style={{ position: 'absolute', bottom: 0, left: '50%', transform: 'translateX(-50%)', width: 56, height: 6, borderRadius: '50%', background: 'rgba(0,0,0,0.06)' }} />

          {/* 猫身体——橙色主体+浅色肚子+摇摆尾巴 */}
          <div className="cat-body" style={{ position: 'absolute', bottom: 4, left: 14, width: 52, height: 46, borderRadius: '50% 50% 45% 45%', background: '#f5a623', boxShadow: 'inset 0 4px 8px rgba(255,255,255,0.2)', animation: 'catSleep 6s ease-in-out infinite' }}>
            {/* Belly */}
            <div style={{ position: 'absolute', bottom: 6, left: 10, width: 32, height: 24, borderRadius: '50%', background: '#fef3d5' }} />

            {/* Tail */}
            <div style={{ position: 'absolute', right: -16, bottom: 20, width: 22, height: 8, borderRadius: '0 10px 10px 0', background: '#f5a623', transformOrigin: 'left center', animation: 'tailWag 2s ease-in-out infinite' }}>
              <div style={{ position: 'absolute', right: -6, top: -3, width: 10, height: 10, borderRadius: '50%', background: '#e8961a' }} />
            </div>

            {/* Left paw */}
            <div style={{ position: 'absolute', bottom: 2, left: 6, width: 14, height: 10, borderRadius: '50%', background: '#f5a623' }} />
            {/* Right paw */}
            <div style={{ position: 'absolute', bottom: 2, right: 6, width: 14, height: 10, borderRadius: '50%', background: '#f5a623' }} />
          </div>

          {/* 猫头——三角耳朵+额头条纹+圆眼高光+鼻子腮红 */}
          <div style={{ position: 'absolute', top: 0, left: 10, width: 60, height: 54, borderRadius: '50%', background: '#f5a623', boxShadow: 'inset 0 4px 8px rgba(255,255,255,0.15)' }}>
            {/* Left ear */}
            <div style={{ position: 'absolute', top: -10, left: 4, width: 0, height: 0, borderLeft: '10px solid transparent', borderRight: '10px solid transparent', borderBottom: '22px solid #f5a623', animation: 'earTwitch 4s ease-in-out infinite' }}>
              <div style={{ position: 'absolute', top: 8, left: -6, width: 0, height: 0, borderLeft: '6px solid transparent', borderRight: '6px solid transparent', borderBottom: '14px solid #fbcb8e' }} />
            </div>
            {/* Right ear */}
            <div style={{ position: 'absolute', top: -10, right: 4, width: 0, height: 0, borderLeft: '10px solid transparent', borderRight: '10px solid transparent', borderBottom: '22px solid #f5a623', animation: 'earTwitch 4s ease-in-out infinite 2s' }}>
              <div style={{ position: 'absolute', top: 8, left: -6, width: 0, height: 0, borderLeft: '6px solid transparent', borderRight: '6px solid transparent', borderBottom: '14px solid #fbcb8e' }} />
            </div>

            {/* Forehead stripes */}
            <div style={{ position: 'absolute', top: 14, left: 16, width: 28, height: 3, borderRadius: 2, background: '#e08e1a', transform: 'rotate(-2deg)' }} />
            <div style={{ position: 'absolute', top: 19, left: 18, width: 24, height: 3, borderRadius: 2, background: '#e08e1a' }} />
            <div style={{ position: 'absolute', top: 24, left: 20, width: 20, height: 3, borderRadius: 2, background: '#e08e1a', transform: 'rotate(2deg)' }} />

            {/* Eyes */}
            <div style={{ position: 'absolute', top: 22, left: 12 }}>
              <div style={{ width: 12, height: blinking ? 3 : 14, borderRadius: blinking ? 2 : '50%', background: '#2c2c2c', transition: 'height 0.05s', overflow: 'hidden' }}>
                {!blinking && <div style={{ width: 4, height: 4, borderRadius: '50%', background: '#fff', position: 'absolute', top: 3, left: 3 }} />}
              </div>
            </div>
            <div style={{ position: 'absolute', top: 22, right: 12 }}>
              <div style={{ width: 12, height: blinking ? 3 : 14, borderRadius: blinking ? 2 : '50%', background: '#2c2c2c', transition: 'height 0.05s', overflow: 'hidden' }}>
                {!blinking && <div style={{ width: 4, height: 4, borderRadius: '50%', background: '#fff', position: 'absolute', top: 3, left: 3 }} />}
              </div>
            </div>

            {/* Nose */}
            <div style={{ position: 'absolute', top: 34, left: '50%', transform: 'translateX(-50%)', width: 8, height: 6, borderRadius: '50%', background: '#e08e1a' }} />
            {/* Mouth */}
            <div style={{ position: 'absolute', top: 40, left: 26, width: 8, height: 4, borderBottom: '2px solid #cc8818', borderRadius: '0 0 50% 50%' }} />

            {/* Cheeks */}
            <div style={{ position: 'absolute', top: 30, left: 4, width: 8, height: 5, borderRadius: '50%', background: 'rgba(255,200,150,0.4)' }} />
            <div style={{ position: 'absolute', top: 30, right: 4, width: 8, height: 5, borderRadius: '50%', background: 'rgba(255,200,150,0.4)' }} />
          </div>
        </div>
      </div>
    </>
  )
}
