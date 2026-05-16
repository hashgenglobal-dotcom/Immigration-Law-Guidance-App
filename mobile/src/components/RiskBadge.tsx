import { StyleSheet, Text, View } from 'react-native'
import type { RiskLevel } from '@/lib/mockData'
import { colors, typography } from '@/theme'

const stylesByLevel: Record<RiskLevel, { bg: string; text: string; border: string }> = {
  low: { bg: colors.riskLowBg, text: colors.riskLowText, border: colors.riskLowBorder },
  medium: { bg: colors.riskMediumBg, text: colors.riskMediumText, border: colors.riskMediumBorder },
  high: { bg: colors.riskHighBg, text: colors.riskHighText, border: colors.riskHighBorder },
}

export function RiskBadge({ level, small }: { level: RiskLevel; small?: boolean }) {
  const s = stylesByLevel[level]
  return (
    <View
      style={[
        styles.badge,
        small && styles.badgeSmall,
        { backgroundColor: s.bg, borderColor: s.border },
      ]}
    >
      <Text style={[styles.text, small && styles.textSmall, { color: s.text }]}>
        {level}
      </Text>
    </View>
  )
}

const styles = StyleSheet.create({
  badge: {
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  badgeSmall: {
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  text: {
    fontSize: typography.caption,
    fontWeight: '600',
    textTransform: 'capitalize',
    letterSpacing: 0.2,
  },
  textSmall: {
    fontSize: 10,
  },
})
