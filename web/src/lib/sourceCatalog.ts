/** Indexed and planned legal sources — web source library catalog */

export type SourceFamily =
  | 'ecfr'
  | 'ina'
  | 'uscis-forms'
  | 'uscis-pm'
  | 'uscis-pages'
  | 'federal-register'
  | 'bia'

export type SourceStatus = 'indexed' | 'preview' | 'planned'

export type SourceFamilyMeta = {
  id: SourceFamily
  name: string
  abbr: string
  color: string
  colorTint: string
  description: string
  corpusNote: string
  status: SourceStatus
}

export type SourceEntry = {
  id: string
  citation: string
  family: SourceFamily
  topic: string
  subtopic: string
  description: string
  officialUrl: string
  status: SourceStatus
  tags: string[]
}

export const SOURCE_FAMILIES: SourceFamilyMeta[] = [
  {
    id: 'ecfr',
    name: 'Code of Federal Regulations',
    abbr: 'CFR / eCFR',
    color: 'var(--blue)',
    colorTint: 'var(--blue-tint)',
    description:
      'Binding agency regulations for immigration procedures, eligibility, and enforcement. Title 8 is indexed for retrieval.',
    corpusNote: 'ecfr-title8-full-* · hybrid vector + keyword search',
    status: 'indexed',
  },
  {
    id: 'ina',
    name: 'Immigration and Nationality Act',
    abbr: 'INA / U.S. Code',
    color: '#5b4db5',
    colorTint: '#f4f0fb',
    description:
      'Primary statutory authority for immigration, naturalization, and citizenship (Title 8, U.S. Code).',
    corpusNote: 'ina-* dataset versions',
    status: 'indexed',
  },
  {
    id: 'uscis-forms',
    name: 'USCIS Forms & Instructions',
    abbr: 'USCIS Forms',
    color: '#2d6a2d',
    colorTint: '#eef6ee',
    description:
      'Official petitions and applications with instructions that carry weight in adjudications.',
    corpusNote: 'Linked via USCIS official pages and cross-references in CFR/PM',
    status: 'indexed',
  },
  {
    id: 'uscis-pm',
    name: 'USCIS Policy Manual',
    abbr: 'Policy Manual',
    color: 'var(--bronze)',
    colorTint: 'var(--bronze-tint)',
    description: 'Official USCIS guidance for adjudicators across employment, naturalization, and more.',
    corpusNote: 'uscis-pm-* · 800+ chunks in MVP corpus',
    status: 'indexed',
  },
  {
    id: 'uscis-pages',
    name: 'USCIS Official Pages',
    abbr: 'USCIS.gov',
    color: '#0f7ba7',
    colorTint: '#e0f2fe',
    description: 'Program pages, form landing pages, and agency guidance published on USCIS.gov.',
    corpusNote: 'uscis-official-pages-*',
    status: 'indexed',
  },
  {
    id: 'federal-register',
    name: 'Federal Register',
    abbr: 'Fed. Register',
    color: '#0f7ba7',
    colorTint: '#e0f2fe',
    description: 'Rulemaking, proposed rules, TPS designations, and DHS/DOJ notices.',
    corpusNote: 'Official Updates feed (preview on web)',
    status: 'preview',
  },
  {
    id: 'bia',
    name: 'BIA Precedent Decisions',
    abbr: 'BIA',
    color: '#b45309',
    colorTint: '#fef3c7',
    description: 'Board precedent binding on immigration judges and DHS officers.',
    corpusNote: 'Post-MVP · not active in retrieval',
    status: 'planned',
  },
]

export function familyMeta(id: SourceFamily): SourceFamilyMeta {
  return SOURCE_FAMILIES.find((f) => f.id === id)!
}

