// TypeScript 类型定义——学生/岗位/诊断/进度/技能等核心数据结构

// 技能项
export interface SkillItem {
  name: string
  score: number
  level: string
}

// 能力维度
export interface AbilityDimension {
  weight: number
  sub_items: SkillItem[]
}

export interface CoreCourse {
  name: string
  score: number
}

export interface AcademicFoundation {
  gpa: string
  rank: string
  core_courses: CoreCourse[]
  awards: string[]
  normalized_score: number
}

export interface SoftSkillDetail {
  level: string
  evidence: string[]
  normalized_score: number
}

// 五维能力画像
export interface AbilityProfile {
  tech_skills: AbilityDimension
  project_exp: AbilityDimension
  academic_foundation: AbilityDimension
  domain_knowledge: AbilityDimension
  soft_skill_evidence: AbilityDimension
}

// 学生信息
export interface Student {
  id: number
  name: string
  grade: string
  major: string
  target_job: string
  tech_skills: Record<string, number>
  project_exp: ProjectExperience[]
  soft_skills: Record<string, number>
  domain_knowledge: Record<string, number>
  resume_text: string
  academic_foundation?: AcademicFoundation
  soft_skill_evidence?: Record<string, SoftSkillDetail>
}

// 项目经历
export interface ProjectExperience {
  name: string
  role: string
  description: string
  duration: string
}

// 岗位信息
export interface Job {
  id: string
  title: string
  category: string
  requirements: Record<string, any>
  weight_config: Record<string, number>
  description: string
  company: string
}

// 差距详情
export interface GapDetail {
  dimension: string
  skill: string
  current: number
  required: number
  gap: number
}

// 阶段任务
export interface PhaseTask {
  name: string
  description: string
  resources: string[]
  criteria: string
  linked_gap?: string
  target_dimension?: string
  expected_impact?: Record<string, number>
}

// 成长阶段
export interface GrowthPhase {
  goal: string
  weeks: number
  tasks: PhaseTask[]
}

// 推荐岗位（统一字段）
export interface RecommendedJob {
  job_id: string
  title: string
  match_score: number
  company: string
  reason?: string
  matched_skills?: string[]
  missing_skills?: string[]
  confidence?: number
}

// 维度解释
export interface DimensionExplanation {
  score: number
  evidence: string[]
  missing: string[]
  confidence: number
}

// 匹配分解释
export interface MatchScoreExplanation {
  formula: string
  weights: Record<string, number>
  dimension_scores: Record<string, number>
  final_score: number
}

// 统一解释结构
export interface Explanations {
  summary?: {
    basis: string
    confidence: number
  }
  match_score?: MatchScoreExplanation
  dimensions?: Record<string, DimensionExplanation>
  recommended_jobs?: RecommendedJob[]
  growth_tasks?: Array<{
    task_name: string
    linked_gap: string
    expected_impact: Record<string, number>
  }>
}

// AI 状态枚举
export type AIStatus = 'available' | 'missing_key' | 'provider_error' | 'schema_error' | 'fallback_rule_based'

// Agent 意图类型
export type AgentIntent = 'diagnose' | 'continue_growth' | 'review_task' | 're_evaluate' | 'ask' | 'navigate'

// Agent 动作类型
export type AgentAction = 'ask_for_info' | 'diagnosis_completed' | 'task_reviewed' | 're_evaluation_completed' | 'advice' | 'error'

// Agent 建议的下一步操作
export interface NextAction {
  label: string
  intent: string
  payload: Record<string, any>
}

// Agent 推理信息
export interface AgentReasoning {
  goal?: string
  basis?: string[]
  decision?: string
  confidence?: number
  used_tools?: string[]
  limits?: string[]
  selected_skill?: string
  next_check?: string
  pipeline_meta?: Record<string, any>
}

// Agent 统一响应
export interface AgentResult {
  action: AgentAction
  message: string
  data: Record<string, any>
  next_actions: NextAction[]
  reasoning?: AgentReasoning
  ai_status: AIStatus
}

// 对话消息（多轮对话面板）
export interface ConversationMessage {
  role: 'user' | 'assistant' | 'system_summary'
  content: string
  intent?: string
  created_at?: string
}

// 诊断结果
export interface DiagnosisResult {
  id: string
  student_id: number
  version: number
  diagnosis_type: string
  match_score: number
  dimension_scores: Record<string, number>
  dimension_changes: Record<string, number>
  gap_details: GapDetail[]
  top5_jobs: RecommendedJob[]
  growth_path: { phases: GrowthPhase[] }
  career_advice: string
  ai_reasoning: Record<string, any>
  reasoning?: AgentReasoning
  // 新增字段
  ability_profile?: AbilityProfile
  explanations?: Explanations
  confidence?: Record<string, any>
  ai_status?: AIStatus
  trigger_event: string
  created_at: string
}
