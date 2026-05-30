import type { Scenario } from '../scenarioTypes'
import { employmentNonimmigrantGuides } from './employment-nonimmigrant'
import { employmentPermanentGuides } from './employment-permanent'
import { f1J1Guides } from './f1-j1'
import { familyBasedGuides } from './family-based'
import { humanitarianGuides } from './humanitarian'
import { naturalizationGuides } from './naturalization-compliance'

export const scenarioGuides: Scenario[] = [
  ...f1J1Guides,
  ...employmentNonimmigrantGuides,
  ...employmentPermanentGuides,
  ...familyBasedGuides,
  ...humanitarianGuides,
  ...naturalizationGuides,
]

export { SCENARIO_CATEGORIES, CATEGORY_BY_ID } from './categories'
