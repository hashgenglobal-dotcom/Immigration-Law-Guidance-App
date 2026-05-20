import { StyleSheet, Text, View } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import type { ComponentProps } from 'react'
import { colors, fontFamily, spacing } from '@/theme'

type IoniconName = ComponentProps<typeof Ionicons>['name']

const PILLARS: { icon: IoniconName; label: string }[] = [
  { icon: 'document-text-outline', label: 'Cited' },
  { icon: 'lock-closed-outline', label: 'Private' },
  { icon: 'library-outline', label: 'Official' },
]

export function AboutTrustStrip() {
  return (
    <View style={styles.row}>
      {PILLARS.map((p) => (
        <View key={p.label} style={styles.item}>
          <View style={styles.iconRing}>
            <Ionicons name={p.icon} size={16} color={colors.brandBronzeLight} />
          </View>
          <Text style={styles.label} numberOfLines={1} adjustsFontSizeToFit minimumFontScale={0.85}>
            {p.label}
          </Text>
        </View>
      ))}
    </View>
  )
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    marginTop: spacing.md,
    paddingTop: spacing.md,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.12)',
    gap: spacing.xs,
  },
  item: {
    flex: 1,
    minWidth: 0,
    alignItems: 'center',
    gap: 6,
    paddingVertical: spacing.sm,
    paddingHorizontal: 2,
    borderRadius: 10,
    backgroundColor: 'rgba(255, 255, 255, 0.06)',
  },
  iconRing: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(156, 123, 92, 0.22)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  label: {
    fontFamily: fontFamily.body,
    fontSize: 10,
    fontWeight: '600',
    color: colors.surfaceWhite,
    letterSpacing: 0.4,
    textTransform: 'uppercase',
    textAlign: 'center',
  },
})
