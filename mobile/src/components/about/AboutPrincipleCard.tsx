import { StyleSheet, Text, View } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import type { ComponentProps } from 'react'
import { colors, fontFamily, layout, radii, shadows, spacing } from '@/theme'

type IoniconName = ComponentProps<typeof Ionicons>['name']
type CardAccent = 'navy' | 'bronze'

export function AboutPrincipleCard({
  title,
  description,
  icon,
  accent = 'navy',
  index,
}: {
  title: string
  description: string
  icon: IoniconName
  accent?: CardAccent
  index: number
}) {
  const isNavy = accent === 'navy'

  return (
    <View style={styles.card}>
      <View style={[styles.accentBar, isNavy ? styles.accentNavy : styles.accentBronze]} />
      <View style={[styles.iconSeal, isNavy ? styles.iconNavy : styles.iconBronze]}>
        <Ionicons name={icon} size={22} color={colors.surfaceWhite} />
      </View>
      <View style={styles.copy}>
        <Text style={styles.title}>{title}</Text>
        <Text style={styles.body}>{description}</Text>
      </View>
      <View style={styles.indexWrap}>
        <Text style={styles.indexText}>{String(index).padStart(2, '0')}</Text>
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    minHeight: layout.minTouchTarget + 20,
    paddingVertical: spacing.md,
    paddingRight: spacing.md,
    paddingLeft: spacing.sm,
    marginBottom: spacing.sm,
    borderRadius: radii.card,
    backgroundColor: colors.parchment,
    borderWidth: 1,
    borderColor: 'rgba(31, 40, 57, 0.06)',
    overflow: 'hidden',
    gap: spacing.sm,
    ...shadows.soft,
  },
  accentBar: {
    position: 'absolute',
    left: 0,
    top: 0,
    bottom: 0,
    width: 4,
  },
  accentNavy: {
    backgroundColor: colors.brandNavy,
  },
  accentBronze: {
    backgroundColor: colors.brandBronze,
  },
  iconSeal: {
    width: 46,
    height: 46,
    borderRadius: 23,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: spacing.xs,
    ...shadows.soft,
  },
  iconNavy: {
    backgroundColor: colors.brandNavy,
  },
  iconBronze: {
    backgroundColor: colors.brandBronze,
  },
  copy: {
    flex: 1,
    paddingVertical: 2,
  },
  title: {
    fontFamily: fontFamily.heading,
    fontSize: 14,
    fontWeight: '600',
    color: colors.brandNavy,
    lineHeight: 19,
    marginBottom: 4,
  },
  body: {
    fontFamily: fontFamily.body,
    fontSize: 12,
    lineHeight: 17,
    color: colors.brandNavy,
    opacity: 0.72,
  },
  indexWrap: {
    width: 36,
    alignItems: 'center',
    justifyContent: 'center',
  },
  indexText: {
    fontFamily: fontFamily.heading,
    fontSize: 18,
    fontWeight: '600',
    color: colors.brandBronze,
    opacity: 0.35,
  },
})
