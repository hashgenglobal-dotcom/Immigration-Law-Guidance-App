import { StyleSheet, Text, View } from 'react-native'
import type { RiskLevel } from '@/lib/mockData'
import { fontFamily, typography } from '@/theme'

/** WCAG-friendly pairings on parchment backgrounds */
const RISK_STYLES: Record<RiskLevel, { bg: string; text: string }> = {
  high: { bg: '#FADBD8', text: '#8B3A3A' },
  medium: { bg: '#FDEBD0', text: '#8B6508' },
  low: { bg: '#EAECE4', text: '#4A5D23' },
}

export function RiskBadge({ level, small }: { level: RiskLevel; small?: boolean }) {
  const palette = RISK_STYLES[level]
  return (
    <View style={[styles.badge, small && styles.badgeSmall, { backgroundColor: palette.bg }]}>
      <Text style={[styles.text, small && styles.textSmall, { color: palette.text }]}>
        {level}
      </Text>
    </View>
  )
}

const styles = StyleSheet.create({
  badge: {
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  badgeSmall: {
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  text: {
    fontFamily: fontFamily.body,
    fontSize: typography.caption,
    fontWeight: '600',
    textTransform: 'capitalize',
    letterSpacing: 0.15,
  },
  textSmall: {
    fontSize: 10,
  },
})
