import { buildGuide } from './buildGuide'
import type { Scenario } from '../scenarioTypes'

const PERM = 'https://www.dol.gov/agencies/eta/foreign-labor/programs/permanent-employment'
const I140 = 'https://www.uscis.gov/green-card/green-card-eligibility/green-card-for-employment-based-immigrants'
const I485 = 'https://www.uscis.gov/green-card/green-card-processes-and-procedures/adjustment-of-status'
const NIW = 'https://www.uscis.gov/working-in-the-united-states/permanent-workers/employment-based-immigration-second-preference-eb-2/national-interest-waiver'

export const employmentPermanentGuides: Scenario[] = [
  buildGuide({
    id: 'perm-labor-certification',
    title: 'PERM labor certification overview',
    category: 'employment-permanent',
    riskLevel: 'medium',
    description:
      'Employer-sponsored green card step one: test the U.S. labor market and certify no qualified U.S. workers are available.',
    overview:
      'Most EB-2 and EB-3 employment-based cases require PERM labor certification from the Department of Labor before USCIS can approve an immigrant petition. The employer must recruit and document good-faith hiring efforts.',
    steps: [
      'Employer obtains prevailing wage determination from DOL for the position.',
      'Conduct required recruitment (job order, newspaper ads, internal posting, etc.).',
      'Document all applicants and lawful rejection reasons in a recruitment report.',
      'File ETA Form 9089 electronically with DOL after recruitment period ends.',
      'Upon PERM approval, employer files Form I-140 with USCIS within validity period.',
    ],
    timeline:
      'Prevailing wage: weeks to months. Recruitment: minimum 60 days. PERM adjudication: several months. PERM approval is valid for 180 days for I-140 filing.',
    tips: ['Recruitment must follow exact DOL rules—errors cause denial.', 'Job requirements must match actual minimum requirements for the role.'],
    sources: [
      { title: 'DOL — PERM', citation: 'PERM', url: PERM, type: 'guidance' },
      { title: 'USCIS — Employment-based GC', citation: 'EB', url: I140, type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'eb2-advanced-degree',
    title: 'EB-2 advanced degree / exceptional ability',
    category: 'employment-permanent',
    riskLevel: 'medium',
    description:
      'Second preference employment category for advanced degree professionals or those with exceptional ability in the sciences, arts, or business.',
    overview:
      'EB-2 requires an advanced degree (or bachelor’s plus five years progressive experience) or exceptional ability. Most cases need PERM and a job offer; NIW cases waive PERM and job offer.',
    steps: [
      'Confirm eligibility: advanced degree or exceptional ability under regulatory criteria.',
      'Complete PERM labor certification unless NIW applies.',
      'Employer files Form I-140 with evidence of ability to pay and beneficiary qualifications.',
      'Check Visa Bulletin for priority date and visa availability.',
      'File I-485 or consular process when priority date is current.',
    ],
    timeline:
      'PERM + I-140 can take 1–2+ years. Wait for priority date depends on country of chargeability and Visa Bulletin.',
    tips: ['Exceptional ability requires meeting at least three of six regulatory criteria.', 'Advanced degree equivalency rules are strict—document carefully.'],
    sources: [
      { title: 'USCIS — EB-2', citation: 'EB-2', url: I140, type: 'guidance' },
      { title: 'Visa Bulletin', citation: 'DOS VB', url: 'https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin.html', type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'eb2-niw',
    title: 'EB-2 National Interest Waiver (NIW)',
    category: 'employment-permanent',
    riskLevel: 'high',
    description:
      'Self-petition for a green card without PERM or employer sponsor if your work is in the national interest.',
    overview:
      'The NIW waives the job offer and PERM requirements for EB-2 beneficiaries whose proposed endeavor has substantial merit and national importance, who are well positioned to advance it, and for whom a waiver benefits the U.S.',
    steps: [
      'Document your proposed endeavor with letters, publications, patents, or business plans.',
      'Show substantial merit and national importance using the Matter of Dhanasar framework.',
      'Demonstrate you are well positioned to advance the endeavor (education, track record, plan).',
      'Argue it benefits the U.S. to waive the job offer and labor certification requirements.',
      'Self-file Form I-140 with comprehensive evidence; premium processing optional.',
    ],
    timeline:
      'I-140 NIW adjudication varies widely (months to over a year). After approval, wait for priority date before I-485 or consular processing.',
    tips: ['NIW is evidence-heavy—plan a strong petition package.', 'Entrepreneurs and researchers often use NIW but must meet all prongs.'],
    sources: [
      { title: 'USCIS — EB-2 NIW', citation: 'NIW', url: NIW, type: 'guidance' },
      { title: 'Form I-140', citation: 'I-140', url: 'https://www.uscis.gov/i-140', type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'eb3-skilled-worker',
    title: 'EB-3 skilled worker',
    category: 'employment-permanent',
    riskLevel: 'medium',
    description:
      'Third preference category for skilled workers, professionals, and other workers with employer sponsorship.',
    overview:
      'EB-3 covers skilled workers (2+ years training/experience), professionals (bachelor’s degree), and other workers (unskilled, less than 2 years). PERM is required for most EB-3 cases.',
    steps: [
      'Employer obtains prevailing wage and completes PERM recruitment.',
      'File and receive approved ETA Form 9089.',
      'Employer files Form I-140 with job offer, PERM approval, and ability-to-pay evidence.',
      'Monitor Visa Bulletin for EB-3 priority dates (often longer waits for India/China).',
      'File I-485 adjustment or consular immigrant visa when priority date is current.',
    ],
    timeline:
      'PERM and I-140: 1–2 years typical. Priority date wait can be several years depending on country.',
    tips: ['“Other worker” subcategory has separate Visa Bulletin lines.', 'Job must remain available through I-140 approval.'],
    sources: [
      { title: 'USCIS — EB-3', citation: 'EB-3', url: I140, type: 'guidance' },
      { title: 'DOL — PERM', citation: 'PERM', url: PERM, type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'eb1a-extraordinary',
    title: 'EB-1A extraordinary ability',
    category: 'employment-permanent',
    riskLevel: 'high',
    description:
      'First preference self-petition for individuals with extraordinary ability—no PERM or job offer required.',
    overview:
      'EB-1A allows self-petitioning if you demonstrate extraordinary ability through sustained national or international acclaim and intend to continue work in your field in the U.S.',
    steps: [
      'Gather evidence meeting at least three of ten regulatory criteria (or one major award).',
      'Prepare a final merits determination showing acclaim at the very top of the field.',
      'Self-file Form I-140 with indexed exhibits and expert letters.',
      'Upon approval, check Visa Bulletin (EB-1 is often current for many countries).',
      'File I-485 concurrently if priority date is current and you are in the U.S.',
    ],
    timeline:
      'I-140 adjudication: months with premium processing. EB-1 priority dates are often current, enabling faster green card completion.',
    tips: ['Comparable evidence allowed if criteria do not readily apply.', 'Quality of letters and objective evidence matters more than quantity.'],
    sources: [
      { title: 'USCIS — EB-1A', citation: 'EB-1A', url: I140, type: 'guidance' },
      { title: 'Form I-140', citation: 'I-140', url: 'https://www.uscis.gov/i-140', type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'i140-immigrant-petition',
    title: 'Form I-140 immigrant petition',
    category: 'employment-permanent',
    riskLevel: 'medium',
    description:
      'Employer or self-petitioner files to classify a foreign worker for an employment-based immigrant visa category.',
    overview:
      'Form I-140 is the immigrant petition that establishes eligibility for an EB category. It must include proof of beneficiary qualifications, job offer (unless NIW/EB-1A), and employer ability to pay.',
    steps: [
      'Determine correct EB category (EB-1, EB-2, EB-3) and whether PERM is required.',
      'Collect beneficiary credentials, experience letters, and licensing.',
      'Employer submits ability-to-pay evidence (tax returns, annual reports, payroll).',
      'File I-140 with correct filing fee and supporting documents.',
      'Retain priority date from I-140 approval for future I-485 or consular processing.',
    ],
    timeline:
      'Standard processing varies; premium processing available for most I-140 categories. Priority date is established on filing date.',
    tips: ['Priority date retention rules apply when changing jobs after I-140 approval.', 'Duplicate filings waste fees—confirm category before filing.'],
    sources: [
      { title: 'Form I-140', citation: 'I-140', url: 'https://www.uscis.gov/i-140', type: 'guidance' },
      { title: 'USCIS — Employment-based GC', citation: 'EB', url: I140, type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'i485-adjustment-of-status',
    title: 'I-485 adjustment of status',
    category: 'employment-permanent',
    riskLevel: 'medium',
    description:
      'Apply for a green card from inside the United States when a visa number is available.',
    overview:
      'Form I-485 allows eligible applicants physically present in the U.S. to become lawful permanent residents without consular processing abroad, when an immigrant petition is approved and priority date is current.',
    steps: [
      'Confirm visa number availability on the Visa Bulletin for your category and country.',
      'File Form I-485 with required forms (I-693 medical, I-765 EAD, I-131 travel doc if desired).',
      'Attend biometrics appointment when scheduled.',
      'Respond to any RFE; prepare for employment-based interview if required.',
      'Receive approval and green card; verify I-551 validity dates.',
    ],
    timeline:
      'Concurrent filing with I-140 possible when visa is current. I-485 processing: months to over a year depending on field office.',
    tips: ['Maintain lawful status while I-485 pending if required.', 'Advance parole needed for international travel while I-485 pending.'],
    sources: [
      { title: 'USCIS — Adjustment of status', citation: 'I-485', url: I485, type: 'guidance' },
      { title: 'Form I-485', citation: 'I-485', url: 'https://www.uscis.gov/i-485', type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'concurrent-i140-i485',
    title: 'Concurrent I-140 and I-485 filing',
    category: 'employment-permanent',
    riskLevel: 'medium',
    description:
      'File immigrant petition and adjustment together when the priority date is current to obtain EAD and advance parole while waiting.',
    overview:
      'When a visa number is immediately available, beneficiaries in the U.S. may file Form I-485 together with or while I-140 is pending, enabling work and travel authorization during processing.',
    steps: [
      'Verify priority date is current on Visa Bulletin for your EB category and country.',
      'Prepare I-140 (or receipt if pending) and full I-485 package with supplements.',
      'Include I-765 for EAD and I-131 for advance parole in the concurrent package.',
      'File all forms with correct fees to the correct USCIS lockbox.',
      'Use EAD/AP cards when issued; maintain eligibility while case is pending.',
    ],
    timeline:
      'EAD/AP typically issued within months of filing. Green card approval timeline depends on USCIS workload and interview requirements.',
    tips: ['If I-140 is denied, I-485 may also be denied—assess case strength first.', 'AC21 portability may protect job changes after 180 days of pending I-485.'],
    sources: [
      { title: 'USCIS — Concurrent filing', citation: 'Concurrent', url: I485, type: 'guidance' },
      { title: 'Visa Bulletin', citation: 'DOS VB', url: 'https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin.html', type: 'guidance' },
    ],
  }),
]
