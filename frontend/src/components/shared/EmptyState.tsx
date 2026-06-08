// 空状态占位组件——展示零数据时的引导信息
import type { FC } from 'react'

interface EmptyStateProps {
  /** 图标（emoji 或文字），默认 "📭" */
  icon?: string
  /** 主标题（必填） */
  title: string
  /** 补充描述 */
  description?: string
  /** 可选操作按钮 */
  action?: {
    label: string
    onClick: () => void
  }
}

const EmptyState: FC<EmptyStateProps> = ({
  icon = '📭',
  title,
  description,
  action,
}) => {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 'var(--space-12) var(--space-6)',
      textAlign: 'center',
    }}>
      {/* 大图标 */}
      <div style={{
        fontSize: 40,
        lineHeight: 1,
        marginBottom: 'var(--space-4)',
      }}>
        {icon}
      </div>

      {/* 标题 */}
      <div style={{
        fontSize: 16,
        fontWeight: 600,
        color: 'var(--text-primary)',
        fontFamily: 'var(--font-display)',
        marginBottom: description ? 'var(--space-2)' : 0,
      }}>
        {title}
      </div>

      {/* 描述 */}
      {description && (
        <div style={{
          fontSize: 13,
          color: 'var(--text-secondary)',
          lineHeight: 1.6,
          maxWidth: 360,
        }}>
          {description}
        </div>
      )}

      {/* 操作按钮 */}
      {action && (
        <button
          className="btn btn-primary"
          onClick={action.onClick}
          style={{
            marginTop: 'var(--space-5)',
            fontFamily: 'var(--font-display)',
            fontWeight: 600,
            fontSize: 13,
            cursor: 'pointer',
          }}
        >
          {action.label}
        </button>
      )}
    </div>
  )
}

export default EmptyState
