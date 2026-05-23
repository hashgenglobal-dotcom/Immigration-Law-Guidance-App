export type RiskLevel = 'low' | 'medium' | 'high'

export type SourceType = 'regulation' | 'statute' | 'case' | 'guidance'

export interface OfficialSource {
  title: string
  citation: string
  url: string
  type: SourceType
}

export interface MockAnswer {
  shortAnswer: string
  simpleExplanation: string
  possibleRisks: string[]
  whatToDoNext: string[]
  sources: OfficialSource[]
  disclaimer: string
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

export const mockAnswer: MockAnswer = {
  shortAnswer:
    'This is mock legal information for development only. A future release will retrieve answers from official sources in the database.',
  simpleExplanation:
    'In plain language: eligibility and procedures depend on your status, filing history, and the specific immigration benefit. This placeholder explains the kind of guidance the app will provide once connected to verified legal text.',
  possibleRisks: [
    'Filing too late or with incomplete evidence can delay or harm your case.',
    'Working or traveling without proper authorization may affect future applications.',
    'Immigration decisions are fact-specific; general information may not fit your situation.',
  ],
  whatToDoNext: [
    'Gather documents related to your status and any notices you received.',
    'Review official USCIS or EOIR materials for your situation.',
    'Consult a qualified immigration attorney for advice about your specific case.',
  ],
  sources: [
    {
      title: '8 CFR § 208.7 - Employment authorization',
      citation: '8 CFR 208.7',
      url: 'https://www.law.cornell.edu/cfr/text/8/208.7',
      type: 'regulation',
    },
    {
      title: 'USCIS - Employment Authorization',
      citation: 'USCIS EAD',
      url: 'https://www.uscis.gov/working-in-the-united-states',
      type: 'guidance',
    },
  ],
  disclaimer:
    'GENERAL LEGAL INFORMATION, NOT LEGAL ADVICE. HIGH-RISK SITUATIONS - SEEK ADVICE FROM A QUALIFIED IMMIGRATION ATTORNEY.',
}

import { scenarioGuides } from './scenarioGuides'

export { scenarioGuides as mockScenarios }

export function getScenarioById(id: string): Scenario | undefined {
  return scenarioGuides.find((s) => s.id === id)
}
