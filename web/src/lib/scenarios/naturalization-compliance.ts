import { buildGuide } from './buildGuide'
import type { Scenario } from '../scenarioTypes'

const N400 = 'https://www.uscis.gov/citizenship/learn-about-citizenship/us-citizenship/naturalization'
const CIVICS = 'https://www.uscis.gov/citizenship/find-study-materials-and-resources/study-for-the-test'
const I131 = 'https://www.uscis.gov/i-131'

export const naturalizationGuides: Scenario[] = [
  buildGuide({
    id: 'n400-eligibility',
    title: 'N-400 naturalization eligibility',
    category: 'naturalization-compliance',
    riskLevel: 'low',
    description:
      'Check if you meet residency, physical presence, good moral character, and English/civics requirements for U.S. citizenship.',
    overview:
      'Most applicants need five years as a permanent resident (three if married to a U.S. citizen), physical presence and continuous residence, good moral character, and basic English and civics knowledge.',
    steps: [
      'Confirm you meet continuous residence and physical presence requirements for your category.',
      'Review any absences over six months that may break continuity.',
      'Assess good moral character for the statutory period (arrests, taxes, child support).',
      'Verify you are at least 18 and hold a valid green card.',
      'Check USCIS N-400 instructions for any category-specific rules (military, spouse, etc.).',
    ],
    timeline:
      'Earliest filing: 90 days before meeting continuous residence requirement. Five-year (or three-year) clock starts from LPR admission date with exceptions.',
    tips: ['Long absences can disrupt eligibility—track every trip abroad.', 'Some criminal history permanently bars naturalization.'],
    sources: [
      { title: 'USCIS — Naturalization', citation: 'N-400', url: N400, type: 'guidance' },
      { title: 'Form N-400', citation: 'N-400', url: 'https://www.uscis.gov/n-400', type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'n400-application-interview',
    title: 'N-400 application and interview prep',
    category: 'naturalization-compliance',
    riskLevel: 'low',
    description:
      'File Form N-400, attend biometrics, and prepare for the citizenship interview and oath ceremony.',
    overview:
      'Naturalization involves submitting Form N-400 with supporting documents, biometrics, an interview testing English and civics (unless exempt), and an oath ceremony where you take the Oath of Allegiance.',
    steps: [
      'Complete Form N-400 online or on paper with travel history and residence details for five years.',
      'Submit with copies of green card, photos (if paper), and fee per current USCIS fee schedule.',
      'Attend biometrics appointment when scheduled.',
      'Study English reading/writing and 100 civics questions for interview.',
      'Attend interview; if approved, schedule oath ceremony and receive Certificate of Naturalization.',
    ],
    timeline:
      'Processing times vary by field office—often 6–18 months from filing to oath. Check USCIS processing times tool.',
    tips: ['Bring all passports and complete travel history to interview.', 'Errors on N-400 can delay or deny—review carefully.'],
    sources: [
      { title: 'USCIS — Naturalization process', citation: 'Naturalization', url: N400, type: 'guidance' },
      { title: 'Form N-400', citation: 'N-400', url: 'https://www.uscis.gov/n-400', type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'civics-english-test-prep',
    title: 'English and civics test study guide',
    category: 'naturalization-compliance',
    riskLevel: 'low',
    description:
      'Prepare for the naturalization English reading/writing test and the 100 civics questions using official USCIS materials.',
    overview:
      'Most applicants must demonstrate ability to read, write, and speak basic English and pass a civics test on U.S. history and government. Age and disability exemptions may apply.',
    steps: [
      'Download USCIS civics questions and study the 2020/2008 version applicable to your test.',
      'Practice reading and writing sentences USCIS provides as samples.',
      'Use USCIS mobile app and official study materials—avoid outdated third-party lists.',
      'Determine if you qualify for 65/20 exemption (older LPR) or medical disability waiver (N-648).',
      'At interview, answer up to 10 civics questions; need 6 correct to pass.',
    ],
    timeline:
      'Study over weeks or months before interview. Exemptions based on age/years as LPR or approved N-648 waive parts of the test.',
    tips: ['Speaking ability is judged throughout the interview, not a separate test.', 'Some applicants qualify for native-language civics test with interpreter.'],
    sources: [
      { title: 'USCIS — Study for the test', citation: 'Civics', url: CIVICS, type: 'guidance' },
      { title: 'USCIS — Test exemptions', citation: 'Exemptions', url: N400, type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'reentry-permit-i131',
    title: 'Re-entry permit (I-131)',
    category: 'naturalization-compliance',
    riskLevel: 'medium',
    description:
      'Preserve permanent resident status during long trips abroad by obtaining a re-entry permit before leaving.',
    overview:
      'Lawful permanent residents planning absences of one year or more (or who risk abandonment with shorter trips) should apply for a re-entry permit on Form I-131 before departing the United States.',
    steps: [
      'File Form I-131 with biometrics fee before leaving the U.S.',
      'Complete biometrics in the U.S.—do not depart before biometrics unless emergency with counsel advice.',
      'Receive re-entry permit (valid up to two years, not extendable from abroad).',
      'Use permit to re-enter after long absences; CBP makes final admissibility decision.',
      'For naturalization, long absences may still break continuous residence even with permit.',
    ],
    timeline:
      'Apply several months before planned departure. Permit valid up to 2 years from issuance for LPRs.',
    tips: ['Re-entry permit does not guarantee admission.', 'Absences over six months can break N-400 continuous residence.'],
    sources: [
      { title: 'Form I-131', citation: 'I-131', url: I131, type: 'guidance' },
      { title: 'USCIS — Travel documents', citation: 'Travel', url: 'https://www.uscis.gov/green-card/green-card-processes-and-procedures/travel-documents', type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'certificate-of-citizenship-n600',
    title: 'Certificate of Citizenship (N-600)',
    category: 'naturalization-compliance',
    riskLevel: 'low',
    description:
      'Document U.S. citizenship if you automatically acquired citizenship through parents after birth but lack proof.',
    overview:
      'Form N-600 is for people who claim U.S. citizenship through birth abroad to U.S. citizen parents or automatic acquisition after birth under INA 320/322, and need an official certificate.',
    steps: [
      'Determine if you acquired citizenship at birth (INA 301) or after birth through resident parent (INA 320).',
      'Gather parent’s citizenship evidence, birth certificates, and proof of physical presence/residence.',
      'File Form N-600 with USCIS or apply for U.S. passport at Department of State.',
      'Attend interview if required with original civil documents.',
      'Receive Certificate of Citizenship as proof for passport and employment eligibility.',
    ],
    timeline:
      'N-600 processing: months. Passport application through State Department may be faster for travel needs.',
    tips: ['Complex acquisition rules changed over time—verify law in effect on your birth date.', 'Adopted children have separate requirements.'],
    sources: [
      { title: 'Form N-600', citation: 'N-600', url: 'https://www.uscis.gov/n-600', type: 'guidance' },
      { title: 'USCIS — Citizenship through parents', citation: 'Derivation', url: N400, type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'dual-citizenship-info',
    title: 'Dual citizenship considerations',
    category: 'naturalization-compliance',
    riskLevel: 'low',
    description:
      'Informational overview of how U.S. naturalization interacts with citizenship of another country—not legal advice on foreign law.',
    overview:
      'The U.S. does not generally require renouncing other nationalities when naturalizing, but your home country’s laws may treat you differently. Military service, taxes, and travel document rules vary by country.',
    steps: [
      'Review your country of origin’s nationality laws regarding dual citizenship.',
      'Understand U.S. Oath of Allegiance requirements and U.S. passport use when entering the U.S.',
      'Use the correct passport for each country’s entry requirements when traveling.',
      'Consult foreign consulate for renunciation requirements if any (some countries require notification).',
      'Keep informed about tax reporting obligations (e.g., U.S. taxes for all citizens regardless of residence).',
    ],
    timeline:
      'Dual status begins upon naturalization oath unless you take steps to renounce other citizenship under foreign law.',
    tips: ['This guide is informational—foreign law varies widely.', 'Some countries revoke citizenship upon naturalizing elsewhere.'],
    sources: [
      { title: 'USCIS — Naturalization', citation: 'Naturalization', url: N400, type: 'guidance' },
      { title: 'Travel.state.gov — dual nationality', citation: 'DOS', url: 'https://travel.state.gov/content/travel/en/legal/travel-legal-considerations/us-citizenship-laws.html', type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'selective-service-registration',
    title: 'Selective Service registration',
    category: 'naturalization-compliance',
    riskLevel: 'low',
    description:
      'Males ages 18–26 generally must register for Selective Service—affecting federal benefits and naturalization good moral character.',
    overview:
      'Most males living in the U.S. ages 18 through 25 must register with Selective Service. Failure to register can affect eligibility for federal student aid, federal employment, and may impact naturalization good moral character.',
    steps: [
      'Register online at sss.gov within 30 days of turning 18 (or within 30 days of entering status in U.S.).',
      'Keep registration acknowledgment for N-400 and benefit applications.',
      'If you did not register and are still under 26, register immediately.',
      'If over 26 and never registered, gather evidence of why registration was not required or status letter from Selective Service.',
      'Include registration proof or status letter with N-400 if applicable.',
    ],
    timeline:
      'Register between ages 18 and 26. Status information letters from Selective Service take several weeks to obtain.',
    tips: ['Non-citizens must register if they are in U.S. as immigrants or certain statuses.', 'Transgender individuals follow Selective Service policy in effect at time of registration.'],
    sources: [
      { title: 'Selective Service System', citation: 'SSS', url: 'https://www.sss.gov/', type: 'guidance' },
      { title: 'USCIS — Good moral character', citation: 'GMC', url: N400, type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'travel-while-n400-pending',
    title: 'Travel while N-400 is pending',
    category: 'naturalization-compliance',
    riskLevel: 'medium',
    description:
      'Understand how international travel affects pending naturalization and when to notify USCIS of absences.',
    overview:
      'You may travel while N-400 is pending using your green card, but absences can affect continuous residence and physical presence requirements. Trips six months or longer raise abandonment and eligibility concerns.',
    steps: [
      'List all trips on N-400 and update USCIS if you travel after filing.',
      'Avoid absences of six months or more unless you obtain re-entry permit and understand N-400 impact.',
      'Absences over one year generally break continuous residence for N-400 (with narrow exceptions).',
      'Carry green card for re-entry; naturalization applicants do not receive advance parole.',
      'If travel is necessary, consult eligibility impact before departing—especially close to interview.',
    ],
    timeline:
      'Continuous residence must generally be maintained through oath. Break may require restarting waiting period.',
    tips: ['Missing scheduled interview due to travel can result in denial.', 'Military and certain spouse exceptions modify absence rules.'],
    sources: [
      { title: 'USCIS — Continuous residence', citation: 'Residence', url: N400, type: 'guidance' },
      { title: 'Form N-400 instructions', citation: 'N-400', url: 'https://www.uscis.gov/n-400', type: 'guidance' },
    ],
  }),
]
