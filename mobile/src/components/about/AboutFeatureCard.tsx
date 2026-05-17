import { StyleSheet, Text, View } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import type { ComponentProps } from 'react'
import { cardStandard, colors, fontFamily, radii, shadows, spacing } from '@/theme'

type IoniconName = ComponentProps<typeof Ionicons>['name']

type CardAccent = 'navy' | 'bronze'

export function AboutFeatureCard({
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
      <View style={[styles.topBar, isNavy ? styles.topBarNavy : styles.topBarBronze]} />
      <View style={styles.indexBadge}>
        <Text style={styles.indexText}>{index}</Text>
      </View>
      <View style={[styles.iconSeal, isNavy ? styles.iconSealNavy : styles.iconSealBronze]}>
        <Ionicons name={icon} size={24} color={colors.surfaceWhite} />
      </View>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.body}>{description}</Text>
    </View>
  )
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
    minWidth: '46%',
    maxWidth: '48%',
    minHeight: 168,
    padding: spacing.md,
    paddingTop: spacing.sm + 4,
    borderWidth: 1,
    borderColor: 'rgba(31, 40, 57, 0.06)',
    overflow: 'hidden',
    ...cardStandard,
  },
  topBar: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 3,
  },
  topBarNavy: {
    backgroundColor: colors.brandNavy,
  },
  topBarBronze: {
    backgroundColor: colors.brandBronze,
  },
  indexBadge: {
    position: 'absolute',
    top: spacing.sm,
    right: spacing.sm,
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: colors.bronzeTint,
    borderWidth: 1,
    borderColor: 'rgba(31, 40, 57, 0.08)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  indexText: {
    fontFamily: fontFamily.body,
    fontSize: 10,
    fontWeight: '700',
    color: colors.brandNavy,
    opacity: 0.45,
  },
  iconSeal: {
    width: 48,
    height: 48,
    borderRadius: radii.button,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.sm,
    ...shadows.soft,
  },
  iconSealNavy: {
    backgroundColor: colors.brandNavy,
  },
  iconSealBronze: {
    backgroundColor: colors.brandBronze,
  },
  title: {
    fontFamily: fontFamily.heading,
    fontSize: 13,
    fontWeight: '600',
    color: colors.brandNavy,
    lineHeight: 18,
    marginBottom: spacing.xs,
  },
  body: {
    fontFamily: fontFamily.body,
    fontSize: 11,
    lineHeight: 16,
    fontWeight: '400',
    color: colors.brandNavy,
    opacity: 0.72,
  },
})
