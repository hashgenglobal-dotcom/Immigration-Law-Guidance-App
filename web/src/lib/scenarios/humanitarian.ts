import { buildGuide } from './buildGuide'
import type { Scenario } from '../scenarioTypes'

const ASYLUM = 'https://www.uscis.gov/humanitarian/refugees-and-asylum/asylum'
const TPS = 'https://www.uscis.gov/humanitarian/temporary-protected-status'
const DACA = 'https://www.uscis.gov/DACA'
const VAWA = 'https://www.uscis.gov/humanitarian/battered-spouse-children-parents'

export const humanitarianGuides: Scenario[] = [
  buildGuide({
    id: 'affirmative-asylum',
    title: 'Affirmative asylum (I-589)',
    category: 'humanitarian',
    riskLevel: 'high',
    description:
      'Apply for protection in the U.S. if you fear persecution in your home country based on race, religion, nationality, political opinion, or particular social group.',
    overview:
      'Affirmative asylum is filed with USCIS while not in removal proceedings. You must apply within one year of last U.S. entry unless an exception applies, and demonstrate a well-founded fear of persecution.',
    steps: [
      'File Form I-589 with detailed personal statement and country conditions evidence.',
      'Apply within one year of arrival unless qualifying for an exception (changed circumstances, etc.).',
      'Attend biometrics and asylum interview with USCIS asylum office.',
      'Bring corroborating documents, witnesses (if any), and interpreter if needed.',
      'If granted, path to green card after one year; if denied, case may be referred to immigration court.',
    ],
    timeline:
      'One-year filing deadline from last entry (exceptions exist). Interview scheduling backlog varies by office—months to years.',
    tips: ['Persecution must be linked to a protected ground.', 'Consultation with experienced counsel is strongly recommended.'],
    sources: [
      { title: 'USCIS — Asylum', citation: 'Asylum', url: ASYLUM, type: 'guidance' },
      { title: 'Form I-589', citation: 'I-589', url: 'https://www.uscis.gov/i-589', type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'tps-registration-renewal',
    title: 'TPS registration and renewal',
    category: 'humanitarian',
    riskLevel: 'medium',
    description:
      'Temporary Protected Status for nationals of designated countries facing armed conflict, disaster, or extraordinary conditions.',
    overview:
      'TPS provides temporary work authorization and protection from removal for eligible nationals of countries designated by DHS. Registration and re-registration require filing during announced windows.',
    steps: [
      'Confirm your country is currently designated and registration/re-registration is open.',
      'Gather proof of nationality, continuous residence, and physical presence on required dates.',
      'File Form I-821 during the registration period; file Form I-765 for work authorization.',
      'Pay required fees or submit fee waiver if eligible.',
      'Re-register during each extension announcement to maintain status and EAD.',
    ],
    timeline:
      'Initial registration only during open periods. EAD validity tied to TPS designation extensions announced in Federal Register.',
    tips: ['TPS is temporary—not a path to green card by itself.', 'Late initial registration may be possible with good cause in limited cases.'],
    sources: [
      { title: 'USCIS — TPS', citation: 'TPS', url: TPS, type: 'guidance' },
      { title: 'Federal Register TPS notices', citation: 'FR', url: 'https://www.federalregister.gov/', type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'daca-renewal-overview',
    title: 'DACA renewal overview',
    category: 'humanitarian',
    riskLevel: 'medium',
    description:
      'Renew Deferred Action for Childhood Arrivals to maintain protection from removal and work authorization.',
    overview:
      'DACA provides deferred action and eligibility for EAD for certain individuals who came to the U.S. as children. USCIS accepts renewals for existing DACA recipients subject to current policy and court orders.',
    steps: [
      'Confirm DACA and advance parole policies are accepting renewals under current litigation/policy.',
      'File Form I-821D renewal with Form I-765 for work permit before expiration when possible.',
      'Include evidence of continuous residence since last approval.',
      'Use correct edition of forms and filing fees on USCIS website.',
      'Track receipt notice; EAD extension rules may apply while renewal pending.',
    ],
    timeline:
      'File renewal 120–150 days before expiration when possible. Processing times vary; check USCIS for auto-extension policies.',
    tips: ['Initial DACA applications may be closed depending on court rulings—verify current status.', 'Advance parole for DACA recipients depends on current policy.'],
    sources: [
      { title: 'USCIS — DACA', citation: 'DACA', url: DACA, type: 'guidance' },
      { title: 'Form I-821D', citation: 'I-821D', url: 'https://www.uscis.gov/i-821d', type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'u-visa-crime-victims',
    title: 'U visa for crime victims',
    category: 'humanitarian',
    riskLevel: 'high',
    description:
      'Immigration protection for victims of qualifying crimes who assist law enforcement in investigation or prosecution.',
    overview:
      'The U visa provides temporary status and a path to a green card for victims of certain crimes who suffered substantial harm and cooperated with certifying law enforcement or prosecutors.',
    steps: [
      'Identify whether the crime qualifies under INA U visa list (domestic violence, assault, trafficking, etc.).',
      'Obtain Form I-918 supplement B certification from a qualifying law enforcement agency.',
      'File Form I-918 with personal statement, evidence of harm, and cooperation documentation.',
      'Wait for visa cap allocation or bona fide determination for deferred action while pending.',
      'After three years in U status, may apply for lawful permanent residence if eligibility maintained.',
    ],
    timeline:
      'Annual cap of 10,000 principal U visas creates long backlogs. Bona fide pending cases may receive deferred action and EAD.',
    tips: ['Certification is often the hardest step—build relationship with investigating agency.', 'Derivative U visas available for qualifying family members.'],
    sources: [
      { title: 'USCIS — U visa', citation: 'U visa', url: 'https://www.uscis.gov/humanitarian/victims-of-criminal-activity-u-nonimmigrant-status', type: 'guidance' },
      { title: 'Form I-918', citation: 'I-918', url: 'https://www.uscis.gov/i-918', type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 't-visa-trafficking',
    title: 'T visa for trafficking survivors',
    category: 'humanitarian',
    riskLevel: 'high',
    description:
      'Protection for survivors of severe forms of trafficking who comply with reasonable law enforcement requests.',
    overview:
      'T nonimmigrant status helps trafficking survivors remain in the U.S. to assist in investigations and rebuild their lives. Eligibility requires victimization in a severe form of trafficking and compliance with law enforcement unless under 18 or traumatized.',
    steps: [
      'Document trafficking experience (labor or sex trafficking involving force, fraud, or coercion).',
      'Cooperate with reasonable law enforcement requests or qualify for an exception.',
      'Demonstrate extreme hardship if removed from the United States.',
      'File Form I-914 with supporting evidence and optional law enforcement declaration.',
      'After three years in T status (or upon investigation completion), may apply for green card.',
    ],
    timeline:
      'Adjudication varies. Cap exists but often not reached. Family derivatives may qualify for T or derivative status.',
    tips: ['Trauma-informed legal help is important.', 'Continued presence may be requested from ICE during investigation.'],
    sources: [
      { title: 'USCIS — T visa', citation: 'T visa', url: 'https://www.uscis.gov/humanitarian/victims-of-human-trafficking-and-other-crimes/t-nonimmigrant-status', type: 'guidance' },
      { title: 'Form I-914', citation: 'I-914', url: 'https://www.uscis.gov/i-914', type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'vawa-self-petition',
    title: 'VAWA self-petition (I-360)',
    category: 'humanitarian',
    riskLevel: 'high',
    description:
      'Self-petition for abused spouses, children, or parents of U.S. citizens or permanent residents without abuser’s knowledge.',
    overview:
      'The Violence Against Women Act allows certain abused family members to self-petition for immigration benefits confidentially, without the abuser’s involvement or consent.',
    steps: [
      'Document relationship to abuser (citizen or LPR spouse/parent) and shared residence.',
      'Gather evidence of battery or extreme cruelty (police reports, photos, affidavits, counseling records).',
      'Demonstrate good moral character during the statutory period.',
      'File Form I-360 with VAWA supplement and personal declaration.',
      'If approved and in U.S., may file I-485 when visa is available; immediate relatives may file concurrently.',
    ],
    timeline:
      'Prima facie determination may provide deferred action and EAD while pending. Full adjudication: months to over a year.',
    tips: ['Confidentiality protections apply—USCIS cannot contact abuser.', 'Male and female victims may qualify.'],
    sources: [
      { title: 'USCIS — VAWA', citation: 'VAWA', url: VAWA, type: 'guidance' },
      { title: 'Form I-360', citation: 'I-360', url: 'https://www.uscis.gov/i-360', type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'sijs-special-immigrant-juvenile',
    title: 'Special Immigrant Juvenile Status (SIJS)',
    category: 'humanitarian',
    riskLevel: 'high',
    description:
      'Immigration relief for children who cannot reunify with one or both parents due to abuse, neglect, or abandonment.',
    overview:
      'SIJS requires a state juvenile court order finding the child dependent on the court, that reunification with one or both parents is not viable due to abuse/neglect/abandonment, and return to home country is not in the child’s best interest.',
    steps: [
      'Obtain qualifying state juvenile court order with required SIJS findings.',
      'File Form I-360 (SIJS) with USCIS before aging out (subject to CSPA in some cases).',
      'After I-360 approval, wait for visa availability (EB-4 category) unless immediate adjustment eligible.',
      'File I-485 when priority date is current.',
      'Work with family court and immigration counsel throughout the process.',
    ],
    timeline:
      'State court process: months. Visa backlog for EB-4 SIJS can add years of wait after I-360 approval.',
    tips: ['Age limits apply—file in juvenile court before turning 18 in most states.', 'Cannot petition for parents through SIJS green card.'],
    sources: [
      { title: 'USCIS — SIJS', citation: 'SIJS', url: 'https://www.uscis.gov/special-immigrant-juvenile-status', type: 'guidance' },
      { title: 'Form I-360', citation: 'I-360', url: 'https://www.uscis.gov/i-360', type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'humanitarian-parole-overview',
    title: 'Humanitarian parole and temporary programs',
    category: 'humanitarian',
    riskLevel: 'high',
    description:
      'Overview of temporary U.S. entry for urgent humanitarian reasons or significant public benefit, including country-specific programs.',
    overview:
      'Humanitarian parole allows temporary entry into the U.S. for individuals who otherwise lack a visa. Programs vary by administration and may include sponsorship-based processes for specific nationalities.',
    steps: [
      'Identify whether a specific parole program applies to your nationality or situation.',
      'Gather identity documents, sponsor information (if required), and humanitarian justification.',
      'File Form I-131 for advance parole or follow program-specific online portal instructions.',
      'Understand parole is temporary—not a visa or green card path by itself.',
      'Plan next lawful status before parole expires or seek extension if available.',
    ],
    timeline:
      'Program-specific. General parole adjudication varies. Parole periods are typically limited (often 1–2 years with possible re-parole).',
    tips: ['Parole can be revoked.', 'Check current Federal Register and USCIS announcements—programs change frequently.'],
    sources: [
      { title: 'USCIS — Humanitarian parole', citation: 'Parole', url: 'https://www.uscis.gov/humanitarian/humanitarian-parole', type: 'guidance' },
      { title: 'CBP — Parole', citation: 'CBP', url: 'https://www.cbp.gov/travel/enforcement/parole', type: 'guidance' },
    ],
  }),
]
