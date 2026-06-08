// PathTab 复评行为验证测试
// 验证: Agent continue_growth 加载、review_task 审核、re_evaluate + task_id、降级逻辑
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import PathTab from '../PathTab'

vi.mock('../../../services/api', () => ({
  getGrowthTasks: vi.fn(),
  submitTaskEvidence: vi.fn(),
  runStudentAgent: vi.fn(),
  runStudentAgentStream: vi.fn(),
}))

vi.mock('../../shared/PathTimeline', () => ({
  default: () => <div data-testid="path-timeline">timeline</div>,
}))
vi.mock('../../shared/TaskCard', () => ({
  default: ({ task, onComplete, status }: any) => (
    <div data-testid={`task-${task.name}`}>
      <span>{task.name}</span>
      <span data-testid={`status-${task.name}`}>{status}</span>
      <button onClick={() => onComplete('完成了学习记录')}>提交</button>
    </div>
  ),
}))

import { runStudentAgent, runStudentAgentStream, getGrowthTasks } from '../../../services/api'

const mockedAgent = vi.mocked(runStudentAgent)
const mockedStream = vi.mocked(runStudentAgentStream)
const mockedDirectTasks = vi.mocked(getGrowthTasks)

const defaultProps = {
  growthPath: {
    phases: [{
      goal: '阶段 1', weeks: 4,
      tasks: [{ name: 'Python基础', description: '学习Python', resources: [], criteria: '完成练习' }],
    }],
  },
  diagnosisId: 'diag-1',
  studentId: 1001,
  onTaskComplete: vi.fn(),
  onReEvaluateComplete: vi.fn(),
}

// 模拟 Agent 返回的成长任务列表
const mockTasks = [{
  id: 'task-1', diagnosis_id: 'diag-1', phase_index: 0, task_index: 0,
  task_name: 'Python基础', task_description: '学习Python基础',
  linked_gap: 'Python', target_dimension: 'tech_skills',
  expected_impact: { tech: 10 }, evidence_required: '学习笔记',
  resources: ['link1'], criteria: '完成练习',
  status: 'in_progress', submitted_evidence: null,
  reviewed_by_ai: {}, re_evaluation_id: null,
  completed_at: null, created_at: '2026-01-01',
}]

