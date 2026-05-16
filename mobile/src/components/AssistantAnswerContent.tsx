import { StyleSheet, Text, View } from 'react-native'
import type { MockAnswer } from '@/lib/mockData'
import { LEGAL_DISCLAIMER_SHORT } from '@/lib/legalCopy'
import { CitationCard } from './CitationCard'
import { colors, spacing, typography } from '@/theme'

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

      <Text style={styles.disclaimer}>{LEGAL_DISCLAIMER_SHORT}</Text>
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: {
    gap: spacing.xs,
  },
  heading: {
    fontSize: typography.caption,
    fontWeight: '700',
    color: colors.text,
    textTransform: 'uppercase',
    letterSpacing: 0.3,
    marginTop: spacing.xs,
  },
  lead: {
    fontSize: typography.small,
    fontWeight: '600',
    lineHeight: 20,
    color: colors.text,
  },
  body: {
    fontSize: typography.small,
    lineHeight: 19,
    color: colors.textSecondary,
  },
  bullet: {
    fontSize: typography.caption,
    lineHeight: 17,
    color: colors.textSecondary,
    marginLeft: 2,
  },
  disclaimer: {
    fontSize: typography.caption,
    lineHeight: 16,
    color: colors.textMuted,
    marginTop: spacing.sm,
    fontStyle: 'italic',
  },
})
