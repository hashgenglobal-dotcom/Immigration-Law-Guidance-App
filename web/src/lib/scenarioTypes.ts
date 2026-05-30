export type RiskLevel = 'low' | 'medium' | 'high'

export type SourceType = 'regulation' | 'statute' | 'case' | 'guidance'

export type ScenarioCategoryId =
  | 'f1-j1'
  | 'employment-nonimmigrant'
  | 'employment-permanent'
  | 'family-based'
  | 'humanitarian'
  | 'naturalization-compliance'

export interface OfficialSource {
  title: string
  citation: string
  url: string
  type: SourceType
}

export interface Scenario {
  id: string
  title: string
  category: ScenarioCategoryId
  riskLevel: RiskLevel
  /** 2–3 sentence overview shown on cards */
  description: string
  /** Detailed markdown: steps, timelines, citations */
  content: string
  sources: OfficialSource[]
}

/** @deprecated use description — kept for landing page compatibility during migration */
export type LegacyScenario = Scenario & {
  shortDescription: string
  overview: string
  keyPoints: string[]
}
