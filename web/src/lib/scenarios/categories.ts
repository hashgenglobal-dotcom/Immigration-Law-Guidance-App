import type { ScenarioCategoryId } from '../scenarioTypes'

export interface ScenarioCategory {
  id: ScenarioCategoryId
  label: string
  shortLabel: string
  description: string
}

export const SCENARIO_CATEGORIES: ScenarioCategory[] = [
  {
    id: 'f1-j1',
    label: 'F-1 & J-1 Student/Scholar Ecosystem',
    shortLabel: 'F-1 & J-1',
    description: 'Student status, OPT, STEM, CPT, cap-gap, and J-1 scholar pathways.',
  },
  {
    id: 'employment-nonimmigrant',
    label: 'Employment-Based Nonimmigrant Visas',
    shortLabel: 'Work Visas',
    description: 'H-1B, L-1, O-1, TN, and related temporary work authorization.',
  },
  {
    id: 'employment-permanent',
    label: 'Employer-Sponsored Permanent Residency',
    shortLabel: 'Green Card (Work)',
    description: 'PERM, EB categories, I-140, and adjustment of status through employment.',
  },
  {
    id: 'family-based',
    label: 'Family-Based Immigration & Relationships',
    shortLabel: 'Family',
    description: 'Marriage, fiancé, parent, child, and sibling petitions.',
  },
  {
    id: 'humanitarian',
    label: 'Humanitarian & Protection',
    shortLabel: 'Humanitarian',
    description: 'Asylum, TPS, DACA, U/T visas, VAWA, and related protections.',
  },
  {
    id: 'naturalization-compliance',
    label: 'Naturalization & Compliance',
    shortLabel: 'Citizenship',
    description: 'N-400 naturalization, travel documents, and compliance basics.',
  },
]

export const CATEGORY_BY_ID = Object.fromEntries(
  SCENARIO_CATEGORIES.map((c) => [c.id, c]),
) as Record<ScenarioCategoryId, ScenarioCategory>
