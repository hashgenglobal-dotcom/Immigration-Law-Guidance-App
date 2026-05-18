import { Linking, Pressable, StyleSheet, Text, View } from 'react-native'
import type { OfficialSource } from '@/lib/mockData'
import { colors, spacing, typography } from '@/theme'

const typeLabels: Record<OfficialSource['type'], string> = {
  regulation: 'Regulation',
  statute: 'Statute',
  case: 'Case law',
  guidance: 'Guidance',
}

export function CitationCard({
  source,
  compact,
}: {
  source: OfficialSource
  compact?: boolean
}) {
  return (
    <View style={[styles.card, compact && styles.cardCompact]}>
      <Text style={[styles.title, compact && styles.titleCompact]} numberOfLines={2}>
        {source.title}
      </Text>
      <Text style={styles.meta} numberOfLines={1}>
        {typeLabels[source.type]} · {source.citation}
      </Text>
      <Pressable
        onPress={() => Linking.openURL(source.url)}
        style={({ pressed }) => [styles.link, pressed && styles.linkPressed]}
        accessibilityRole="link"
      >
        <Text style={styles.linkText}>View source</Text>
      </Pressable>
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
})
