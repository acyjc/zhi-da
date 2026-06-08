// Toast 全局通知系统——轻量 DOM 驱动，无需 React Context
// 用法: import { toast } from '../utils/toast'
//       toast.success('操作成功')
//       toast.error('操作失败')
//       toast.warning('请注意')
//       toast.info('提示')

type ToastType = 'success' | 'error' | 'warning' | 'info'

const TOAST_DURATION = 3200
const TOAST_CONTAINER_ID = 'toast-container'

function getContainer(): HTMLElement {
  let container = document.getElementById(TOAST_CONTAINER_ID)
  if (!container) {
    container = document.createElement('div')
    container.id = TOAST_CONTAINER_ID
    container.className = 'toast-container'
    document.body.appendChild(container)
  }
  return container
}

function show(message: string, type: ToastType = 'info') {
  const container = getContainer()
  const el = document.createElement('div')
  el.className = `toast toast-${type}`
  el.setAttribute('role', 'alert')

  const iconMap: Record<ToastType, string> = {
    success: '✓',
    error: '✕',
    warning: '!',
    info: 'i',
  }

  el.innerHTML = `
    <span class="toast-icon toast-icon-${type}">${iconMap[type]}</span>
    <span class="toast-msg">${escapeHtml(message)}</span>
  `

  container.appendChild(el)

  // Trigger enter animation
  requestAnimationFrame(() => {
    el.classList.add('toast-visible')
  })

  // Auto dismiss
  setTimeout(() => {
    el.classList.add('toast-exit')
    el.addEventListener('animationend', () => el.remove(), { once: true })
  }, TOAST_DURATION)
}

function escapeHtml(text: string): string {
  const div = document.createElement('span')
  div.textContent = text
  return div.innerHTML
}

export const toast = {
  show,
  success: (msg: string) => show(msg, 'success'),
  error: (msg: string) => show(msg, 'error'),
  warning: (msg: string) => show(msg, 'warning'),
  info: (msg: string) => show(msg, 'info'),
}
