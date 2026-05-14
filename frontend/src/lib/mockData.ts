export const mockScenarios = [
  {
    id: 'ice-door',
    title: 'ICE came to my door',
    riskLevel: 'high',
    description: 'Immigration officers are at your residence',
    shortDescription: 'Know your rights when ICE agents arrive',
  },
  {
    id: 'overstay',
    title: 'I overstayed my visa',
    riskLevel: 'medium',
    description: 'Your visa has expired and you are out of status',
    shortDescription: 'Understanding options after visa expiration',
  },
  {
    id: 'nta',
    title: 'I received a Notice to Appear',
    riskLevel: 'high',
    description: 'You have been placed in removal proceedings',
    shortDescription: 'What to do after receiving an NTA',
  },
  {
    id: 'asylum',
    title: 'I want to apply for asylum',
    riskLevel: 'medium',
    description: 'Seeking protection due to persecution in home country',
    shortDescription: 'Asylum application process and requirements',
  },
  {
    id: 'citizenship',
    title: 'I want to apply for citizenship',
    riskLevel: 'low',
    description: 'Naturalization process for permanent residents',
    shortDescription: 'N-400 application requirements',
  },
  {
    id: 'lost-document',
    title: 'I lost an immigration document',
    riskLevel: 'medium',
    description: 'Replacement procedures for lost documents',
    shortDescription: 'How to replace lost immigration documents',
  },
]

export const mockAnswer = {
  shortAnswer: 'This is a placeholder answer. Backend integration pending.',
  simpleExplanation: 'This section will contain a clear, plain-language explanation of the legal issue.',
  possibleRisks: [
    'Risk 1: Placeholder - backend will provide actual risks',
    'Risk 2: Placeholder - backend will provide actual risks',
  ],
  whatToDoNext: [
    'Step 1: Placeholder - backend will provide actionable steps',
    'Step 2: Placeholder - backend will provide actionable steps',
  ],
  sources: [
    {
      title: '8 CFR § 208.7 - Employment authorization',
      citation: '8 CFR 208.7',
      url: 'https://www.law.cornell.edu/cfr/text/8/208.7',
      type: 'regulation',
    },
  ],
  disclaimer: 'This is general legal information, not legal advice. Consult with an immigration attorney for your specific situation.',
}
