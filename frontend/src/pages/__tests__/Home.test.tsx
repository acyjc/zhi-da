import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Home from '../../pages/Home'
import { useAppStore } from '../../stores/appStore'

// 模拟 API 模块
vi.mock('../../services/api', () => ({
  getStudent: vi.fn(),
  listEnterprisesForLogin: vi.fn(),
  login: vi.fn(),
  setAuthToken: vi.fn(),
}))

import { listEnterprisesForLogin, login } from '../../services/api'

const mockedListEnterprises = vi.mocked(listEnterprisesForLogin)
const mockedLogin = vi.mocked(login)

function renderHome() {
  return render(
    <MemoryRouter>
      <Home />
    </MemoryRouter>,
  )
}

describe('Home - 企业登录状态校验', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // 默认 login mock 返回有效 token
    mockedLogin.mockResolvedValue({
      access_token: 'mock-token',
      token_type: 'bearer',
      expires_at: '2026-06-09T00:00:00Z',
      role: 'enterprise',
      student_id: 0,
      enterprise_id: '1',
      admin_account: '',
    })
    useAppStore.setState({
      student: null,
      jobs: [],
      diagnosisResult: null,
      diagnosisHistory: [],
      isLoading: false,
      progress: { stage: '', progress: 0, message: '' },
      triggeredReEvaluate: false,
    })
    localStorage.clear()
  })

  it('企业列表渲染正确，active 企业可用、pending/disabled 企业 disabled', async () => {
    mockedListEnterprises.mockResolvedValue([
      { id: '1', name: '待审核企业', status: 'pending' },
      { id: '2', name: '活跃企业A', status: 'active' },
      { id: '3', name: '已禁用企业', status: 'disabled' },
    ])

    renderHome()

    // 切换到企业端 tab
    fireEvent.click(await screen.findByText('企业端'))

    // 企业列表应正确渲染：pending/disabled 的 option 带 disabled，active 的不带
    await waitFor(() => {
      const options = document.querySelectorAll('option')
      expect(options.length).toBe(4) // placeholder + 3 enterprises

      const pendingOpt = Array.from(options).find(o => o.textContent?.includes('待审核企业'))
      expect(pendingOpt!.disabled).toBe(true)

      const activeOpt = Array.from(options).find(o => o.textContent?.includes('活跃企业A'))
      expect(activeOpt!.disabled).toBe(false)

      const disabledOpt = Array.from(options).find(o => o.textContent?.includes('已禁用企业'))
      expect(disabledOpt!.disabled).toBe(true)
    })
  })

  it('pending 企业 option 带 disabled 属性且不可进入', async () => {
    mockedListEnterprises.mockResolvedValue([
      { id: '1', name: '待审核企业', status: 'pending' },
      { id: '2', name: '活跃企业', status: 'active' },
    ])

    renderHome()
    fireEvent.click(await screen.findByText('企业端'))

    await waitFor(() => {
      const options = document.querySelectorAll('option')
      const pendingOpt = Array.from(options).find(o => o.textContent?.includes('待审核企业'))
      expect(pendingOpt).toBeTruthy()
      expect(pendingOpt!.disabled).toBe(true)
      expect(pendingOpt!.textContent).toContain('待审核')
    })
  })

  it('disabled 企业 option 带 disabled 属性且不可进入', async () => {
    mockedListEnterprises.mockResolvedValue([
      { id: '1', name: '活跃企业', status: 'active' },
      { id: '2', name: '已禁用企业', status: 'disabled' },
    ])

    renderHome()
    fireEvent.click(await screen.findByText('企业端'))

    await waitFor(() => {
      const options = document.querySelectorAll('option')
      const disabledOpt = Array.from(options).find(o => o.textContent?.includes('已禁用企业'))
      expect(disabledOpt).toBeTruthy()
      expect(disabledOpt!.disabled).toBe(true)
      expect(disabledOpt!.textContent).toContain('已禁用')
    })
  })

  it('选择 pending 企业提交时显示审核提示', async () => {
    mockedListEnterprises.mockResolvedValue([
      { id: '1', name: '待审核企业', status: 'pending' },
      { id: '2', name: '活跃企业', status: 'active' },
    ])

    renderHome()
    fireEvent.click(await screen.findByText('企业端'))

    // 等加载完，然后手动选择 pending 企业
    await waitFor(() => {
      expect(document.querySelectorAll('option').length).toBeGreaterThan(1)
    })

    const select = document.querySelector('select') as HTMLSelectElement
    fireEvent.change(select, { target: { value: '1' } })

    // 提交
    const submitBtn = await screen.findByRole('button', { name: /进入企业端/ })
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(screen.getByText(/尚未通过审核/)).toBeTruthy()
    })
  })

  it('选择 disabled 企业提交时显示禁用提示', async () => {
    mockedListEnterprises.mockResolvedValue([
      { id: '1', name: '活跃企业', status: 'active' },
      { id: '2', name: '已禁用企业', status: 'disabled' },
    ])

    renderHome()
    fireEvent.click(await screen.findByText('企业端'))

    await waitFor(() => {
      expect(document.querySelectorAll('option').length).toBeGreaterThan(1)
    })

    const select = document.querySelector('select') as HTMLSelectElement
    fireEvent.change(select, { target: { value: '2' } })

    const submitBtn = await screen.findByRole('button', { name: /进入企业端/ })
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(screen.getByText(/已被禁用/)).toBeTruthy()
    })
  })

  it('active 企业可以正常提交（不会显示错误消息）', async () => {
    mockedListEnterprises.mockResolvedValue([
      { id: '1', name: '活跃企业', status: 'active' },
    ])

    renderHome()
    fireEvent.click(await screen.findByText('企业端'))

    // 等列表加载完，手动选择 active 企业
    await waitFor(() => {
      expect(document.querySelectorAll('option').length).toBeGreaterThan(1)
    })

    const select = document.querySelector('select') as HTMLSelectElement
    fireEvent.change(select, { target: { value: '1' } })

    const submitBtn = await screen.findByRole('button', { name: /进入企业端/ })
    fireEvent.click(submitBtn)

    // 等一个 tick，确保没有出现在 login-message 区域的错误消息
    await new Promise(r => setTimeout(r, 100))
    expect(document.querySelector('.login-message')).toBeNull()
  })
})
