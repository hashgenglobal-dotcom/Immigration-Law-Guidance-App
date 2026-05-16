import { StyleSheet, Text, View } from 'react-native'
import type { RiskLevel } from '@/lib/mockData'
import { colors, typography } from '@/theme'

const stylesByLevel: Record<RiskLevel, { bg: string; text: string; border: string }> = {
  low: { bg: colors.riskLowBg, text: colors.riskLowText, border: colors.riskLowBorder },
  medium: { bg: colors.riskMediumBg, text: colors.riskMediumText, border: colors.riskMediumBorder },
  high: { bg: colors.riskHighBg, text: colors.riskHighText, border: colors.riskHighBorder },
}

export function RiskBadge({ level }: { level: RiskLevel }) {
  const s = stylesByLevel[level]
  return (
    <View style={[styles.badge, { backgroundColor: s.bg, borderColor: s.border }]}>
      <Text style={[styles.text, { color: s.text }]}>{level.toUpperCase()}</Text>
    </View>
  )
}

const styles = StyleSheet.create({
  badge: {
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  text: {
    fontSize: typography.caption,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
})
