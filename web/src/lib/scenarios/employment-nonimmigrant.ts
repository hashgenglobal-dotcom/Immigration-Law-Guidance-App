import { buildGuide } from './buildGuide'
import type { Scenario } from '../scenarioTypes'

const H1B = 'https://www.uscis.gov/working-in-the-united-states/h-1b-specialty-occupations'
const I129 = 'https://www.uscis.gov/i-129'
const L1 = 'https://www.uscis.gov/working-in-the-united-states/l-1b-intracompany-transferee'
const O1 = 'https://www.uscis.gov/working-in-the-united-states/o-1-visa-individuals-with-extraordinary-ability-or-achievement'
const TN = 'https://www.uscis.gov/working-in-the-united-states/tn-usmca-professionals'

export const employmentNonimmigrantGuides: Scenario[] = [
  buildGuide({
    id: 'h1b-cap-registration',
    title: 'H-1B cap registration and lottery',
    category: 'employment-nonimmigrant',
    riskLevel: 'medium',
    description:
      'How employers register for the annual H-1B cap, lottery selection, and next steps after selection.',
    overview:
      'Most private employers must register each beneficiary in the H-1B electronic registration system during the annual window. USCIS selects registrations by lottery before full petitions may be filed.',
    steps: [
      'Employer creates a USCIS online account and submits H-1B registrations during the registration period.',
      'Pay the registration fee for each beneficiary registered.',
      'If selected, employer files Form I-129 with supporting evidence within the filing window.',
      'Beneficiary maintains lawful status while petition is pending if already in the U.S.',
      'Upon approval, beneficiary may begin H-1B on the petition start date.',
    ],
    timeline:
      'Registration typically opens in March for an October 1 start date. Selected employers usually have about 90 days to file the full petition.',
    tips: ['Multiple employers can register the same beneficiary—only one petition should be filed if selected.', 'Cap-exempt employers do not use the lottery.'],
    sources: [
      { title: 'USCIS — H-1B cap', citation: 'H-1B cap', url: H1B, type: 'guidance' },
      { title: 'Form I-129', citation: 'I-129', url: I129, type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'h1b-consular-processing',
    title: 'H-1B consular processing guide',
    category: 'employment-nonimmigrant',
    riskLevel: 'medium',
    description:
      'Obtain an H-1B visa stamp abroad after petition approval when you are outside the U.S. or prefer consular processing.',
    overview:
      'Consular processing is used when the beneficiary is outside the United States or chooses to obtain a visa at a U.S. embassy or consulate rather than changing status inside the U.S.',
    steps: [
      'Employer obtains an approved Form I-129 with consular notification (if beneficiary is abroad).',
      'Beneficiary completes DS-160 visa application and pays the visa fee.',
      'Schedule a visa interview at the appropriate U.S. embassy or consulate.',
      'Bring approval notice, passport, job offer, and supporting documents to the interview.',
      'Enter the U.S. on H-1B visa and begin employment on the approved start date.',
    ],
    timeline:
      'After I-129 approval, consular appointment availability varies by post. Administrative processing can add weeks or months.',
    tips: ['221(g) administrative processing is common—plan travel accordingly.', 'Maintain valid passport for at least six months beyond intended stay.'],
    sources: [
      { title: 'USCIS — H-1B', citation: 'H-1B', url: H1B, type: 'guidance' },
      { title: 'Travel.state.gov — visa', citation: 'Visa', url: 'https://travel.state.gov/content/travel/en/us-visas.html', type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'h1b-change-of-status',
    title: 'H-1B change of status (in the U.S.)',
    category: 'employment-nonimmigrant',
    riskLevel: 'medium',
    description:
      'Switch from another nonimmigrant status to H-1B without leaving the United States using Form I-129.',
    overview:
      'If you are already in the U.S. in another status (F-1, J-1, L-1, etc.), your employer may request a change of status to H-1B on Form I-129 instead of consular processing.',
    steps: [
      'Employer files Form I-129 with change-of-status request and full H-1B evidence package.',
      'Beneficiary maintains current status until H-1B approval and effective date.',
      'If cap-subject, ensure registration was selected before filing.',
      'Respond to any USCIS Request for Evidence (RFE) within the deadline.',
      'Begin H-1B employment only after approval and on the start date listed.',
    ],
    timeline:
      'Standard processing varies; premium processing (if available) provides faster adjudication. H-1B typically starts October 1 for cap cases.',
    tips: ['International travel while COS is pending may abandon the request.', 'Cap-gap may extend F-1/OPT if applicable.'],
    sources: [
      { title: 'USCIS — Change of status', citation: 'COS', url: H1B, type: 'guidance' },
      { title: 'Form I-129', citation: 'I-129', url: I129, type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'h1b-amendment-transfer',
    title: 'H-1B amendment and employer transfer',
    category: 'employment-nonimmigrant',
    riskLevel: 'medium',
    description:
      'Change employers, job locations, or job duties while maintaining H-1B status through new petitions or amendments.',
    overview:
      'H-1B workers may change employers through a new I-129 petition (H-1B transfer). Material changes to job duties or work location may require an amended petition. Portability rules allow starting with a new employer in certain cases.',
    steps: [
      'New employer files Form I-129 requesting H-1B classification and extension if needed.',
      'Include evidence of specialty occupation, LCA, and beneficiary qualifications.',
      'Under AC21 portability, employment may begin upon USCIS receipt if prior H-1B was valid.',
      'File an amendment for material changes at the same employer (location, duties).',
      'Keep copies of all approval notices and I-94 records.',
    ],
    timeline:
      'Transfer petitions are often filed with premium processing. Employment with new employer can begin upon receipt if portability requirements are met.',
    tips: ['Gaps between employers can affect status—file before ending prior employment when possible.', 'Remote work may trigger new LCA posting requirements.'],
    sources: [
      { title: 'USCIS — H-1B portability', citation: 'AC21', url: H1B, type: 'guidance' },
      { title: 'Form I-129', citation: 'I-129', url: I129, type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'l1a-intracompany-manager',
    title: 'L-1A intracompany manager',
    category: 'employment-nonimmigrant',
    riskLevel: 'medium',
    description:
      'Transfer to the U.S. as a manager or executive after working for a related foreign entity for at least one year.',
    overview:
      'L-1A allows multinational companies to transfer managers or executives from a foreign office to a U.S. office. Initial stay is up to three years, extendable up to seven years total.',
    steps: [
      'Confirm one year of continuous employment abroad with qualifying organization within the last three years.',
      'U.S. entity files Form I-129 with evidence of qualifying relationship (parent, branch, subsidiary, affiliate).',
      'Document managerial or executive duties—not primarily doing the work of subordinates.',
      'Obtain L-1A approval and, if abroad, apply for L visa at consulate.',
      'Extensions filed before status expires; plan for eventual green card under EB-1C if eligible.',
    ],
    timeline:
      'Initial L-1A approval up to 3 years; extensions in 2-year increments; maximum 7 years in L-1A classification.',
    tips: ['Start-up L-1A has additional requirements for new U.S. offices.', 'Managerial capacity must be documented with org charts and job descriptions.'],
    sources: [
      { title: 'USCIS — L-1A', citation: 'L-1A', url: L1, type: 'guidance' },
      { title: 'Form I-129', citation: 'I-129', url: I129, type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'l1b-specialized-knowledge',
    title: 'L-1B specialized knowledge',
    category: 'employment-nonimmigrant',
    riskLevel: 'medium',
    description:
      'Transfer employees with specialized knowledge of company products, processes, or systems to a U.S. affiliate.',
    overview:
      'L-1B is for employees with specialized knowledge of the petitioning organization’s products, services, research, or proprietary techniques not commonly held in the industry.',
    steps: [
      'Document one year of employment abroad with qualifying organization.',
      'Prepare detailed evidence of specialized knowledge (training, patents, proprietary systems).',
      'File Form I-129 demonstrating qualifying relationship and specialized knowledge role.',
      'Distinguish specialized knowledge from general skills or common industry expertise.',
      'Plan extensions within the five-year L-1B maximum.',
    ],
    timeline:
      'Initial approval up to 3 years; maximum 5 years total in L-1B classification.',
    tips: ['USCIS scrutinizes L-1B specialized knowledge closely.', 'Blanket L petitions may be available for large multinational employers.'],
    sources: [
      { title: 'USCIS — L-1B', citation: 'L-1B', url: L1, type: 'guidance' },
      { title: 'Form I-129', citation: 'I-129', url: I129, type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'o1a-extraordinary-ability',
    title: 'O-1A extraordinary ability',
    category: 'employment-nonimmigrant',
    riskLevel: 'high',
    description:
      'Temporary visa for individuals with extraordinary ability in sciences, education, business, or athletics.',
    overview:
      'O-1A requires sustained national or international acclaim and a U.S. job or event in your field. Evidence must meet regulatory criteria or comparable proof of extraordinary ability.',
    steps: [
      'Identify a U.S. petitioner (employer, agent, or sponsor) for the O-1 petition.',
      'Gather evidence across criteria: awards, publications, judging, high salary, critical role, etc.',
      'Obtain advisory opinion from peer group or labor organization if required.',
      'File Form I-129 with O supplement and detailed evidence index.',
      'If approved abroad, apply for O visa at consulate; if in U.S., change of status may be requested.',
    ],
    timeline:
      'Initial period up to 3 years; extensions in 1-year increments for same event or activity. Premium processing available.',
    tips: ['Consultation letters are required for most O-1A cases.', 'Build evidence over time—strong cases show sustained acclaim.'],
    sources: [
      { title: 'USCIS — O-1', citation: 'O-1', url: O1, type: 'guidance' },
      { title: 'Form I-129 O supplement', citation: 'I-129 O', url: I129, type: 'guidance' },
    ],
  }),
  buildGuide({
    id: 'tn-usmca-professional',
    title: 'TN USMCA professional',
    category: 'employment-nonimmigrant',
    riskLevel: 'low',
    description:
      'Work in the U.S. as a Canadian or Mexican professional in an occupation listed under the USMCA (formerly NAFTA).',
    overview:
      'TN status is available to citizens of Canada and Mexico in specific professional occupations. Canadians may apply at the border; Mexicans apply at a consulate.',
    steps: [
      'Confirm your job title and duties match a USMCA profession list occupation.',
      'Obtain a detailed employer support letter describing duties, qualifications, and temporary nature.',
      'Prepare proof of citizenship and credentials (degree, licenses).',
      'Canadians: apply at a port of entry or pre-flight inspection; Mexicans: consular TN visa.',
      'TN is granted in up to 3-year increments and is renewable.',
    ],
    timeline:
      'Border applications for Canadians can be same-day. TN is temporary—must show intent to depart when status ends.',
    tips: ['TN is not dual intent like H-1B—green card planning requires care.', 'Self-employment is not permitted on TN.'],
    sources: [
      { title: 'USCIS — TN professionals', citation: 'TN', url: TN, type: 'guidance' },
      { title: 'CBP — TN information', citation: 'CBP', url: 'https://www.cbp.gov/travel/business-visas', type: 'guidance' },
    ],
  }),
]
