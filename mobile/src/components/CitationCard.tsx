import { Linking, Pressable, StyleSheet, Text, View } from 'react-native'
import type { OfficialSource } from '@/lib/mockData'
import type { ChatCitation } from '@/types/chat'
import { colors, spacing, typography } from '@/theme'

const typeLabels: Record<OfficialSource['type'], string> = {
  regulation: 'Regulation',
  statute: 'Statute',
  case: 'Case law',
  guidance: 'Guidance',
}

function apiCitationTitle(citation: ChatCitation): string {
  if (citation.topic?.trim()) {
    return citation.subtopic?.trim()
      ? `${citation.topic} — ${citation.subtopic}`
      : citation.topic
  }
  return citation.citation
}

function apiCitationMeta(citation: ChatCitation): string {
  const parts = [citation.citation]
  if (citation.risk_level) parts.push(citation.risk_level)
  return parts.join(' · ')
}

export function CitationCard({
  source,
  apiCitation,
  compact,
}: {
  /** Mock / scenario sources */
  source?: OfficialSource
  /** Live chat API citation */
  apiCitation?: ChatCitation
  compact?: boolean
}) {
  const title = source ? source.title : apiCitation ? apiCitationTitle(apiCitation) : ''
  const meta = source
    ? `${typeLabels[source.type]} · ${source.citation}`
    : apiCitation
      ? apiCitationMeta(apiCitation)
      : ''
  const url = source?.url ?? apiCitation?.official_url ?? null

  return (
    <View style={[styles.card, compact && styles.cardCompact]}>
      <Text style={[styles.title, compact && styles.titleCompact]} numberOfLines={2}>
        {title}
      </Text>
      <Text style={styles.meta} numberOfLines={1}>
        {meta}
      </Text>
      {url ? (
        <Pressable
          onPress={() => Linking.openURL(url)}
          style={({ pressed }) => [styles.link, pressed && styles.linkPressed]}
          accessibilityRole="link"
        >
          <Text style={styles.linkText}>View source</Text>
        </Pressable>
      ) : (
        <Text style={styles.noLink}>Official link not available</Text>
      )}
    </View>
  )
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.creamMuted,
    borderColor: colors.border,
    borderWidth: 1,
    borderLeftWidth: 3,
    borderLeftColor: colors.bronze,
    borderRadius: 8,
    padding: spacing.sm + 2,
    marginBottom: spacing.sm,
  },
  cardCompact: {
    padding: spacing.sm,
    marginBottom: spacing.xs,
  },
  title: {
    fontSize: typography.small,
    fontWeight: '600',
    color: colors.text,
    marginBottom: 2,
  },
  titleCompact: {
    fontSize: typography.caption,
  },
  meta: {
    fontSize: typography.caption,
    color: colors.textMuted,
    marginBottom: 4,
  },
  link: {
    alignSelf: 'flex-start',
  },
  linkPressed: {
    opacity: 0.7,
  },
  linkText: {
    fontSize: typography.caption,
    fontWeight: '600',
    color: colors.bronzeDark,
  },
  noLink: {
    fontSize: typography.caption,
    color: colors.textMuted,
    fontStyle: 'italic',
  },
})