describe('PathTab - Agent 行为验证', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    defaultProps.onTaskComplete = vi.fn()
    defaultProps.onReEvaluateComplete = vi.fn()
  })

  it('加载时通过 Agent continue_growth 获取任务', async () => {
    mockedAgent.mockResolvedValue({
      action: 'advice', message: '', data: { tasks: mockTasks },
      next_actions: [], ai_status: 'available',
    })

    render(<PathTab {...defaultProps} />)

    await waitFor(() => {
      expect(mockedAgent).toHaveBeenCalledWith(1001, 'continue_growth')
    })
  })

  it('Agent 失败时降级到直接 GrowthTask API', async () => {
    mockedAgent.mockRejectedValue(new Error('Agent unavailable'))
    mockedDirectTasks.mockResolvedValue(mockTasks as any)

    render(<PathTab {...defaultProps} />)

    await waitFor(() => {
      expect(mockedDirectTasks).toHaveBeenCalledWith(1001, 'diag-1')
    })
  })

  it('提交任务证据优先通过 Agent review_task', async () => {
    // 1. 加载任务
    mockedAgent
      .mockResolvedValueOnce({
        action: 'advice', message: '', data: { tasks: mockTasks },
        next_actions: [], ai_status: 'available',
      })
      // 2. 审核任务
      .mockResolvedValueOnce({
        action: 'task_reviewed', message: '审核完成',
        data: {
          review: {
            task_id: 'task-1', task_name: 'Python基础',
            evidence_length: 10, review_score: 4,
            has_evidence: true, preliminary_approved: false,
            feedback: '还需要更多实践',
          },
          status: 'in_progress',
        },
        next_actions: [], ai_status: 'available',
      })

    render(<PathTab {...defaultProps} />)

    // 等待任务加载
    await waitFor(() => {
      expect(screen.getByTestId('task-Python基础')).toBeTruthy()
    })

    // 点击提交
    fireEvent.click(screen.getByTestId('task-Python基础').querySelector('button')!)

    // 验证 review_task 被调用
    await waitFor(() => {
      expect(mockedAgent).toHaveBeenCalledWith(
        1001, 'review_task',
        { task_id: 'task-1', evidence: '完成了学习记录' },
      )
    })

    // 审核结果展示
    await waitFor(() => {
      expect(screen.getByText(/还需要更多实践/)).toBeTruthy()
    })
  })

  it('审核通过后触发复评——传入 task_id 使用 re_evaluate intent', async () => {
    // 1. 加载任务
    mockedAgent
      .mockResolvedValueOnce({
        action: 'advice', message: '', data: { tasks: mockTasks },
        next_actions: [], ai_status: 'available',
      })
      // 2. 审核通过
      .mockResolvedValueOnce({
        action: 'task_reviewed', message: '审核通过',
        data: {
          review: {
            task_id: 'task-1', task_name: 'Python基础',
            evidence_length: 50, review_score: 5,
            has_evidence: true, preliminary_approved: true,
            feedback: '优秀！',
          },
          status: 'completed',
        },
        next_actions: [], ai_status: 'available',
      })

    // 3. 复评 Stream
    mockedStream.mockResolvedValue({
      action: 're_evaluation_completed', message: '复评完成',
      data: { id: 'diag-2' },
      next_actions: [], ai_status: 'available',
    })

    render(<PathTab {...defaultProps} />)

    // 等待任务加载
    await waitFor(() => {
      expect(screen.getByTestId('task-Python基础')).toBeTruthy()
    })

    // 提交任务 → 审核通过
    fireEvent.click(screen.getByTestId('task-Python基础').querySelector('button')!)

    // 等待复评确认面板出现（使用 getByRole 避免匹配到标题文本）
    await waitFor(() => {
      expect(screen.getByRole('button', { name: '触发复评' })).toBeTruthy()
    })

    // 点击「触发复评」
    fireEvent.click(screen.getByRole('button', { name: '触发复评' }))

    // 验证: runStudentAgentStream 被调用，intent='re_evaluate'，payload 包含 task_id
    await waitFor(() => {
      expect(mockedStream).toHaveBeenCalledWith(
        1001, 're_evaluate', { task_id: 'task-1' },
        expect.any(Function),
      )
    })

    // 验证: onReEvaluateComplete 被调用，携带新诊断 ID
    await waitFor(() => {
      expect(defaultProps.onReEvaluateComplete).toHaveBeenCalledWith('diag-2')
    })
  })

  it('复评失败时显示错误信息', async () => {
    // 1. 加载任务
    mockedAgent
      .mockResolvedValueOnce({
        action: 'advice', message: '', data: { tasks: mockTasks },
        next_actions: [], ai_status: 'available',
      })
      // 2. 审核通过
      .mockResolvedValueOnce({
        action: 'task_reviewed', message: '审核通过',
        data: {
          review: {
            task_id: 'task-1', task_name: 'Python基础',
            evidence_length: 50, review_score: 5,
            has_evidence: true, preliminary_approved: true,
            feedback: '优秀！',
          },
          status: 'completed',
        },
        next_actions: [], ai_status: 'available',
      })

    // 3. 复评失败
    mockedStream.mockRejectedValue(new Error('复评服务暂时不可用'))

    render(<PathTab {...defaultProps} />)

    // 等待加载 → 提交 → 审核通过 → 触发复评
    await waitFor(() => {
      expect(screen.getByTestId('task-Python基础')).toBeTruthy()
    })
    fireEvent.click(screen.getByTestId('task-Python基础').querySelector('button')!)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: '触发复评' })).toBeTruthy()
    })
    fireEvent.click(screen.getByRole('button', { name: '触发复评' }))

    // 验证错误信息显示
    await waitFor(() => {
      expect(screen.getByText(/复评服务暂时不可用/)).toBeTruthy()
    })
  })
})
