import { StyleSheet, Text, View } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { DigitalHeroArt } from '@/components/digital'
import { brand } from '@/lib/brand'
import { HomeChatPrompt } from './HomeChatPrompt'
import { colors, fontFamily, radii, shadows, spacing } from '@/theme'

export function HomeHero({ onOpenAssistant }: { onOpenAssistant: () => void }) {
  return (
    <View style={styles.hero}>
      <DigitalHeroArt />
      <View style={styles.content}>
        <View style={styles.mottoBadge}>
          <View style={styles.mottoIconRing}>
            <Ionicons name="scale-outline" size={14} color={colors.surfaceWhite} />
          </View>
          <Text style={styles.mottoText}>{brand.motto}</Text>
        </View>
        <Text style={styles.title}>{brand.name}</Text>
        <Text style={styles.tagline}>{brand.tagline}</Text>
        <Text style={styles.subtitle}>{brand.description}</Text>
        <HomeChatPrompt onPress={onOpenAssistant} />
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  hero: {
    position: 'relative',
    borderRadius: radii.card,
    marginBottom: spacing.md,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: 'rgba(156, 123, 92, 0.35)',
    backgroundColor: colors.brandNavy,
    ...shadows.soft,
  },
  content: {
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.lg,
    zIndex: 1,
  },
  mottoBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    gap: spacing.sm,
    borderRadius: radii.full,
    borderWidth: 1,
    borderColor: 'rgba(156, 123, 92, 0.45)',
    backgroundColor: colors.bronzeTint,
    paddingRight: spacing.md,
    paddingLeft: 6,
    paddingVertical: 6,
    marginBottom: spacing.md,
  },
  mottoIconRing: {
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.brandBronze,
  },
  mottoText: {
    fontFamily: fontFamily.body,
    fontSize: 12,
    fontWeight: '600',
    color: colors.brandNavy,
    letterSpacing: 0.4,
  },
  title: {
    fontFamily: fontFamily.heading,
    fontSize: 26,
    fontWeight: '600',
    color: colors.surfaceWhite,
    letterSpacing: -0.4,
    marginBottom: spacing.xs,
  },
  tagline: {
    fontFamily: fontFamily.body,
    fontSize: 16,
    fontWeight: '400',
    color: colors.surfaceWhite,
    lineHeight: 24,
    opacity: 0.95,
    marginBottom: spacing.sm,
  },
  subtitle: {
    fontFamily: fontFamily.body,
    fontSize: 13,
    lineHeight: 20,
    color: colors.surfaceWhite,
    opacity: 0.82,
    flexShrink: 1,
  },
})
