// 错误边界——捕获渲染异常，展示友好降级 UI 替代白屏
import React from 'react'

interface ErrorBoundaryProps {
  children: React.ReactNode
  fallback?: React.ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('[ErrorBoundary] 渲染异常:', error, info.componentStack)
  }

  private handleReload = () => {
    window.location.reload()
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          width: '100%',
          background: 'var(--bg-primary)',
          padding: 'var(--space-6)',
        }}>
          <div style={{
            textAlign: 'center',
            background: 'var(--bg-card)',
            borderRadius: 'var(--radius-xl)',
            boxShadow: 'var(--shadow-sm)',
            padding: 'var(--space-12)',
            maxWidth: 460,
            width: '100%',
            border: '1px solid var(--border-light)',
          }}>
            {/* 警告三角图标 */}
            <div style={{ marginBottom: 'var(--space-5)' }}>
              <svg
                width="48"
                height="48"
                viewBox="0 0 24 24"
                fill="none"
                stroke="var(--accent-warning)"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                <line x1="12" y1="9" x2="12" y2="13" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
            </div>

            <h2 style={{
              fontSize: 18,
              fontWeight: 600,
              color: 'var(--text-primary)',
              fontFamily: 'var(--font-display)',
              marginBottom: 'var(--space-2)',
            }}>
              页面出了点问题
            </h2>

            <p style={{
              fontSize: 13,
              color: 'var(--text-secondary)',
              lineHeight: 1.6,
              marginBottom: 'var(--space-6)',
            }}>
              请刷新页面重试，如果问题持续存在请联系管理员
            </p>

            <button
              className="btn btn-primary"
              onClick={this.handleReload}
              style={{
                fontFamily: 'var(--font-display)',
                fontWeight: 600,
                fontSize: 14,
                cursor: 'pointer',
              }}
            >
              刷新页面
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
