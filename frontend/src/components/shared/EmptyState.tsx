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
    <div className="state-container">
      <div className="state-icon">{icon}</div>
      <div className="state-title" style={{ marginBottom: description ? undefined : 0 }}>
        {title}
      </div>
      {description && (
        <div className="state-desc">{description}</div>
      )}
      {action && (
        <button
          className="btn btn-primary"
          onClick={action.onClick}
          style={{ marginTop: 'var(--space-5)' }}
        >
          {action.label}
        </button>
      )}
    </div>
  )
}

export default EmptyState