export const SOURCE_CATALOG: SourceEntry[] = [
  // eCFR — employment & status
  {
    id: 'ecfr-274a-12',
    citation: '8 CFR § 274a.12',
    family: 'ecfr',
    topic: 'Employment authorization',
    subtopic: 'Classes of aliens authorized to work',
    description: 'Lists categories of noncitizens eligible for employment authorization and related conditions.',
    officialUrl: 'https://www.ecfr.gov/current/title-8/chapter-I/subchapter-B/part-274a/section-274a.12',
    status: 'indexed',
    tags: ['EAD', 'work authorization', 'I-765'],
  },
  {
    id: 'ecfr-274a-13',
    citation: '8 CFR § 274a.13',
    family: 'ecfr',
    topic: 'Employment authorization',
    subtopic: 'Application for employment authorization',
    description: 'Procedures and standards for EAD applications and validity periods.',
    officialUrl: 'https://www.ecfr.gov/current/title-8/chapter-I/subchapter-B/part-274a/section-274a.13',
    status: 'indexed',
    tags: ['EAD', 'I-765'],
  },
  {
    id: 'ecfr-208-7',
    citation: '8 CFR § 208.7',
    family: 'ecfr',
    topic: 'Asylum',
    subtopic: 'Employment authorization for asylum applicants',
    description: 'EAD eligibility and filing windows for individuals with pending asylum applications.',
    officialUrl: 'https://www.ecfr.gov/current/title-8/chapter-I/subchapter-B/part-208/section-208.7',
    status: 'indexed',
    tags: ['asylum', 'EAD', 'I-765'],
  },
  {
    id: 'ecfr-208-4',
    citation: '8 CFR § 208.4',
    family: 'ecfr',
    topic: 'Asylum',
    subtopic: 'Filing the application',
    description: 'Requirements for filing Form I-589 and related procedural rules.',
    officialUrl: 'https://www.ecfr.gov/current/title-8/chapter-I/subchapter-B/part-208/section-208.4',
    status: 'indexed',
    tags: ['asylum', 'I-589'],
  },
  {
    id: 'ecfr-1245-1',
    citation: '8 CFR § 1245.1',
    family: 'ecfr',
    topic: 'Adjustment of status',
    subtopic: 'Eligibility',
    description: 'General eligibility requirements for adjustment of status to lawful permanent resident.',
    officialUrl: 'https://www.ecfr.gov/current/title-8/chapter-I/subchapter-B/part-1245/section-1245.1',
    status: 'indexed',
    tags: ['AOS', 'green card', 'I-485'],
  },
  {
    id: 'ecfr-1245-10',
    citation: '8 CFR § 1245.10',
    family: 'ecfr',
    topic: 'Adjustment of status',
    subtopic: 'Travel and advance parole',
    description: 'Rules on travel while an adjustment application is pending.',
    officialUrl: 'https://www.ecfr.gov/current/title-8/chapter-I/subchapter-B/part-1245/section-1245.10',
    status: 'indexed',
    tags: ['AOS', 'advance parole', 'I-131'],
  },
  {
    id: 'ecfr-214-2',
    citation: '8 CFR § 214.2',
    family: 'ecfr',
    topic: 'Nonimmigrant status',
    subtopic: 'Special requirements by classification',
    description: 'Class-specific rules for F, J, H, L, and other nonimmigrant categories.',
    officialUrl: 'https://www.ecfr.gov/current/title-8/chapter-I/subchapter-B/part-214/section-214.2',
    status: 'indexed',
    tags: ['F-1', 'H-1B', 'OPT', 'status'],
  },
  {
    id: 'ecfr-217-2',
    citation: '8 CFR § 217.2',
    family: 'ecfr',
    topic: 'OPT',
    subtopic: 'F-1 optional practical training',
    description: 'OPT eligibility, reporting, and STEM extension requirements for F-1 students.',
    officialUrl: 'https://www.ecfr.gov/current/title-8/chapter-I/subchapter-B/part-217/section-217.2',
    status: 'indexed',
    tags: ['F-1', 'OPT', 'STEM'],
  },
  {
    id: 'ecfr-316-10',
    citation: '8 CFR § 316.10',
    family: 'ecfr',
    topic: 'Naturalization',
    subtopic: 'Physical presence and residence',
    description: 'Continuous residence and physical presence requirements for naturalization.',
    officialUrl: 'https://www.ecfr.gov/current/title-8/chapter-I/subchapter-B/part-316/section-316.10',
    status: 'indexed',
    tags: ['naturalization', 'N-400', 'citizenship'],
  },
  {
    id: 'ecfr-239-2',
    citation: '8 CFR § 239.2',
    family: 'ecfr',
    topic: 'Removal proceedings',
    subtopic: 'Notice to appear',
    description: 'Content and service requirements for the Notice to Appear (NTA).',
    officialUrl: 'https://www.ecfr.gov/current/title-8/chapter-I/subchapter-B/part-239/section-239.2',
    status: 'indexed',
    tags: ['NTA', 'removal', 'EOIR'],
  },
  {
    id: 'ecfr-244-6',
    citation: '8 CFR § 244.6',
    family: 'ecfr',
    topic: 'TPS',
    subtopic: 'Employment authorization',
    description: 'EAD provisions for Temporary Protected Status beneficiaries.',
    officialUrl: 'https://www.ecfr.gov/current/title-8/chapter-I/subchapter-B/part-244/section-244.6',
    status: 'indexed',
    tags: ['TPS', 'EAD'],
  },
  // INA
  {
    id: 'ina-208',
    citation: 'INA § 208',
    family: 'ina',
    topic: 'Asylum',
    subtopic: 'Asylum and withholding of removal',
    description: 'Statutory basis for asylum eligibility, bars, and withholding of removal.',
    officialUrl: 'https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title8-section1158',
    status: 'indexed',
    tags: ['asylum', 'withholding'],
  },
  {
    id: 'ina-240a',
    citation: 'INA § 240A',
    family: 'ina',
    topic: 'Cancellation of removal',
    subtopic: 'Relief for certain residents and non-permanent residents',
    description: 'Statutory standards for cancellation of removal in immigration court.',
    officialUrl: 'https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title8-section1229b',
    status: 'indexed',
    tags: ['cancellation', 'removal'],
  },
  {
    id: 'ina-274a',
    citation: 'INA § 274A',
    family: 'ina',
    topic: 'Employment',
    subtopic: 'Unlawful employment of aliens',
    description: 'Employer verification and unlawful employment provisions (I-9 framework).',
    officialUrl: 'https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title8-section1324a',
    status: 'indexed',
    tags: ['employment', 'I-9'],
  },
  {
    id: 'ina-316',
    citation: 'INA § 316',
    family: 'ina',
    topic: 'Naturalization',
    subtopic: 'General requirements',
    description: 'Residence, physical presence, good moral character, and English/civics requirements.',
    officialUrl: 'https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title8-section1427',
    status: 'indexed',
    tags: ['naturalization', 'N-400'],
  },
  {
    id: 'ina-101',
    citation: 'INA § 101',
    family: 'ina',
    topic: 'Definitions',
    subtopic: 'Immigration terms',
    description: 'Definitions of admission, immigrant, nonimmigrant, and other core terms.',
    officialUrl: 'https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title8-section1101',
    status: 'indexed',
    tags: ['definitions'],
  },
  // USCIS Forms
  {
    id: 'form-i-765',
    citation: 'Form I-765',
    family: 'uscis-forms',
    topic: 'Employment authorization',
    subtopic: 'Application for Employment Authorization',
    description: 'Official form and instructions for requesting or renewing an EAD.',
    officialUrl: 'https://www.uscis.gov/i-765',
    status: 'indexed',
    tags: ['EAD', 'work permit'],
  },
  {
    id: 'form-i-485',
    citation: 'Form I-485',
    family: 'uscis-forms',
    topic: 'Adjustment of status',
    subtopic: 'Application to Register Permanent Residence',
    description: 'Apply for lawful permanent resident status without leaving the United States.',
    officialUrl: 'https://www.uscis.gov/i-485',
    status: 'indexed',
    tags: ['AOS', 'green card'],
  },
  {
    id: 'form-i-589',
    citation: 'Form I-589',
    family: 'uscis-forms',
    topic: 'Asylum',
    subtopic: 'Application for Asylum and for Withholding of Removal',
    description: 'Application for asylum, withholding of removal, and Convention Against Torture protection.',
    officialUrl: 'https://www.uscis.gov/i-589',
    status: 'indexed',
    tags: ['asylum'],
  },
  {
    id: 'form-i-130',
    citation: 'Form I-130',
    family: 'uscis-forms',
    topic: 'Family-based immigration',
    subtopic: 'Petition for Alien Relative',
    description: 'Establishes a qualifying family relationship for immigrant visa or AOS processing.',
    officialUrl: 'https://www.uscis.gov/i-130',
    status: 'indexed',
    tags: ['family', 'petition'],
  },
  {
    id: 'form-i-539',
    citation: 'Form I-539',
    family: 'uscis-forms',
    topic: 'Status extension / change',
    subtopic: 'Application to Extend/Change Nonimmigrant Status',
    description: 'Extend or change nonimmigrant status (e.g., B, F, J) while in the U.S.',
    officialUrl: 'https://www.uscis.gov/i-539',
    status: 'indexed',
    tags: ['extension', 'change of status'],
  },
  {
    id: 'form-n-400',
    citation: 'Form N-400',
    family: 'uscis-forms',
    topic: 'Naturalization',
    subtopic: 'Application for Naturalization',
    description: 'Apply for U.S. citizenship through naturalization.',
    officialUrl: 'https://www.uscis.gov/n-400',
    status: 'indexed',
    tags: ['citizenship', 'naturalization'],
  },
  // USCIS Policy Manual
  {
    id: 'pm-vol10-e',
    citation: 'USCIS Policy Manual Vol. 10, Part E',
    family: 'uscis-pm',
    topic: 'Employment authorization',
    subtopic: 'Employment Authorization Document',
    description: 'Adjudicator guidance on EAD categories, eligibility, and validity.',
    officialUrl: 'https://www.uscis.gov/policy-manual/volume-10-part-e',
    status: 'indexed',
    tags: ['EAD', 'policy'],
  },
  {
    id: 'pm-vol12',
    citation: 'USCIS Policy Manual Vol. 12',
    family: 'uscis-pm',
    topic: 'Naturalization',
    subtopic: 'Citizenship and Naturalization',
    description: 'Policy guidance on naturalization requirements and adjudication.',
    officialUrl: 'https://www.uscis.gov/policy-manual/volume-12',
    status: 'indexed',
    tags: ['N-400', 'citizenship'],
  },
  {
    id: 'pm-vol8',
    citation: 'USCIS Policy Manual Vol. 8',
    family: 'uscis-pm',
    topic: 'Admissibility',
    subtopic: 'Grounds of inadmissibility',
    description: 'Guidance on health, criminal, security, and public charge inadmissibility.',
    officialUrl: 'https://www.uscis.gov/policy-manual/volume-8',
    status: 'indexed',
    tags: ['inadmissibility', 'I-485'],
  },
  {
    id: 'pm-vol1',
    citation: 'USCIS Policy Manual Vol. 1',
    family: 'uscis-pm',
    topic: 'General policies',
    subtopic: 'Agency structure and jurisdiction',
    description: 'Foundational USCIS policy organization and general adjudication principles.',
    officialUrl: 'https://www.uscis.gov/policy-manual/volume-1',
    status: 'indexed',
    tags: ['policy'],
  },
  // USCIS official pages
  {
    id: 'page-opt',
    citation: 'USCIS — Optional Practical Training (OPT)',
    family: 'uscis-pages',
    topic: 'F-1 students',
    subtopic: 'OPT overview',
    description: 'Agency overview of OPT types, timelines, and reporting obligations.',
    officialUrl: 'https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-opt-for-f-1-students',
    status: 'indexed',
    tags: ['F-1', 'OPT'],
  },
  {
    id: 'page-h1b',
    citation: 'USCIS — H-1B Specialty Occupations',
    family: 'uscis-pages',
    topic: 'Employment visas',
    subtopic: 'H-1B program',
    description: 'Cap registration, eligibility, and employer requirements for H-1B workers.',
    officialUrl: 'https://www.uscis.gov/working-in-the-united-states/temporary-workers/h-1b-specialty-occupations',
    status: 'indexed',
    tags: ['H-1B'],
  },
  {
    id: 'page-green-card',
    citation: 'USCIS — Green Card (Permanent Residence)',
    family: 'uscis-pages',
    topic: 'Permanent residence',
    subtopic: 'Overview',
    description: 'Paths to lawful permanent residence and maintaining permanent resident status.',
    officialUrl: 'https://www.uscis.gov/green-card',
    status: 'indexed',
    tags: ['green card', 'LPR'],
  },
  // Preview / planned
  {
    id: 'fr-tps-example',
    citation: 'Federal Register — TPS designation notice',
    family: 'federal-register',
    topic: 'TPS',
    subtopic: 'Designation / extension',
    description: 'Illustrative Federal Register notice for TPS country designations (feed preview).',
    officialUrl: 'https://www.federalregister.gov/',
    status: 'preview',
    tags: ['TPS', 'Federal Register'],
  },
  {
    id: 'bia-precedent',
    citation: 'BIA Precedent Decision (sample)',
    family: 'bia',
    topic: 'Asylum',
    subtopic: 'Credibility standards',
    description: 'Precedent decisions will be indexed post-MVP for removal and relief cases.',
    officialUrl: 'https://www.justice.gov/eoir/board-of-immigration-appeals',
    status: 'planned',
    tags: ['BIA', 'precedent'],
  },
]

export function catalogStats() {
  const indexed = SOURCE_CATALOG.filter((s) => s.status === 'indexed').length
  const families = new Set(SOURCE_CATALOG.map((s) => s.family)).size
  return { total: SOURCE_CATALOG.length, indexed, families }
}
