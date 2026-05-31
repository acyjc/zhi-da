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

// 四维能力画像
export interface AbilityProfile {
  tech_skills: AbilityDimension
  project_exp: AbilityDimension
  soft_skills: AbilityDimension
  domain_knowledge: AbilityDimension
}

// 学生信息
export interface Student {
  id: string
  name: string
  grade: string
  major: string
  target_job: string
  tech_skills: Record<string, number>
  project_exp: ProjectExperience[]
  soft_skills: Record<string, number>
  domain_knowledge: Record<string, number>
  resume_text: string
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
}

// 成长阶段
export interface GrowthPhase {
  goal: string
  weeks: number
  tasks: PhaseTask[]
}

// 诊断结果
export interface DiagnosisResult {
  id: string
  student_id: string
  version: number
  diagnosis_type: string
  match_score: number
  dimension_scores: Record<string, number>
  dimension_changes: Record<string, number>
  gap_details: GapDetail[]
  top5_jobs: { job_id: string; title: string; score: number; company: string }[]
  growth_path: { phases: GrowthPhase[] }
  career_advice: string
  ai_reasoning: Record<string, any>
  trigger_event: string
  created_at: string
}
