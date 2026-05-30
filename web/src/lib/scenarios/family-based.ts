import { buildGuide } from './buildGuide'
import type { Scenario } from '../scenarioTypes'

const FAMILY = 'https://www.uscis.gov/family'
const I130 = 'https://www.uscis.gov/i-130'
const I751 = 'https://www.uscis.gov/i-751'
const K1 = 'https://www.uscis.gov/family/family-of-us-citizens/fiancee-visa'

export const familyBasedGuides: Scenario[] = [
  buildGuide({
    id: 'marriage-green-card',
    title: 'Marriage-based green card',
    category: 'family-based',
    riskLevel: 'medium',
    description:
      'U.S. citizen or permanent resident petitions for a spouse with I-130 and, if eligible, I-485 or consular processing.',
    overview:
      'A U.S. citizen or lawful permanent resident may petition for a foreign national spouse. Immediate relatives of citizens have no visa backlog; LPR spouses wait for visa availability. Evidence of bona fide marriage is critical.',
    steps: [
      'U.S. petitioner files Form I-130 with proof of citizenship/LPR status and marriage validity.',
      'If spouse is in the U.S. and eligible, file Form I-485 concurrently (citizen) or when visa is current (LPR).',
      'Submit bona fide marriage evidence: joint finances, lease, photos, affidavits.',
      'Attend biometrics and interview—be prepared to answer questions about relationship.',
      'If approved, spouse receives conditional or permanent resident status depending on marriage length.',
    ],
    timeline:
      'Citizen spouse in U.S.: often 10–24 months to interview. Consular cases vary by embassy. LPR petitions wait for Visa Bulletin priority date.',
    tips: ['Conditional GC (2 years) if marriage is less than 2 years old at approval.', 'Fraud findings have severe consequences—document genuine relationship.'],
    sources: [
      { title: 'USCIS — Family of U.S. citizens', citation: 'Family', url: FAMILY, type: 'guidance' },
      { title: 'Form I-130', citation: 'I-130', url: I130, type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'k1-fiance-visa',
    title: 'K-1 fiancé visa',
    category: 'family-based',
    riskLevel: 'medium',
    description:
      'U.S. citizens bring a foreign fiancé to marry within 90 days of U.S. entry, then apply for adjustment of status.',
    overview:
      'The K-1 visa allows a U.S. citizen’s fiancé to enter the U.S. to marry within 90 days. After marriage, the foreign spouse files Form I-485 for a green card.',
    steps: [
      'U.S. citizen files Form I-129F with evidence of in-person meeting within two years and intent to marry.',
      'Upon I-129F approval, case goes to National Visa Center and then U.S. embassy abroad.',
      'Fiancé attends medical exam and visa interview with civil documents.',
      'Enter U.S. on K-1, marry within 90 days of entry.',
      'File Form I-485 after marriage with joint evidence and attend AOS interview.',
    ],
    timeline:
      'I-129F processing: months. Consular processing: additional months. Must marry within 90 days of U.S. entry on K-1.',
    tips: ['Children may qualify for K-2 derivative visas.', 'Cannot adjust status through anyone other than the petitioning citizen fiancé.'],
    sources: [
      { title: 'USCIS — K-1 visa', citation: 'K-1', url: K1, type: 'guidance' },
      { title: 'Form I-129F', citation: 'I-129F', url: 'https://www.uscis.gov/i-129f', type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'i751-remove-conditions',
    title: 'Removing conditions on marriage GC (I-751)',
    category: 'family-based',
    riskLevel: 'medium',
    description:
      'Convert a 2-year conditional green card to permanent status by proving the marriage is genuine or qualifying for a waiver.',
    overview:
      'Conditional permanent residents who obtained status through marriage must file Form I-751 within the 90-day window before the conditional card expires to remove conditions on residence.',
    steps: [
      'File Form I-751 jointly with spouse during the 90-day period before card expiration.',
      'Include evidence of ongoing bona fide marriage since conditional residency began.',
      'If divorced or abused, explore waiver filing without spouse’s cooperation.',
      'Attend biometrics; respond to RFE or interview if scheduled.',
      'Receive 10-year green card upon approval.',
    ],
    timeline:
      'File within 90 days before conditional GC expires. Receipt extends status while pending. Adjudication: months to over a year.',
    tips: ['Failure to file on time can terminate status.', 'Waiver cases require strong evidence of good-faith marriage or abuse.'],
    sources: [
      { title: 'Form I-751', citation: 'I-751', url: I751, type: 'guidance' },
      { title: 'USCIS — Remove conditions', citation: 'I-751 guide', url: FAMILY, type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'parent-i130-petition',
    title: 'Parent petition (I-130)',
    category: 'family-based',
    riskLevel: 'low',
    description:
      'U.S. citizens age 21+ may petition for parents as immediate relatives with no annual visa cap.',
    overview:
      'Parents of U.S. citizens are immediate relatives. Only citizens (not LPRs) may petition for parents. If parents are in the U.S., adjustment may be possible if they entered lawfully or qualify for 245(i) or other relief.',
    steps: [
      'Confirm petitioner is U.S. citizen age 21 or older.',
      'File Form I-130 with birth certificate proving parent-child relationship and proof of citizenship.',
      'If parent is abroad, proceed through NVC and consular immigrant visa process.',
      'If parent is in U.S. and eligible, file Form I-485 concurrently or when I-130 is approved.',
      'Parent attends interview with civil documents and medical exam results.',
    ],
    timeline:
      'Immediate relative cases: I-130 and I-485 often processed in roughly 12–24 months if in U.S. Consular cases depend on embassy schedules.',
    tips: ['Parents who entered without inspection may need consular processing and waiver.', 'Affidavit of Support (I-864) required for most cases.'],
    sources: [
      { title: 'USCIS — Family', citation: 'Family', url: FAMILY, type: 'guidance' },
      { title: 'Form I-130', citation: 'I-130', url: I130, type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'unmarried-adult-child',
    title: 'Unmarried adult child petition (F1/F3)',
    category: 'family-based',
    riskLevel: 'medium',
    description:
      'Petition unmarried sons and daughters of U.S. citizens (F1) or permanent residents (F3) with significant wait times.',
    overview:
      'Family preference categories F1 (citizen’s unmarried adult children) and F3 (LPR’s unmarried adult children) are subject to Visa Bulletin backlogs, especially for Mexico and Philippines.',
    steps: [
      'File Form I-130 with proof of relationship and petitioner’s status.',
      'Track priority date on Visa Bulletin for F1 or F3 category.',
      'Beneficiary must remain unmarried to stay in category—marriage changes category or voids F3 eligibility.',
      'When priority date is current, complete NVC processing or file I-485 if in U.S. and eligible.',
      'Attend immigrant visa interview or AOS interview.',
    ],
    timeline:
      'Wait times vary from years to decades depending on category and country. Monitor Visa Bulletin monthly.',
    tips: ['Age-out protection may apply under CSPA—calculate before beneficiary turns 21.', 'Marriage while waiting may require a different category or new petition.'],
    sources: [
      { title: 'Visa Bulletin', citation: 'DOS VB', url: 'https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin.html', type: 'guidance' },
      { title: 'Form I-130', citation: 'I-130', url: I130, type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'sibling-petition-f4',
    title: 'Sibling petition (F4)',
    category: 'family-based',
    riskLevel: 'medium',
    description:
      'U.S. citizens may petition for brothers and sisters in the F4 category—often the longest family preference wait.',
    overview:
      'Sibling petitions (F4) are available only to U.S. citizens petitioning for brothers or sisters. Wait times are among the longest in the family system, particularly for India, Mexico, and Philippines.',
    steps: [
      'U.S. citizen files I-130 with birth certificates showing common parentage.',
      'Monitor F4 priority date on Visa Bulletin—waits can exceed 10–20 years for some countries.',
      'Beneficiary must wait abroad or maintain independent lawful status in the U.S.',
      'When date is current, complete NVC or I-485 process.',
      'Attend interview with full civil and financial documentation.',
    ],
    timeline:
      'F4 waits are measured in years to decades. Priority date locks in on I-130 filing date.',
    tips: ['LPRs cannot petition for siblings—must naturalize first.', 'Derivative beneficiaries (spouse/children) may be included on the petition.'],
    sources: [
      { title: 'USCIS — Family preference', citation: 'F4', url: FAMILY, type: 'guidance' },
      { title: 'Visa Bulletin', citation: 'DOS VB', url: 'https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin.html', type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'cspa-age-out-protection',
    title: 'Child Status Protection Act (CSPA)',
    category: 'family-based',
    riskLevel: 'high',
    description:
      'Calculate whether a child can still immigrate with a parent despite turning 21 while waiting for a visa number.',
    overview:
      'CSPA provides a formula to determine a child’s “CSPA age” by subtracting petition processing time and certain wait periods from biological age. If CSPA age is under 21 when visa is available, the child may remain a derivative.',
    steps: [
      'Identify the relevant date: I-130 approval, visa availability, or I-485 filing depending on case type.',
      'Calculate days petition was pending with USCIS and subtract from child’s age at time of visa availability.',
      'For employment cases, subtract time I-140 was pending if applicable.',
      'Ensure child seeks to acquire permanent residence within one year of visa availability (with exceptions).',
      'Document CSPA calculation in cover letter if age is close to 21.',
    ],
    timeline:
      'Must act within one year of visa becoming available to “seek to acquire” unless an exception applies. Calculation is case-specific.',
    tips: ['CSPA does not freeze age indefinitely—seek to acquire promptly.', 'Consult current USCIS policy on CSPA for your category.'],
    sources: [
      { title: 'USCIS — CSPA', citation: 'CSPA', url: 'https://www.uscis.gov/green-card/green-card-processes-and-procedures/child-status-protection-act-cspa', type: 'guidance' },
      { title: 'INA §203(h)', citation: 'CSPA statute', url: 'https://www.uscis.gov/legal-resources/immigration-and-nationality-act', type: 'statute' },
    ],
  }),
  buildGuide({
    id: 'affidavit-of-support-i864',
    title: 'Affidavit of Support (I-864)',
    category: 'family-based',
    riskLevel: 'low',
    description:
      'Financial sponsor commitment required for most family and employment-based immigrants to show they will not become a public charge.',
    overview:
      'Form I-864 is a legally binding contract in which the sponsor demonstrates income at or above 125% of the Federal Poverty Guidelines (or uses assets/joint sponsors).',
    steps: [
      'Primary sponsor completes Form I-864 with tax returns, W-2s, and employment letter.',
      'Compare household income to poverty guidelines for household size including immigrant.',
      'If income is insufficient, add a joint sponsor or count qualifying assets.',
      'Submit signed I-864 with AOS or NVC document package.',
      'Understand ongoing support obligations until immigrant becomes citizen or earns 40 quarters.',
    ],
    timeline:
      'Prepared during I-485 or NVC stage. Must use most recent tax year available—typically last three years of returns submitted.',
    tips: ['Sponsor must be U.S. citizen or LPR domiciled in the U.S.', 'I-864 enforcement can continue for years after approval.'],
    sources: [
      { title: 'Form I-864', citation: 'I-864', url: 'https://www.uscis.gov/i-864', type: 'guidance' },
      { title: 'USCIS — Public charge', citation: 'I-864 guide', url: FAMILY, type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'i601a-provisional-waiver',
    title: 'Provisional unlawful presence waiver (I-601A)',
    category: 'family-based',
    riskLevel: 'high',
    description:
      'Request waiver of unlawful presence before leaving the U.S. for consular immigrant visa interview.',
    overview:
      'Certain immediate relatives of U.S. citizens who accrued unlawful presence may apply for a provisional waiver (I-601A) before departing for consular processing, reducing time separated from family abroad.',
    steps: [
      'Confirm eligibility: immediate relative of U.S. citizen, unlawful presence only, approved I-130.',
      'Demonstrate extreme hardship to U.S. citizen spouse or parent if waiver denied.',
      'File Form I-601A with extensive hardship evidence while in the U.S.',
      'Upon provisional approval, attend immigrant visa interview abroad.',
      'If visa issued, re-enter as lawful permanent resident.',
    ],
    timeline:
      'I-601A processing: months. After approval, consular interview scheduled abroad. Unlawful presence triggers 3/10-year bars without waiver.',
    tips: ['Departure triggers the bar—do not leave until I-601A strategy is confirmed.', 'Hardship must be to qualifying relative, not the applicant.'],
    sources: [
      { title: 'USCIS — I-601A', citation: 'I-601A', url: 'https://www.uscis.gov/i-601a', type: 'guidance' },
      { title: 'USCIS — Waivers', citation: 'Waivers', url: FAMILY, type: 'guidance' },
    ],
  }),
]
