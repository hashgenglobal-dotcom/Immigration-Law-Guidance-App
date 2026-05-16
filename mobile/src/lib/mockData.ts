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

export const mockScenarios: Scenario[] = [
  {
    id: 'asylum-work-auth',
    title: 'Asylum work authorization',
    riskLevel: 'medium',
    shortDescription: 'When and how pending asylum applicants may apply for employment authorization',
    overview:
      'Asylum applicants may be eligible to apply for employment authorization after their application has been pending for a required period, subject to regulatory requirements and processing times.',
    keyPoints: [
      'Eligibility timing is defined in federal regulations—not immediate upon filing.',
      'Use the correct USCIS form and category when applying for an EAD.',
      'Unauthorized work before approval can have immigration consequences.',
    ],
    sources: [
      {
        title: '8 CFR § 208.7 - Employment authorization',
        citation: '8 CFR 208.7',
        url: 'https://www.law.cornell.edu/cfr/text/8/208.7',
        type: 'regulation',
      },
    ],
  },
  {
    id: 'asylum-filing-deadline',
    title: 'Asylum filing deadline',
    riskLevel: 'high',
    shortDescription: 'One-year filing rule and exceptions in asylum cases',
    overview:
      'Most individuals must apply for asylum within one year of arrival in the United States, with limited exceptions. Missing deadlines can bar asylum unless an exception applies.',
    keyPoints: [
      'The one-year rule is a critical deadline with serious consequences if missed.',
      'Exceptions exist for changed circumstances or extraordinary circumstances.',
      'Document dates of entry and events supporting any exception carefully.',
    ],
    sources: [
      {
        title: 'INA § 208(a)(2)(B) - Timing',
        citation: 'INA 208(a)(2)(B)',
        url: 'https://www.law.cornell.edu/uscode/text/8/1158',
        type: 'statute',
      },
    ],
  },
  {
    id: 'aos-eligibility',
    title: 'Adjustment of status eligibility',
    riskLevel: 'medium',
    shortDescription: 'Who may apply to adjust status inside the United States',
    overview:
      'Adjustment of status allows certain individuals already in the U.S. to apply for lawful permanent residence without leaving, if they meet eligibility and admissibility requirements and a visa is available.',
    keyPoints: [
      'You generally need an approved immigrant petition and an available visa number when required.',
      'Unlawful presence, status violations, or certain grounds of inadmissibility may affect eligibility.',
      'Travel while a pending AOS application may require advance parole.',
    ],
    sources: [
      {
        title: 'USCIS - Adjustment of Status',
        citation: 'USCIS AOS',
        url: 'https://www.uscis.gov/green-card/green-card-processes-and-procedures/adjustment-of-status',
        type: 'guidance',
      },
    ],
  },
  {
    id: 'ead-categories',
    title: 'Employment authorization categories',
    riskLevel: 'low',
    shortDescription: 'Common EAD eligibility categories and form instructions',
    overview:
      'Employment authorization is granted in specific categories. Applicants must use the correct category code and evidence listed in USCIS instructions for their situation.',
    keyPoints: [
      'Category codes on Form I-765 must match your immigration status or pending application.',
      'Evidence requirements vary by category—follow the form edition instructions.',
      'An EAD is not a visa and does not by itself grant immigration status.',
    ],
    sources: [
      {
        title: 'USCIS Form I-765',
        citation: 'Form I-765',
        url: 'https://www.uscis.gov/i-765',
        type: 'guidance',
      },
    ],
  },
  {
    id: 'notice-to-appear',
    title: 'Notice to Appear',
    riskLevel: 'high',
    shortDescription: 'What a Notice to Appear means and immediate steps',
    overview:
      'A Notice to Appear (NTA) initiates removal proceedings in immigration court. Hearing dates, charges, and relief options require prompt attention and often attorney assistance.',
    keyPoints: [
      'Do not ignore court dates—failure to appear can result in removal in absentia.',
      'Review the charges and factual allegations on the NTA carefully.',
      'Seek legal representation as soon as possible for removal defense.',
    ],
    sources: [
      {
        title: 'EOIR - Immigration Court',
        citation: 'EOIR',
        url: 'https://www.justice.gov/eoir',
        type: 'guidance',
      },
    ],
  },
]

export function getScenarioById(id: string): Scenario | undefined {
  return mockScenarios.find((s) => s.id === id)
}
