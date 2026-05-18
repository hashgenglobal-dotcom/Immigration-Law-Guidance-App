import { StyleSheet, Text, View } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import type { ComponentProps } from 'react'
import { colors, fontFamily, radii, spacing } from '@/theme'

type IoniconName = ComponentProps<typeof Ionicons>['name']

const SIGNALS: { icon: IoniconName; label: string }[] = [
  { icon: 'git-network-outline', label: 'Digital law' },
  { icon: 'shield-half-outline', label: 'Immigrant rights' },
  { icon: 'document-attach-outline', label: 'Official sources' },
]

/** Short cues so the logo area explains what SourcePath does */
export function LogoAppExplainer() {
  return (
    <View style={styles.wrap}>
      <Text style={styles.headline}>
        Cited immigration guidance from USCIS, eCFR & INA — not unchecked AI guesses.
      </Text>
      <View style={styles.chips}>
        {SIGNALS.map((s) => (
          <View key={s.label} style={styles.chip}>
            <Ionicons name={s.icon} size={12} color={colors.brandBronzeLight} />
            <Text style={styles.chipText}>{s.label}</Text>
          </View>
        ))}
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: {
    alignItems: 'center',
    gap: spacing.sm,
    marginBottom: spacing.lg,
    paddingHorizontal: spacing.sm,
  },
  headline: {
    fontFamily: fontFamily.body,
    fontSize: 12,
    lineHeight: 18,
    color: colors.surfaceWhite,
    opacity: 0.82,
    textAlign: 'center',
    maxWidth: 320,
  },
  chips: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: spacing.xs,
  },
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: spacing.sm,
    paddingVertical: 5,
    borderRadius: radii.full,
    backgroundColor: 'rgba(156, 123, 92, 0.18)',
    borderWidth: 1,
    borderColor: 'rgba(156, 123, 92, 0.4)',
  },
  chipText: {
    fontFamily: fontFamily.body,
    fontSize: 10,
    fontWeight: '600',
    color: colors.brandBronzeLight,
    letterSpacing: 0.4,
    textTransform: 'uppercase',
  },
})
