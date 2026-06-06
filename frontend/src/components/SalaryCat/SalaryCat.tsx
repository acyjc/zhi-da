// 职达小助手桌宠——「月薪喵」视频桌宠 + 点击展开LLM对话面板
import { useState, useRef, useEffect } from 'react'
import { useAppStore } from '../../stores/appStore'
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
    { role: 'assistant', content: '你好喵~ 我是您的求职伴侣「小达」！有什么职业成长的问题可以问我喵~' },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEnd = useRef<HTMLDivElement>(null)
  
  const [petPosition, setPetPosition] = useState({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState(false)
  const petRef = useRef<HTMLDivElement>(null)
  const dragState = useRef({ dragging: false, startX: 0, startY: 0, offsetX: 0, offsetY: 0 })

  const { theme } = useAppStore()

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    const handler = (e: Event) => {
      const customEvent = e as CustomEvent
      if (customEvent.detail) {
        setMessages(prev => [...prev, { role: 'assistant', content: customEvent.detail }])
        setOpen(true)
      }
    }
    window.addEventListener('salarycat-message', handler)
    return () => window.removeEventListener('salarycat-message', handler)
  }, [])

  // Initialize pet position (bottom-right) and handle dragging
  useEffect(() => {
    const calcPosition = () => ({
      x: Math.max(0, window.innerWidth - 104),
      y: Math.max(0, window.innerHeight - 104),
    })

    const initial = calcPosition()
    petRef.current?.style.setProperty('left', `${initial.x}px`)
    petRef.current?.style.setProperty('top', `${initial.y}px`)
    setPetPosition(initial)

    const onPointerMove = (e: PointerEvent) => {
      const ds = dragState.current
      if (!ds.dragging) return
      const dx = e.clientX - ds.startX
      const dy = e.clientY - ds.startY
      if (Math.abs(dx) > 4 || Math.abs(dy) > 4) {
        setIsDragging(true)
        const newX = Math.max(0, Math.min(window.innerWidth - 80, ds.offsetX + dx))
        const newY = Math.max(0, Math.min(window.innerHeight - 80, ds.offsetY + dy))
        if (petRef.current) {
          petRef.current.style.left = `${newX}px`
          petRef.current.style.top = `${newY}px`
        }
      }
    }

    const onPointerUp = (e: PointerEvent) => {
      const ds = dragState.current
      if (!ds.dragging) return
      ds.dragging = false
      const dx = e.clientX - ds.startX
      const dy = e.clientY - ds.startY
      if (Math.abs(dx) > 4 || Math.abs(dy) > 4) {
        const newX = Math.max(0, Math.min(window.innerWidth - 80, ds.offsetX + dx))
        const newY = Math.max(0, Math.min(window.innerHeight - 80, ds.offsetY + dy))
        setPetPosition({ x: newX, y: newY })
        setIsDragging(false)
      } else {
        setIsDragging(false)
        setOpen(prev => !prev)
      }
    }

    window.addEventListener('pointermove', onPointerMove)
    window.addEventListener('pointerup', onPointerUp)

    const onResize = () => {
      setPetPosition(prev => {
        const clamped = {
          x: Math.max(0, Math.min(window.innerWidth - 80, prev.x)),
          y: Math.max(0, Math.min(window.innerHeight - 80, prev.y)),
        }
        if (petRef.current) {
          petRef.current.style.left = `${clamped.x}px`
          petRef.current.style.top = `${clamped.y}px`
        }
        return clamped
      })
    }
    window.addEventListener('resize', onResize)

    return () => {
      window.removeEventListener('pointermove', onPointerMove)
      window.removeEventListener('pointerup', onPointerUp)
      window.removeEventListener('resize', onResize)
    }
  }, [])

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
      setMessages(prev => [...prev, { role: 'assistant', content: '喵…网络连接失败，请稍后再试喵~' }])
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

  const isDark = theme === 'dark'

  // Compute chat panel position relative to pet
  const panelStyle: React.CSSProperties = (() => {
    const panelW = 340
    const panelH = 440
    const gap = 12
    const rightSpace = window.innerWidth - petPosition.x - 80
    const onRight = rightSpace >= panelW + gap
    return {
      position: 'fixed' as const,
      left: onRight ? petPosition.x + 80 + gap : Math.max(8, petPosition.x - panelW - gap),
      top: Math.max(8, Math.min(window.innerHeight - panelH - 8, petPosition.y - panelH / 2 + 40)),
      width: `min(${panelW}px, calc(100vw - 48px))`,
      height: panelH,
      zIndex: 9998,
    }
  })()

  return (
    <>
      {/* 对话面板——消息列表+快捷提问+输入框 */}
      {open && (
        <div style={{
          ...panelStyle,
          background: 'var(--bg-card)', borderRadius: 18, border: '1px solid var(--border-light)',
          boxShadow: 'var(--shadow-md)', display: 'flex', flexDirection: 'column',
          overflow: 'hidden', animation: 'slideUp 0.3s ease-out',
        }}>
          {/* Header */}
          <div style={{
            padding: '14px 18px', borderBottom: '1px solid var(--border-light)',
            background: isDark
              ? 'linear-gradient(135deg, #1e1d24, #16151a)'
              : 'linear-gradient(135deg, #fdf8f5, #fffcfb)',
            display: 'flex', alignItems: 'center', gap: 10,
          }}>
            <div style={{ width: 36, height: 36, borderRadius: '50%', overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <img src="/xiaoda.png" alt="小达" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 700, fontSize: 15, color: 'var(--text-primary)' }}>小达</div>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>您的 AI 职业成长伙伴</div>
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
                  <div style={{ width: 28, height: 28, borderRadius: '50%', overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, border: isDark ? '1px solid #4a332a' : '1px solid #fbcb8e' }}>
                    <img src="/xiaoda.png" alt="小达" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  </div>
                )}
                <div style={{
                  maxWidth: '80%', padding: '10px 14px', borderRadius: msg.role === 'user' ? '14px 14px 4px 14px' : '14px 14px 14px 4px',
                  background: msg.role === 'user' ? 'var(--accent-blue)' : 'var(--bg-hover)',
                  color: msg.role === 'user' ? '#fff' : 'var(--text-primary)',
                  fontSize: 13, lineHeight: 1.6, wordBreak: 'break-word',
                }}>
                  {msg.content}
                </div>
              </div>
            ))}
            {loading && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{ width: 28, height: 28, borderRadius: '50%', overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center', border: isDark ? '1px solid #4a332a' : '1px solid #fbcb8e', flexShrink: 0 }}>
                  <img src="/xiaoda.png" alt="小达" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                </div>
                <div style={{ display: 'flex', gap: 4, padding: '10px 14px', background: 'var(--bg-hover)', borderRadius: '14px 14px 14px 4px' }}>
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
                  style={{ padding: '4px 10px', borderRadius: 12, border: '1px solid var(--border-light)', background: 'var(--bg-card)', cursor: 'pointer', fontSize: 12, color: 'var(--text-secondary)', whiteSpace: 'nowrap', transition: 'border-color 0.2s, background-color 0.2s' }}
                  onMouseEnter={e => (e.currentTarget.style.borderColor = 'var(--accent-teal)')}
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
              placeholder="发送消息..."
              style={{ flex: 1, border: '1px solid var(--border-light)', borderRadius: 20, padding: '8px 14px', fontSize: 13, outline: 'none', background: 'var(--bg-hover)', color: 'var(--text-primary)', }}
              onFocus={e => (e.target.style.borderColor = 'var(--accent-teal)')}
              onBlur={e => (e.target.style.borderColor = 'var(--border-light)')}
            />
            <button onClick={() => send(input)} disabled={loading || !input.trim()}
              style={{ width: 36, height: 36, borderRadius: '50%', border: 'none', background: input.trim() ? 'var(--accent-teal)' : 'var(--border-light)', color: '#fff', fontSize: 16, cursor: input.trim() ? 'pointer' : 'default', display: 'flex', alignItems: 'center', justifyContent: 'center', transition: 'background 0.2s', flexShrink: 0 }}>
              ➤
            </button>
          </div>
        </div>
      )}

      {/* Mascot Video Button (Draggable) */}
      <div
        ref={petRef}
        title="点击和小达聊天"
        className={`salarycat-pet${isDragging ? ' dragging' : ''}`}
        style={{ left: petPosition.x, top: petPosition.y }}
        onPointerDown={(e) => {
          e.preventDefault()
          petRef.current?.setPointerCapture(e.pointerId)
          dragState.current = {
            dragging: true,
            startX: e.clientX,
            startY: e.clientY,
            offsetX: petPosition.x,
            offsetY: petPosition.y,
          }
        }}
      >
        <video
          src="/yuexinmiao.mp4"
          autoPlay
          muted
          loop
          playsInline
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            pointerEvents: 'none',
          }}
        />
      </div>
    </>
  )
}
