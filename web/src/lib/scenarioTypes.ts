export type RiskLevel = 'low' | 'medium' | 'high'

export type SourceType = 'regulation' | 'statute' | 'case' | 'guidance'

export interface OfficialSource {
  title: string
  citation: string
  url: string
  type: SourceType
}

export interface Scenario {
  id: string
  title: string
  riskLevel: RiskLevel
  shortDescription: string
  overview: string
  keyPoints: string[]
  sources: OfficialSource[]
}
