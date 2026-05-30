import type { OfficialSource, RiskLevel, Scenario, ScenarioCategoryId } from '../scenarioTypes'

type GuideInput = {
  id: string
  title: string
  category: ScenarioCategoryId
  riskLevel: RiskLevel
  description: string
  overview: string
  steps: string[]
  timeline: string
  tips?: string[]
  sources: OfficialSource[]
}

export function buildGuide(input: GuideInput): Scenario {
  const tipsBlock =
    input.tips && input.tips.length > 0
      ? `\n\n## Tips and cautions\n\n${input.tips.map((t) => `- ${t}`).join('\n')}\n`
      : ''

  const content = [
    '## Overview',
    '',
    input.overview,
    '',
    '## Step-by-step',
    '',
    ...input.steps.map((s, i) => `${i + 1}. ${s}`),
    '',
    '## Typical timeline',
    '',
    input.timeline,
    tipsBlock,
    '',
    '## Verify with official sources',
    '',
    'Use the linked government pages below for current forms, fees, and filing windows. Rules change frequently—always confirm before acting.',
  ]
    .join('\n')
    .trim()

  return {
    id: input.id,
    title: input.title,
    category: input.category,
    riskLevel: input.riskLevel,
    description: input.description,
    content,
    sources: input.sources,
  }
}
