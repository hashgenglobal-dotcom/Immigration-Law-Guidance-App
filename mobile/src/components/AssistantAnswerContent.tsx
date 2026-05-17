import { StyleSheet, Text, View } from 'react-native'
import type { MockAnswer } from '@/lib/mockData'
import { LEGAL_DISCLAIMER_SHORT } from '@/lib/legalCopy'
import { CitationCard } from './CitationCard'
import { colors, fontFamily, radii, spacing, typography } from '@/theme'

export function AssistantAnswerContent({ answer }: { answer: MockAnswer }) {
  return (
    <View style={styles.wrap}>
      <Text style={styles.heading}>Summary</Text>
      <Text style={styles.lead}>{answer.shortAnswer}</Text>

      <Text style={styles.heading}>Explanation</Text>
      <Text style={styles.body}>{answer.simpleExplanation}</Text>

      {answer.possibleRisks.length > 0 ? (
        <>
          <Text style={styles.heading}>Possible risks</Text>
          {answer.possibleRisks.map((risk, i) => (
            <Text key={i} style={styles.bullet}>
              · {risk}
            </Text>
          ))}
        </>
      ) : null}

      {answer.whatToDoNext.length > 0 ? (
        <>
          <Text style={styles.heading}>What to do next</Text>
          {answer.whatToDoNext.map((step, i) => (
            <Text key={i} style={styles.bullet}>
              {i + 1}. {step}
            </Text>
          ))}
        </>
      ) : null}

      {answer.sources.length > 0 ? (
        <>
          <Text style={styles.heading}>Official sources</Text>
          {answer.sources.map((source, i) => (
            <CitationCard key={i} source={source} compact />
          ))}
        </>
      ) : null}

      <View style={styles.disclaimerBox}>
        <Text style={styles.disclaimer}>{LEGAL_DISCLAIMER_SHORT}</Text>
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: {
    gap: spacing.xs,
  },
  heading: {
    fontFamily: fontFamily.body,
    fontSize: typography.caption,
    fontWeight: '600',
    color: colors.brandBronze,
    textTransform: 'uppercase',
    letterSpacing: 0.4,
    marginTop: spacing.xs,
  },
  lead: {
    fontFamily: fontFamily.body,
    fontSize: typography.small,
    fontWeight: '600',
    lineHeight: 21,
    color: colors.brandNavy,
  },
  body: {
    fontFamily: fontFamily.body,
    fontSize: typography.small,
    lineHeight: 20,
    color: colors.brandNavy,
    opacity: 0.85,
  },
  bullet: {
    fontFamily: fontFamily.body,
    fontSize: typography.caption,
    lineHeight: 18,
    color: colors.brandNavy,
    opacity: 0.8,
    marginLeft: 2,
  },
  disclaimerBox: {
    marginTop: spacing.sm,
    padding: spacing.sm,
    borderRadius: radii.button,
    backgroundColor: colors.bronzeTint,
    borderLeftWidth: 3,
    borderLeftColor: colors.brandBronze,
  },
  disclaimer: {
    fontFamily: fontFamily.body,
    fontSize: typography.caption,
    lineHeight: 17,
    color: colors.brandNavy,
    opacity: 0.8,
  },
})
