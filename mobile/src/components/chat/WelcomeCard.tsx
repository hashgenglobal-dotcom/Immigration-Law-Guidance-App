import { StyleSheet, Text, View } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import type { ComponentProps } from 'react'
import { appImages } from '@/assets/images'
import { IllustrationBanner } from '@/components/digital'
import { brand } from '@/lib/brand'
import { cardStandard, colors, fontFamily, radii, spacing } from '@/theme'

type IoniconName = ComponentProps<typeof Ionicons>['name']

const BULLETS: { icon: IoniconName; title: string; body: string }[] = [
  {
    icon: 'chatbubble-outline',
    title: 'Ask anything',
    body: 'Type your question in plain language.',
  },
  {
    icon: 'book-outline',
    title: 'Official sources',
    body: 'Answers are grounded in US law and agency guidance.',
  },
  {
    icon: 'checkmark-circle-outline',
    title: 'Clear guidance',
    body: 'Structured summaries with citations—not legal advice.',
  },
]

function WelcomeBullet({
  icon,
  title,
  body,
}: {
  icon: IoniconName
  title: string
  body: string
}) {
  return (
    <View style={styles.bulletRow}>
      <View style={styles.bulletIconRing}>
        <Ionicons name={icon} size={18} color={colors.brandBronze} />
      </View>
      <View style={styles.bulletCopy}>
        <Text style={styles.bulletTitle}>{title}</Text>
        <Text style={styles.bulletBody}>{body}</Text>
      </View>
    </View>
  )
}

/** Empty-state welcome — centered SourcePath intro + how the assistant works. */
export function WelcomeCard() {
  return (
    <View style={styles.wrap}>
      <View style={styles.brandBlock}>
        <View style={styles.mottoPill}>
          <Ionicons name="scale-outline" size={13} color={colors.surfaceWhite} />
          <Text style={styles.mottoText}>{brand.motto}</Text>
        </View>
        <Text style={styles.brandName}>{brand.name}</Text>
        <Text style={styles.brandTagline}>{brand.tagline}</Text>
        <Text style={styles.brandHint}>
          General information only—not legal advice. Start a conversation below.
        </Text>
      </View>

      <View style={styles.card}>
        <IllustrationBanner source={appImages.askWelcome} height={100} />
        {BULLETS.map((b) => (
          <WelcomeBullet key={b.title} icon={b.icon} title={b.title} body={b.body} />
        ))}
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: spacing.lg,
    paddingHorizontal: spacing.xs,
    minHeight: 320,
    gap: spacing.lg,
  },
  brandBlock: {
    alignItems: 'center',
    maxWidth: 340,
  },
  mottoPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: colors.brandBronze,
    borderRadius: radii.full,
    paddingHorizontal: spacing.sm + 2,
    paddingVertical: 6,
    marginBottom: spacing.sm,
  },
  mottoText: {
    fontFamily: fontFamily.body,
    fontSize: 11,
    fontWeight: '600',
    color: colors.surfaceWhite,
    letterSpacing: 0.5,
  },
  brandName: {
    fontFamily: fontFamily.heading,
    fontSize: 24,
    fontWeight: '600',
    color: colors.brandNavy,
    letterSpacing: -0.3,
    marginBottom: spacing.xs,
  },
  brandTagline: {
    fontFamily: fontFamily.body,
    fontSize: 15,
    lineHeight: 22,
    color: colors.brandNavy,
    opacity: 0.85,
    textAlign: 'center',
    marginBottom: spacing.sm,
  },
  brandHint: {
    fontFamily: fontFamily.body,
    fontSize: 12,
    lineHeight: 18,
    color: colors.textMuted,
    textAlign: 'center',
  },
  card: {
    width: '100%',
    maxWidth: 360,
    padding: spacing.lg,
    gap: spacing.md,
    ...cardStandard,
  },
  bulletRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  bulletIconRing: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.bronzeTint,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 2,
  },
  bulletCopy: {
    flex: 1,
    gap: 2,
  },
  bulletTitle: {
    fontFamily: fontFamily.body,
    fontSize: 14,
    fontWeight: '600',
    color: colors.brandNavy,
  },
  bulletBody: {
    fontFamily: fontFamily.body,
    fontSize: 13,
    lineHeight: 19,
    fontWeight: '400',
    color: colors.brandNavy,
    opacity: 0.72,
  },
})
