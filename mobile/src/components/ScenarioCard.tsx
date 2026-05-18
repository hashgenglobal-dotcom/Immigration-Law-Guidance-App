import { Pressable, StyleSheet, Text, View } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import type { Scenario } from '@/lib/mockData'
import { RiskBadge } from './RiskBadge'
import { cardStandard, colors, fontFamily, layout, radii, spacing } from '@/theme'

const CARD_MARGIN_BOTTOM = 16

export function ScenarioCard({
  scenario,
  onPress,
}: {
  scenario: Scenario
  onPress: () => void
}) {
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [styles.cardOuter, pressed && styles.cardPressed]}
      accessibilityRole="button"
    >
      <View style={styles.navyAccent} />
      <View style={styles.card}>
        <View style={styles.main}>
          <View style={styles.titleRow}>
            <Text style={styles.title} numberOfLines={2}>
              {scenario.title}
            </Text>
            <RiskBadge level={scenario.riskLevel} small />
          </View>
          <Text style={styles.description} numberOfLines={2}>
            {scenario.shortDescription}
          </Text>
          <View style={styles.footer}>
            <Text style={styles.openLabel}>Open guide</Text>
            <Ionicons name="arrow-forward" size={14} color={colors.brandBronze} />
          </View>
        </View>
        <View style={styles.bookmarkWrap} pointerEvents="none">
          <Ionicons name="bookmark-outline" size={20} color={colors.brandBronze} />
        </View>
      </View>
    </Pressable>
  )
}

const styles = StyleSheet.create({
  cardOuter: {
    flexDirection: 'row',
    marginBottom: CARD_MARGIN_BOTTOM,
    minHeight: layout.minTouchTarget,
    overflow: 'hidden',
    ...cardStandard,
  },
  cardPressed: {
    opacity: 0.97,
    transform: [{ scale: 0.995 }],
  },
  navyAccent: {
    width: 4,
    backgroundColor: colors.brandNavy,
  },
  card: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    backgroundColor: colors.surfaceWhite,
    borderTopWidth: 1,
    borderTopColor: 'rgba(31, 40, 57, 0.06)',
  },
  main: {
    flex: 1,
    paddingRight: spacing.sm,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: spacing.sm,
    marginBottom: 6,
  },
  title: {
    flex: 1,
    fontFamily: fontFamily.heading,
    fontSize: 15,
    fontWeight: '600',
    lineHeight: 20,
    color: colors.brandNavy,
  },
  description: {
    fontFamily: fontFamily.body,
    fontSize: 13,
    lineHeight: 19,
    fontWeight: '400',
    color: colors.brandNavy,
    opacity: 0.68,
    marginBottom: spacing.sm,
  },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  openLabel: {
    fontFamily: fontFamily.body,
    fontSize: 12,
    fontWeight: '600',
    color: colors.brandBronze,
  },
  bookmarkWrap: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.bronzeTint,
    borderWidth: 1,
    borderColor: 'rgba(31, 40, 57, 0.06)',
  },
})
