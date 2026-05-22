import { Pressable, StyleSheet, Text, View } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import type { OfficialUpdateItem } from '@/types/updates'
import { cardStandard, colors, fontFamily, radii, spacing, typography } from '@/theme'

const PUBLISHER_LABEL: Record<string, string> = {
  uscis: 'USCIS',
  dhs: 'DHS',
  federal_register: 'Federal Register',
}

function publisherLabel(publisher: string): string {
  return PUBLISHER_LABEL[publisher] ?? publisher.replace(/_/g, ' ').toUpperCase()
}

function formatDate(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso.slice(0, 10)
  return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

export function UpdateCard({
  item,
  onPress,
}: {
  item: OfficialUpdateItem
  onPress: () => void
}) {
  const lead = item.summary_bullets[0] ?? 'Open the official release for details.'
  const tags = item.topic_labels.filter((l) => l !== 'General').slice(0, 2)

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [styles.card, cardStandard, pressed && styles.pressed]}
      accessibilityRole="button"
    >
      <View style={styles.metaRow}>
        <Text style={styles.publisher}>{publisherLabel(item.publisher)}</Text>
        <Text style={styles.date}>{formatDate(item.published_at)}</Text>
      </View>
      <Text style={styles.title} numberOfLines={2}>
        {item.title}
      </Text>
      <Text style={styles.lead} numberOfLines={2}>
        {lead}
      </Text>
      {tags.length > 0 ? (
        <View style={styles.tagRow}>
          {tags.map((label) => (
            <View key={label} style={styles.tag}>
              <Text style={styles.tagText}>{label}</Text>
            </View>
          ))}
        </View>
      ) : null}
      <View style={styles.footer}>
        <Text style={styles.footerText}>View summary</Text>
        <Ionicons name="chevron-forward" size={16} color={colors.brandBronze} />
      </View>
    </Pressable>
  )
}

const styles = StyleSheet.create({
  card: {
    padding: spacing.md,
    gap: spacing.xs,
  },
  pressed: {
    opacity: 0.92,
  },
  metaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  publisher: {
    fontFamily: fontFamily.body,
    fontSize: typography.caption,
    fontWeight: '700',
    color: colors.brandBronze,
    textTransform: 'uppercase',
    letterSpacing: 0.4,
  },
  date: {
    fontFamily: fontFamily.body,
    fontSize: typography.caption,
    color: colors.brandNavy,
    opacity: 0.55,
  },
  title: {
    fontFamily: fontFamily.heading,
    fontSize: typography.body,
    fontWeight: '600',
    color: colors.brandNavy,
    lineHeight: 22,
  },
  lead: {
    fontFamily: fontFamily.body,
    fontSize: typography.small,
    lineHeight: 19,
    color: colors.brandNavy,
    opacity: 0.78,
  },
  tagRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.xs,
    marginTop: spacing.xs,
  },
  tag: {
    backgroundColor: colors.bronzeTint,
    borderRadius: radii.full,
    paddingHorizontal: spacing.sm,
    paddingVertical: 3,
  },
  tagText: {
    fontFamily: fontFamily.body,
    fontSize: 10,
    fontWeight: '600',
    color: colors.brandNavy,
  },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: spacing.xs,
  },
  footerText: {
    fontFamily: fontFamily.body,
    fontSize: typography.caption,
    fontWeight: '600',
    color: colors.brandBronze,
  },
})
