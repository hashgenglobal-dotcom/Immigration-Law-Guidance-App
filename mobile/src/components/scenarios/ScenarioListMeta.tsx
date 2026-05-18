import { StyleSheet, Text, View } from 'react-native'
import { colors, fontFamily, spacing, typography } from '@/theme'

export function ScenarioListMeta({
  visible,
  total,
}: {
  visible: number
  total: number
}) {
  const label =
    visible === total
      ? `${visible} guide${visible === 1 ? '' : 's'}`
      : `Showing ${visible} of ${total}`

  return (
    <View style={styles.row}>
      <View style={styles.accent} />
      <Text style={styles.label}>{label}</Text>
    </View>
  )
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginBottom: spacing.sm,
  },
  accent: {
    width: 3,
    height: 14,
    borderRadius: 2,
    backgroundColor: colors.brandNavy,
  },
  label: {
    fontFamily: fontFamily.body,
    fontSize: typography.caption,
    fontWeight: '600',
    color: colors.brandNavy,
    letterSpacing: 0.3,
    textTransform: 'uppercase',
  },
})
