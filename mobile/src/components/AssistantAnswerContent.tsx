import { StyleSheet, Text, View } from 'react-native'
import type { MockAnswer } from '@/lib/mockData'
import type { ChatAssistantContent } from '@/types/chat'
import { CitationCard } from './CitationCard'
import { colors, fontFamily, radii, spacing, typography } from '@/theme'

function DisclaimerBlock({ text }: { text: string }) {
  return (
    <View style={styles.disclaimerBox}>
      <Text style={styles.disclaimer}>{text}</Text>
    </View>
  )
}

/** Structured mock answer (legacy scenarios / dev). */
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

      <DisclaimerBlock text={answer.disclaimer} />
    </View>
  )
}

/** Live backend answer from POST /api/chat. */
export function AssistantChatContent({ content }: { content: ChatAssistantContent }) {
  return (
    <View style={styles.wrap}>
      <View style={styles.privacyRow}>
        <Text style={styles.privacyBadge}>Privacy: {content.privacyMode}</Text>
        {content.activeDataset ? (
          <Text style={styles.dataset} numberOfLines={1}>
            Sources: {content.activeDataset}
          </Text>
        ) : null}
      </View>

      <Text style={styles.heading}>Information</Text>
      <Text style={styles.body}>{content.answer}</Text>

      {content.citations.length > 0 ? (
        <>
          <Text style={styles.heading}>Official sources</Text>
          {content.citations.map((citation, i) => (
            <CitationCard key={`${citation.citation}-${i}`} apiCitation={citation} compact />
          ))}
        </>
      ) : content.citationsMissing ? (
        <Text style={styles.citationsNote}>
          No official citations were returned for this answer. Verify details using primary
          government sources or a qualified immigration attorney.
        </Text>
      ) : null}

      <DisclaimerBlock
        text={
          content.disclaimer ||
          'General immigration information only — not legal advice. Consult a qualified immigration attorney for your situation.'
        }
      />
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: {
    gap: spacing.xs,
  },
  privacyRow: {
    gap: 2,
    marginBottom: spacing.xs,
  },
  privacyBadge: {
    fontFamily: fontFamily.body,
    fontSize: typography.caption,
    fontWeight: '600',
    color: colors.brandBronze,
    textTransform: 'uppercase',
    letterSpacing: 0.3,
  },
  dataset: {
    fontFamily: fontFamily.body,
    fontSize: typography.caption,
    color: colors.brandNavy,
    opacity: 0.65,
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
  citationsNote: {
    fontFamily: fontFamily.body,
    fontSize: typography.caption,
    lineHeight: 18,
    color: colors.brandNavy,
    opacity: 0.75,
    fontStyle: 'italic',
    marginTop: spacing.xs,
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
