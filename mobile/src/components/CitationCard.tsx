import { Linking, Pressable, StyleSheet, Text, View } from 'react-native'
import type { OfficialSource } from '@/lib/mockData'
import { colors, spacing, typography } from '@/theme'

const typeLabels: Record<OfficialSource['type'], string> = {
  regulation: 'Regulation',
  statute: 'Statute',
  case: 'Case law',
  guidance: 'Agency guidance',
}

export function CitationCard({ source }: { source: OfficialSource }) {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>{source.title}</Text>
      <Text style={styles.meta}>
        {typeLabels[source.type]} · {source.citation}
      </Text>
      <Pressable
        onPress={() => Linking.openURL(source.url)}
        style={({ pressed }) => [styles.link, pressed && styles.linkPressed]}
        accessibilityRole="link"
      >
        <Text style={styles.linkText}>View official source</Text>
      </Pressable>
    </View>
  )
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderLeftWidth: 4,
    borderLeftColor: colors.primary,
    borderRadius: 12,
    padding: spacing.md,
    marginBottom: spacing.sm,
  },
  title: {
    fontSize: typography.body,
    fontWeight: '600',
    color: colors.text,
    marginBottom: spacing.xs,
  },
  meta: {
    fontSize: typography.caption,
    color: colors.textMuted,
    marginBottom: spacing.sm,
  },
  link: {
    alignSelf: 'flex-start',
    paddingVertical: spacing.xs,
  },
  linkPressed: {
    opacity: 0.7,
  },
  linkText: {
    fontSize: typography.small,
    fontWeight: '600',
    color: colors.primary,
  },
})
