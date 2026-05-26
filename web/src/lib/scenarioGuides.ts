import type { Scenario } from './scenarioTypes'

/** Twelve high-impact scenario guides (official-source oriented; not legal advice). */
export const scenarioGuides: Scenario[] = [
  {
    id: 'f1-status-basics',
    title: 'F-1 status basics',
    riskLevel: 'low',
    shortDescription:
      'Enrollment, on-campus work limits, grace period, and keeping lawful F-1 status',
    overview:
      'F-1 status is tied to a SEVP-certified school and full-time study. Work, travel, and program changes must follow SEVP and USCIS rules. Falling out of status can affect OPT, H-1B, and future benefits.',
    keyPoints: [
      'Maintain full-time enrollment and follow your I-20 program dates unless your DSO authorizes a reduced course load.',
      'On-campus work is generally limited to 20 hours per week while school is in session unless your DSO says otherwise.',
      'Off-campus work usually requires CPT, OPT, or other authorization—do not work off-campus without approval.',
      'After completing your program, you may have a 60-day grace period to depart, change status, or start approved OPT—confirm dates with your DSO.',
      'Report address changes and employment updates to your DSO within required timeframes (SEVIS).',
      'If you need to drop below full time, transfer schools, or extend your program, get a new I-20 from your DSO before your status lapses.',
    ],
    sources: [
      {
        title: 'USCIS — Students and Exchange Visitors',
        citation: 'USCIS F-1',
        url: 'https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors',
        type: 'guidance',
      },
      {
        title: 'Study in the States (SEVP)',
        citation: 'SEVP',
        url: 'https://studyinthestates.dhs.gov/',
        type: 'guidance',
      },
    ],
  },
  {
    id: 'post-completion-opt',
    title: 'Post-completion OPT (Form I-765)',
    riskLevel: 'medium',
    shortDescription:
      'DSO recommendation, filing I-765, EAD card, and when you may start working',
    overview:
      'Post-completion OPT lets eligible F-1 students work in a job related to their major after finishing their program. You need a DSO recommendation in SEVIS, then USCIS must approve Form I-765 before employment begins.',
    keyPoints: [
      'Ask your DSO to recommend post-completion OPT and issue an updated I-20 with the OPT recommendation.',
      'File Form I-765 with USCIS after the DSO enters the OPT request in SEVIS—use the edition and fee on the official form page.',
      'Apply within the filing window USCIS sets for your situation (often up to 90 days before and within 60 days after your program end date—confirm on current USCIS OPT instructions).',
      'Select the correct eligibility category on I-765 for post-completion OPT (see form instructions for the current code).',
      'You may not begin OPT employment until USCIS approves I-765 and you receive your EAD, unless USCIS rules allow a different start rule for your case.',
      'Unemployment during OPT is limited—track days and report employment changes to your DSO.',
      'If you later pursue H-1B, understand cap-gap rules if your OPT may expire before Oct. 1.',
    ],
    sources: [
      {
        title: 'USCIS — OPT for F-1 Students',
        citation: 'USCIS OPT',
        url: 'https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-opt-for-f-1-students',
        type: 'guidance',
      },
      {
        title: 'Form I-765',
        citation: 'Form I-765',
        url: 'https://www.uscis.gov/i-765',
        type: 'guidance',
      },
    ],
  },
  {
    id: 'stem-opt-extension',
    title: 'STEM OPT extension (I-983 + I-765)',
    riskLevel: 'medium',
    shortDescription:
      '24-month STEM extension, training plan, E-Verify employer, and filing deadlines',
    overview:
      'If you have a qualifying STEM degree from an accredited SEVP school, you may request a 24-month extension of post-completion OPT. Your employer must participate in E-Verify and complete Form I-983 with you before you file I-765.',
    keyPoints: [
      'Confirm your degree is on the STEM Designated Degree Program List and that you are within the STEM OPT filing period.',
      'Verify your employer is enrolled in E-Verify and will cooperate on Form I-983 (training plan).',
      'Complete and sign Form I-983 with your employer; keep copies and update it when material changes occur.',
      'Request an updated STEM OPT I-20 from your DSO (signed within the period USCIS requires before filing).',
      'File Form I-765 for the STEM extension before your current OPT EAD expires—timely filing may trigger a 180-day automatic extension while pending.',
      'Attend any biometrics appointment USCIS schedules (photo requirements for I-765 have changed—follow your notice).',
      'Report employment changes to your DSO within required deadlines; unemployment limits still apply during STEM OPT.',
    ],
    sources: [
      {
        title: 'USCIS — STEM OPT',
        citation: 'USCIS STEM OPT',
        url: 'https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-extension-for-stem-students-stem-opt',
        type: 'guidance',
      },
      {
        title: 'Form I-983',
        citation: 'Form I-983',
        url: 'https://www.uscis.gov/i-983',
        type: 'guidance',
      },
    ],
  },
  {
    id: 'h1b-cap-gap',
    title: 'Cap-gap after H-1B filing',
    riskLevel: 'medium',
    shortDescription:
      'Extending F-1/OPT work authorization while a cap-subject H-1B is pending',
    overview:
      'If your employer timely files a cap-subject H-1B petition for you and your F-1 or OPT would end before Oct. 1, you may qualify for an automatic cap-gap extension of status and work authorization until Sept. 30 in many cases.',
    keyPoints: [
      'Cap-gap applies only when a cap-subject H-1B petition is properly filed for you before your F-1/OPT end date—employer action is required.',
      'The extension is automatic in eligible cases; your proof is often an updated I-20 from your DSO showing the extension—not a new EAD.',
      'If the H-1B petition is denied, withdrawn, or revoked, cap-gap ends and grace-period rules may apply—act quickly with your DSO.',
      'You may be able to apply for STEM OPT during cap-gap in some situations; timing rules are strict—confirm with your DSO.',
      'If you change your mind about H-1B, follow USCIS guidance on withdrawal timing to avoid status gaps.',
      'Plan travel carefully—departing the U.S. during cap-gap can affect whether you can return under F-1 without a valid visa.',
    ],
    sources: [
      {
        title: 'USCIS — Cap-gap extension',
        citation: 'USCIS cap-gap',
        url: 'https://www.uscis.gov/working-in-the-united-states/temporary-workers/h-1b-specialty-occupations/extension-of-post-completion-optional-practical-training-opt-and-f-1-status-for-eligible-students',
        type: 'guidance',
      },
    ],
  },
  {
    id: 'f1-to-h1b-timeline',
    title: 'F-1 to H-1B timeline',
    riskLevel: 'medium',
    shortDescription:
      'Registration, selection, petition, and change of status from student to H-1B worker',
    overview:
      'Most new H-1B workers go through an annual cap registration, possible selection, then an employer-filed H-1B petition. Students often move from OPT through cap-gap to H-1B effective Oct. 1 if approved.',
    keyPoints: [
      'Your employer (not you) registers you in the H-1B electronic registration during the annual window if you need a cap number.',
      'If selected, the employer may file Form I-129 for a cap-subject H-1B with supporting labor condition and specialty occupation evidence.',
      'Beneficiaries already in the U.S. may request a change of status to H-1B instead of consular processing—follow attorney/employer strategy.',
      'If you are on OPT, coordinate filing dates with cap-gap so work authorization does not lapse before Oct. 1.',
      'H-1B approval is employer-specific—changing employers later requires a new petition or portability rules.',
      'Keep copies of all I-797 notices, registration selection, and I-129 receipts.',
    ],
    sources: [
      {
        title: 'USCIS — H-1B electronic registration',
        citation: 'USCIS H-1B registration',
        url: 'https://www.uscis.gov/working-in-the-united-states/temporary-workers/h-1b-specialty-occupations/h-1b-electronic-registration-process',
        type: 'guidance',
      },
      {
        title: 'USCIS — H-1B specialty occupations',
        citation: 'USCIS H-1B',
        url: 'https://www.uscis.gov/working-in-the-united-states/temporary-workers/h-1b-specialty-occupations',
        type: 'guidance',
      },
    ],
  },
  {
    id: 'h4-ead',
    title: 'H-4 employment authorization',
    riskLevel: 'low',
    shortDescription:
      'When H-4 spouses may file Form I-765 and evidence of eligibility',
    overview:
      'Certain H-4 spouses of H-1B workers may apply for employment authorization if the H-1B principal has an approved I-140 or meets AC21 extensions beyond six years. Work is only allowed after USCIS approves the EAD.',
    keyPoints: [
      'Confirm you qualify under current rules (approved I-140 or qualifying AC21 status for the H-1B spouse).',
      'Gather proof of relationship, the H-1B spouse’s status, and the qualifying immigrant petition or extension evidence listed in I-765 instructions.',
      'File Form I-765 with the correct category code for H-4 spouses (see current form instructions).',
      'Do not work until you receive the EAD card with valid dates.',
      'Renew before expiration; check whether automatic extension rules apply to your category and if you have the right I-797 combo.',
      'Travel outside the U.S. may require a valid H-4 visa stamp for reentry—EAD alone is not a travel document.',
    ],
    sources: [
      {
        title: 'USCIS — H-4 EAD',
        citation: 'USCIS H-4',
        url: 'https://www.uscis.gov/working-in-the-united-states/temporary-workers/h-1b-specialty-occupations/h-1b-qualifying-spouses-and-children',
        type: 'guidance',
      },
      {
        title: 'Form I-765',
        citation: 'Form I-765',
        url: 'https://www.uscis.gov/i-765',
        type: 'guidance',
      },
    ],
  },
  {
    id: 'ead-renewal-biometrics',
    title: 'EAD renewal and biometrics',
    riskLevel: 'medium',
    shortDescription:
      'Renewing work authorization, automatic extensions, and photo/biometrics rules',
    overview:
      'Many categories require filing a new Form I-765 before your EAD expires. USCIS processing times vary; some categories allow continued work with an automatic extension if you file on time and meet the criteria in the Federal Register and form instructions.',
    keyPoints: [
      'Check your EAD expiration date and file a renewal early—USCIS recommends applying before expiry per form instructions.',
      'Use the I-765 edition and fee shown on the official USCIS page the day you file.',
      'If automatic extension applies to your category, keep your expired EAD, Form I-797 receipt, and proof of same-category renewal filing for employers.',
      'Watch for biometrics appointment notices—USCIS may require photos taken at an Application Support Center for I-765 (policies have changed; follow your notice).',
      'Respond promptly to any Request for Evidence (RFE)—missing deadlines can end work authorization.',
      'Update your address with USCIS within 10 days of moving (Form AR-11) so notices reach you.',
    ],
    sources: [
      {
        title: 'USCIS — Form I-765',
        citation: 'Form I-765',
        url: 'https://www.uscis.gov/i-765',
        type: 'guidance',
      },
      {
        title: 'USCIS — Address change',
        citation: 'AR-11',
        url: 'https://www.uscis.gov/addresschange',
        type: 'guidance',
      },
    ],
  },
  {
    id: 'h1b-cap-registration',
    title: 'H-1B cap registration (beneficiary guide)',
    riskLevel: 'medium',
    shortDescription:
      'What workers should know about the annual lottery and employer registration',
    overview:
      'Each fiscal year, employers register prospective H-1B workers in USCIS’s online system and pay a registration fee per beneficiary. Only selected registrations may lead to a cap-subject I-129 petition. Beneficiaries do not file the registration themselves.',
    keyPoints: [
      'Only a U.S. employer (or authorized representative) may submit your registration—you provide information the employer requests.',
      'One registration per beneficiary per year is allowed; duplicate registrations can disqualify you.',
      'Selection does not equal approval—it only allows the employer to file a cap-subject H-1B petition within the filing window stated on the notice.',
      'If not selected, the employer cannot file a new cap petition until a future registration period unless an exemption applies (e.g., cap-exempt employer).',
      'Keep your passport, degree evaluations, and employment history ready in case you are selected and the employer files quickly.',
      'Check USCIS each year for registration dates, fees, and any rule changes (e.g., wage-weighted selection).',
    ],
    sources: [
      {
        title: 'USCIS — H-1B registration process',
        citation: 'USCIS registration',
        url: 'https://www.uscis.gov/working-in-the-united-states/temporary-workers/h-1b-specialty-occupations/h-1b-electronic-registration-process',
        type: 'guidance',
      },
    ],
  },
  {
    id: 'h1b-after-selection',
    title: 'H-1B after selection and start date',
    riskLevel: 'medium',
    shortDescription:
      'From selected registration to I-129 approval, Oct. 1 start, and portability',
    overview:
      'After registration selection, your employer files Form I-129 for H-1B status. If approved, you may start H-1B employment on the effective date in the approval (often Oct. 1 for cap cases). Changing employers later has separate rules.',
    keyPoints: [
      'Employer files Form I-129 with Labor Condition Application (LCA) and specialty occupation evidence within the deadline on the selection notice.',
      'If you are in the U.S., the petition may request change of status; if abroad, you may need consular visa processing.',
      'Do not start H-1B work until the petition is approved and the start date on your I-797 has begun.',
      'If you were on OPT, coordinate cap-gap documentation with your DSO while the petition is pending.',
      'H-1B portability may allow starting with a new employer after a timely filed extension or transfer petition—confirm with an attorney before switching jobs.',
      'Keep all pay stubs, I-797 approvals, and I-94 records for future green card or extension filings.',
    ],
    sources: [
      {
        title: 'USCIS — Form I-129',
        citation: 'Form I-129',
        url: 'https://www.uscis.gov/i-129',
        type: 'guidance',
      },
      {
        title: 'USCIS — H-1B specialty occupations',
        citation: 'USCIS H-1B',
        url: 'https://www.uscis.gov/working-in-the-united-states/temporary-workers/h-1b-specialty-occupations',
        type: 'guidance',
      },
    ],
  },
  {
    id: 'family-gc-i130-overview',
    title: 'Family-based green card overview',
    riskLevel: 'medium',
    shortDescription:
      'I-130 petition, visa availability, and choosing adjustment vs consular processing',
    overview:
      'Most family-based permanent residence starts with Form I-130 filed by a qualifying relative. After approval, many beneficiaries wait for a visa number (priority date) before applying for a green card through adjustment of status in the U.S. or immigrant visa abroad.',
    keyPoints: [
      'Identify the correct family relationship category (immediate relative vs preference categories) and who may file I-130.',
      'File Form I-130 with proof of relationship and status of the petitioner; USCIS issues a receipt and later a decision.',
      'Check the Visa Bulletin monthly for priority dates if you are not an immediate relative.',
      'If a visa is available and you are in the U.S., you may file Form I-485 (adjustment) when eligible; others consular process.',
      'Maintain lawful status while waiting—overstay or unauthorized work can trigger inadmissibility issues.',
      'Some cases need Form I-601 waivers for inadmissibility—high complexity; get legal advice.',
    ],
    sources: [
      {
        title: 'USCIS — Family of U.S. citizens',
        citation: 'USCIS family',
        url: 'https://www.uscis.gov/family',
        type: 'guidance',
      },
      {
        title: 'Form I-130',
        citation: 'Form I-130',
        url: 'https://www.uscis.gov/i-130',
        type: 'guidance',
      },
      {
        title: 'Visa Bulletin',
        citation: 'Visa Bulletin',
        url: 'https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin.html',
        type: 'guidance',
      },
    ],
  },
  {
    id: 'i485-adjustment',
    title: 'Adjustment of status (Form I-485)',
    riskLevel: 'medium',
    shortDescription:
      'Applying for a green card inside the U.S., work/travel documents, and interviews',
    overview:
      'Adjustment of status lets eligible applicants apply for lawful permanent residence without leaving the United States. You typically file Form I-485 with supporting forms for work (I-765) and travel (I-131) when rules allow.',
    keyPoints: [
      'Confirm you have an approved immigrant petition (or concurrent filing eligibility) and a visa number if required.',
      'File Form I-485 with civil documents, medical exam (I-693), and fees per the USCIS filing guide for your category.',
      'You may file Form I-765 and Form I-131 with or after I-485—follow current instructions for combo cards.',
      'Attend biometrics and the green card interview if scheduled; bring originals of documents submitted.',
      'Do not travel outside the U.S. without advance parole if you do not have other valid travel authorization.',
      'Report address changes to USCIS while your case is pending.',
    ],
    sources: [
      {
        title: 'USCIS — Adjustment of status',
        citation: 'USCIS AOS',
        url: 'https://www.uscis.gov/green-card/green-card-processes-and-procedures/adjustment-of-status',
        type: 'guidance',
      },
      {
        title: 'Form I-485',
        citation: 'Form I-485',
        url: 'https://www.uscis.gov/i-485',
        type: 'guidance',
      },
    ],
  },
  {
    id: 'advance-parole-aos',
    title: 'Advance parole while I-485 is pending',
    riskLevel: 'medium',
    shortDescription:
      'Travel outside the U.S. without abandoning a pending adjustment application',
    overview:
      'If you leave the United States while Form I-485 is pending without advance parole (or another valid travel document), USCIS may treat your application as abandoned. Advance parole is requested on Form I-131 and must be approved before travel unless an exception applies.',
    keyPoints: [
      'File Form I-131 for advance parole before international travel unless you hold a valid H/L/K status with clear travel rules—get advice for dual-intent statuses.',
      'Wait for the I-131 approval notice and carry it with your passport when you return; a pending I-131 alone is not enough.',
      'Long absences can affect continuous residence for naturalization later—even with advance parole.',
      'If you have accrued unlawful presence or prior removal orders, travel can trigger bars—consult an attorney before departing.',
      'Emergency travel may be possible through humanitarian parole in rare cases—separate from standard advance parole.',
      'Keep copies of your I-485 receipt, I-131 approval, and entry stamp when you return.',
    ],
    sources: [
      {
        title: 'USCIS — Form I-131',
        citation: 'Form I-131',
        url: 'https://www.uscis.gov/i-131',
        type: 'guidance',
      },
      {
        title: 'USCIS — Travel documents',
        citation: 'USCIS travel',
        url: 'https://www.uscis.gov/forms/explore-my-options/travel-documents',
        type: 'guidance',
      },
    ],
  },
]
