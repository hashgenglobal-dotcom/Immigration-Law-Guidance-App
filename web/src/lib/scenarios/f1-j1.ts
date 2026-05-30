import { buildGuide } from './buildGuide'
import type { Scenario } from '../scenarioTypes'

const USCIS_STUDENTS =
  'https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors'
const SEVP = 'https://studyinthestates.dhs.gov/'
const USCIS_OPT =
  'https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-opt-for-f-1-students'
const I765 = 'https://www.uscis.gov/i-765'
const I983 = 'https://www.ice.gov/sevis/practical-training'
const J1 = 'https://j1visa.state.gov/'
const CAP_GAP =
  'https://www.uscis.gov/working-in-the-united-states/temporary-workers/h-1b-specialty-occupations/h-1b-cap-gap-extension-for-f-1-students'

export const f1J1Guides: Scenario[] = [
  buildGuide({
    id: 'f1-status-basics',
    title: 'F-1 status basics',
    category: 'f1-j1',
    riskLevel: 'low',
    description:
      'Understand enrollment requirements, on-campus work limits, grace periods, and how to maintain lawful F-1 status through your program.',
    overview:
      'F-1 status is tied to a SEVP-certified school and full-time study. Work, travel, and program changes must follow SEVP and USCIS rules. Falling out of status can affect OPT, H-1B, and future benefits.',
    steps: [
      'Maintain full-time enrollment unless your DSO authorizes a reduced course load.',
      'Limit on-campus work to 20 hours per week while school is in session unless your DSO says otherwise.',
      'Do not work off-campus without CPT, OPT, or other authorization.',
      'Report address and employment changes to your DSO within SEVIS deadlines.',
      'Before dropping below full time, transferring, or extending, obtain an updated I-20 from your DSO.',
    ],
    timeline:
      'Status is continuous while enrolled and compliant. After program completion you may have a 60-day grace period to depart, change status, or begin approved OPT—confirm exact dates on your I-20.',
    tips: ['Keep copies of every signed I-20 and SEVIS printout.', 'Never work off-campus without written authorization.'],
    sources: [
      { title: 'USCIS — Students and Exchange Visitors', citation: 'USCIS F-1', url: USCIS_STUDENTS, type: 'guidance' },
      { title: 'Study in the States (SEVP)', citation: 'SEVP', url: SEVP, type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'post-completion-opt',
    title: 'Post-completion OPT (Form I-765)',
    category: 'f1-j1',
    riskLevel: 'medium',
    description:
      'File for Optional Practical Training after graduation: DSO recommendation, I-765 filing window, EAD card, and when employment may begin.',
    overview:
      'Post-completion OPT allows eligible F-1 students to work in a job related to their major after finishing their program. You need a DSO recommendation in SEVIS before USCIS can approve Form I-765.',
    steps: [
      'Request post-completion OPT recommendation from your DSO and receive a signed I-20 with OPT notation.',
      'File Form I-765 with USCIS within the filing window on current USCIS OPT instructions.',
      'Select the correct eligibility category on I-765 per the current form instructions.',
      'Wait for approval and EAD before starting employment unless USCIS rules allow otherwise.',
      'Report employment and address changes to your DSO; track unemployment days during OPT.',
    ],
    timeline:
      'Apply up to 90 days before and within 60 days after program end (verify current USCIS guidance). Processing times vary; file early. Standard post-completion OPT is up to 12 months.',
    tips: ['Unemployment during OPT is limited—track days carefully.', 'Keep proof that work is related to your major.'],
    sources: [
      { title: 'USCIS — OPT for F-1 Students', citation: 'USCIS OPT', url: USCIS_OPT, type: 'guidance' },
      { title: 'Form I-765', citation: 'Form I-765', url: I765, type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'stem-opt-extension',
    title: 'STEM OPT extension (I-983 + I-765)',
    category: 'f1-j1',
    riskLevel: 'medium',
    description:
      'Extend OPT by 24 months with a qualifying STEM degree, E-Verify employer, and completed Form I-983 training plan.',
    overview:
      'The STEM OPT extension adds up to 24 months of work authorization for F-1 students with a qualifying STEM degree from an accredited SEVP school. Your employer must participate in E-Verify and complete Form I-983 with you.',
    steps: [
      'Confirm your degree appears on the STEM Designated Degree Program List.',
      'Verify your employer is enrolled in E-Verify and willing to complete Form I-983.',
      'Complete and sign Form I-983 (training plan) with your employer; update when material changes occur.',
      'Request a STEM OPT I-20 from your DSO with required signatures and dates.',
      'File Form I-765 before your current OPT EAD expires, within USCIS filing windows.',
    ],
    timeline:
      'File I-765 up to 90 days before OPT expiration. STEM extension provides up to 24 additional months. Two lifetime STEM extensions are allowed with a second qualifying degree.',
    tips: ['Material changes to training require an updated I-983.', 'Self-employment is not permitted on STEM OPT.'],
    sources: [
      { title: 'USCIS — STEM OPT', citation: 'USCIS STEM', url: USCIS_OPT, type: 'guidance' },
      { title: 'Form I-983 information', citation: 'I-983', url: I983, type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'cpt-authorization',
    title: 'Curricular Practical Training (CPT)',
    category: 'f1-j1',
    riskLevel: 'medium',
    description:
      'Work authorization tied to your curriculum—internships, co-ops, and required practical training before graduation.',
    overview:
      'CPT allows F-1 students to accept off-campus employment that is an integral part of an established curriculum. Authorization is granted by your DSO on your I-20, not by USCIS.',
    steps: [
      'Confirm the position is required or integral to your program (internship, co-op, practicum).',
      'Obtain a job offer letter describing duties, dates, and employer information.',
      'Meet with your DSO to request CPT authorization before starting work.',
      'Receive an updated I-20 with CPT notation showing employer, dates, and part-time/full-time status.',
      'Begin work only on or after the CPT start date on your I-20.',
    ],
    timeline:
      'CPT can be part-time (≤20 hrs/week during school) or full-time during authorized periods. One year of full-time CPT may eliminate post-completion OPT eligibility—confirm with your DSO.',
    tips: ['Unauthorized employment ends lawful status.', 'CPT must be completed before program end date.'],
    sources: [
      { title: 'USCIS — CPT overview', citation: 'USCIS CPT', url: USCIS_STUDENTS, type: 'guidance' },
      { title: 'Study in the States — CPT', citation: 'SEVP CPT', url: SEVP, type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'h1b-cap-gap',
    title: 'H-1B cap-gap extension',
    category: 'f1-j1',
    riskLevel: 'medium',
    description:
      'Bridge F-1/OPT status when an H-1B petition is pending and your EAD or grace period would otherwise expire before October 1.',
    overview:
      'Cap-gap allows certain F-1 students whose OPT or grace period expires after an H-1B petition is filed to remain in status until H-1B begins on October 1, if the petition is selected and pending or approved.',
    steps: [
      'Ensure your employer timely files an H-1B petition subject to the cap while you are in valid F-1 status.',
      'Confirm the petition is selected in the cap lottery (if applicable) and remains pending or approved.',
      'Work with your DSO to update SEVIS for cap-gap if your OPT EAD expires before October 1.',
      'Do not travel outside the U.S. without understanding re-entry risks during cap-gap.',
      'Transition to H-1B status on the approved start date (typically October 1).',
    ],
    timeline:
      'Cap-gap typically covers the period from OPT expiration through September 30 if requirements are met. H-1B status generally begins October 1.',
    tips: ['Cap-gap does not apply to all H-1B filings—confirm cap-subject vs. cap-exempt.', 'Travel during cap-gap can be risky—consult your DSO.'],
    sources: [
      { title: 'USCIS — H-1B cap-gap', citation: 'Cap-gap', url: CAP_GAP, type: 'guidance' },
      { title: 'USCIS — H-1B overview', citation: 'H-1B', url: 'https://www.uscis.gov/working-in-the-united-states/h-1b-specialty-occupations', type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'j1-status-basics',
    title: 'J-1 exchange visitor status',
    category: 'f1-j1',
    riskLevel: 'low',
    description:
      'Program categories, DS-2019 maintenance, work authorization, and two-year home residency rule basics for J-1 scholars and students.',
    overview:
      'J-1 status is for approved exchange programs (research, training, au pair, etc.). Your program sponsor issues Form DS-2019 and sets program dates, work permissions, and any 212(e) home residency requirement.',
    steps: [
      'Review your DS-2019 for program category, start/end dates, and work authorization notes.',
      'Maintain health insurance meeting J-1 program requirements.',
      'Obtain sponsor approval before any employment or program changes.',
      'Report address changes to your sponsor within required timeframes.',
      'Before program end, plan for grace period, departure, or change of status.',
    ],
    timeline:
      'Program dates are on DS-2019. A 30-day grace period may apply after program completion—confirm with your sponsor.',
    tips: ['212(e) two-year rule may block H/L status or green card until waived or fulfilled.', 'Each sponsor has specific rules—follow your RO/ARO guidance.'],
    sources: [
      { title: 'Exchange Visitor Program', citation: 'J-1', url: J1, type: 'guidance' },
      { title: 'USCIS — Exchange Visitors', citation: 'USCIS J-1', url: USCIS_STUDENTS, type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'j1-waiver-212e',
    title: 'J-1 waiver (212(e) home residency)',
    category: 'f1-j1',
    riskLevel: 'high',
    description:
      'Navigate the two-year home physical presence requirement and waiver options before changing to H-1B or permanent residency.',
    overview:
      'Some J-1 participants are subject to INA 212(e), requiring two years of physical presence in the home country before obtaining H, L, or immigrant visas. Waivers are available through several bases but are discretionary.',
    steps: [
      'Determine if 212(e) applies by checking your DS-2019 and visa stamp notations.',
      'Identify an appropriate waiver basis (no objection, persecution, hardship, interested agency, etc.).',
      'Gather supporting documents for the waiver application to the Department of State.',
      'If DOS recommends a waiver, USCIS or other agencies may need to approve.',
      'Do not change status or adjust until the waiver is fully approved.',
    ],
    timeline:
      'Waiver processing can take several months to over a year depending on basis and agency review. Plan well before any status change deadline.',
    tips: ['212(e) is case-specific—verify on every DS-2019 renewal.', 'Some waiver bases require a home country no-objection letter.'],
    sources: [
      { title: 'DOS — J-1 waiver', citation: '212(e) waiver', url: 'https://j1visa.state.gov/basics/waiver-of-the-exchange-visitor-two-year-home-country-physical-presence-requirement', type: 'guidance' },
      { title: 'USCIS — 212(e) information', citation: 'INA 212(e)', url: USCIS_STUDENTS, type: 'statute' },
    ],
  }),
  buildGuide({
    id: 'f1-to-h1b-change',
    title: 'F-1 to H-1B change of status',
    category: 'f1-j1',
    riskLevel: 'medium',
    description:
      'Move from student status to H-1B specialty occupation without leaving the U.S., including cap timing and maintaining status during processing.',
    overview:
      'An employer may file Form I-129 to change your status from F-1 to H-1B while you remain in the United States. Cap-subject cases require lottery selection; cap-gap may bridge OPT expiration.',
    steps: [
      'Secure an H-1B job offer in a specialty occupation from a willing petitioner.',
      'Employer registers for cap lottery (if cap-subject) and files I-129 upon selection.',
      'Request change of status on I-129 rather than consular processing if remaining in the U.S.',
      'Maintain valid F-1 status until H-1B is approved and effective.',
      'Begin H-1B employment only on the approved start date.',
    ],
    timeline:
      'Cap registration is typically March; selected petitions filed by June 30. H-1B start is usually October 1. Premium processing may shorten adjudication time.',
    tips: ['Travel while I-129 is pending can abandon the change-of-status request.', 'Cap-exempt employers (universities, certain nonprofits) skip the lottery.'],
    sources: [
      { title: 'USCIS — H-1B', citation: 'H-1B', url: 'https://www.uscis.gov/working-in-the-united-states/h-1b-specialty-occupations', type: 'guidance' },
      { title: 'Form I-129', citation: 'I-129', url: 'https://www.uscis.gov/i-129', type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'f1-reinstatement',
    title: 'F-1 reinstatement to lawful status',
    category: 'f1-j1',
    riskLevel: 'high',
    description:
      'Recover F-1 status after a status violation by filing Form I-539 with USCIS or through a DSO in limited cases.',
    overview:
      'If you fall out of F-1 status (e.g., unauthorized employment, failure to enroll full time), reinstatement may be possible if you meet eligibility criteria and file timely with a DSO recommendation.',
    steps: [
      'Meet immediately with your DSO to assess whether reinstatement is possible.',
      'Document the violation, reasons, and that you are not deportable on other grounds.',
      'Obtain a new I-20 with reinstatement recommendation from your DSO.',
      'File Form I-539 with USCIS including fee, I-20, explanation letter, and supporting evidence.',
      'Do not work or travel until reinstatement is approved unless advised otherwise.',
    ],
    timeline:
      'File as soon as possible after discovering the violation. USCIS processing times vary; remaining in the U.S. while pending has risks if denied.',
    tips: ['Reinstatement is discretionary—not guaranteed.', 'Some violations may require departure and consular re-entry instead.'],
    sources: [
      { title: 'USCIS — Reinstatement', citation: 'Reinstatement', url: USCIS_STUDENTS, type: 'guidance' },
      { title: 'Form I-539', citation: 'I-539', url: 'https://www.uscis.gov/i-539', type: 'guidance' },
    ],
  }),
]
