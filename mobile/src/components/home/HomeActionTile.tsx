import { Alert, Pressable, StyleSheet, Text, View } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import type { ComponentProps } from 'react'
import { colors, fontFamily, layout, radii, shadows, spacing } from '@/theme'

type IoniconName = ComponentProps<typeof Ionicons>['name']
type TileVariant = 'primary' | 'secondary' | 'comingSoon'

export function HomeActionTile({
  title,
  subtitle,
  icon,
  variant,
  onPress,
  comingSoonLabel = 'Coming soon',
}: {
  title: string
  subtitle: string
  icon: IoniconName
  variant: TileVariant
  onPress?: () => void
  comingSoonLabel?: string
}) {
  const isPrimary = variant === 'primary'
  const isComingSoon = variant === 'comingSoon'

  const handlePress = () => {
    if (isComingSoon) {
      Alert.alert(
        comingSoonLabel,
        'This feature will be available in a future release.',
        [{ text: 'OK' }],
      )
      return
    }
    onPress?.()
  }

  return (
    <Pressable
      onPress={handlePress}
      accessibilityRole="button"
      accessibilityState={{ disabled: isComingSoon }}
      style={({ pressed }) => [
        styles.shell,
        isPrimary && styles.shellPrimary,
        variant === 'secondary' && styles.shellSecondary,
        isComingSoon && styles.shellComingSoon,
        pressed && !isComingSoon && styles.shellPressed,
        pressed && isComingSoon && styles.shellComingSoonPressed,
      ]}
    >
      {variant === 'secondary' ? <View style={styles.navyAccent} /> : null}
      <View style={[styles.iconSeal, isPrimary && styles.iconSealPrimary, isComingSoon && styles.iconSealMuted]}>
        <Ionicons
          name={isComingSoon ? 'time-outline' : icon}
          size={22}
          color={isPrimary ? colors.surfaceWhite : isComingSoon ? colors.textMuted : colors.brandBronze}
        />
      </View>
      <View style={styles.copy}>
        <View style={styles.titleRow}>
          <Text
            style={[styles.title, isPrimary && styles.titlePrimary, isComingSoon && styles.titleMuted]}
            numberOfLines={1}
          >
            {title}
          </Text>
          {isComingSoon ? (
            <View style={styles.soonBadge}>
              <Text style={styles.soonBadgeText}>{comingSoonLabel}</Text>
            </View>
          ) : null}
        </View>
        <Text
          style={[styles.subtitle, isPrimary && styles.subtitlePrimary, isComingSoon && styles.subtitleMuted]}
          numberOfLines={2}
        >
          {subtitle}
        </Text>
      </View>
      <View
        style={[
          styles.chevronWrap,
          isPrimary && styles.chevronWrapPrimary,
          isComingSoon && styles.chevronWrapMuted,
        ]}
      >
        <Ionicons
          name={isComingSoon ? 'lock-closed-outline' : 'chevron-forward'}
          size={18}
          color={isPrimary ? colors.brandBronzeLight : isComingSoon ? colors.textMuted : colors.brandNavy}
        />
      </View>
    </Pressable>
  )
}

const styles = StyleSheet.create({
  shell: {
    flexDirection: 'row',
    alignItems: 'center',
    minHeight: layout.minTouchTarget + 16,
    borderRadius: radii.card,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.md,
    gap: spacing.sm,
    overflow: 'hidden',
  },
  shellPrimary: {
    backgroundColor: colors.brandNavy,
    borderWidth: 1,
    borderColor: 'rgba(156, 123, 92, 0.45)',
    ...shadows.soft,
  },
  shellSecondary: {
    backgroundColor: colors.surfaceWhite,
    borderWidth: 1,
    borderColor: 'rgba(31, 40, 57, 0.08)',
    ...shadows.soft,
  },
  shellComingSoon: {
    backgroundColor: 'rgba(255, 255, 255, 0.65)',
    borderWidth: 1,
    borderColor: 'rgba(31, 40, 57, 0.08)',
    borderStyle: 'dashed',
  },
  shellPressed: {
    opacity: 0.94,
    transform: [{ scale: 0.995 }],
  },
  shellComingSoonPressed: {
    opacity: 0.88,
  },
  navyAccent: {
    position: 'absolute',
    left: 0,
    top: 0,
    bottom: 0,
    width: 4,
    backgroundColor: colors.brandNavy,
  },
  iconSeal: {
    width: 48,
    height: 48,
    borderRadius: radii.button,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.bronzeTint,
  },
  iconSealPrimary: {
    backgroundColor: 'rgba(156, 123, 92, 0.28)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  iconSealMuted: {
    backgroundColor: colors.parchment,
  },
  copy: {
    flex: 1,
    paddingRight: spacing.xs,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: spacing.xs,
    marginBottom: 4,
  },
  title: {
    fontFamily: fontFamily.heading,
    fontSize: 16,
    fontWeight: '600',
    color: colors.brandNavy,
    letterSpacing: -0.2,
  },
  titlePrimary: {
    color: colors.surfaceWhite,
  },
  titleMuted: {
    color: colors.brandNavy,
    opacity: 0.55,
  },
  subtitle: {
    fontFamily: fontFamily.body,
    fontSize: 12,
    lineHeight: 17,
    color: colors.brandNavy,
    opacity: 0.72,
  },
  subtitlePrimary: {
    color: colors.surfaceWhite,
    opacity: 0.8,
  },
  subtitleMuted: {
    opacity: 0.45,
  },
  soonBadge: {
    backgroundColor: colors.bronzeTint,
    borderRadius: radii.full,
    paddingHorizontal: spacing.sm,
    paddingVertical: 3,
    borderWidth: 1,
    borderColor: 'rgba(156, 123, 92, 0.25)',
  },
  soonBadgeText: {
    fontFamily: fontFamily.body,
    fontSize: 9,
    fontWeight: '700',
    color: colors.brandBronze,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  chevronWrap: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.bronzeTint,
  },
  chevronWrapPrimary: {
    backgroundColor: 'rgba(255, 255, 255, 0.12)',
  },
  chevronWrapMuted: {
    backgroundColor: colors.parchment,
  },
})
