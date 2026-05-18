import { StyleSheet, Text, View } from 'react-native'
import { useRouter } from 'expo-router'
import { SourcePathLogoMark } from '@/components/brand/SourcePathLogoMark'
import { AccessBadge } from '@/components/auth/AccessBadge'
import { AuthBackButton } from '@/components/auth/AuthBackButton'
import { AuthShell } from '@/components/auth/AuthShell'
import { GuestModeButton } from '@/components/auth/GuestModeButton'
import { PrimaryButton } from '@/components'
import { useAuth } from '@/context/AuthContext'
import { brand } from '@/lib/brand'
import { colors, fontFamily, radii, spacing } from '@/theme'

export default function AuthChoiceScreen() {
  const router = useRouter()
  const { signInAsGuest } = useAuth()

  const handleGuest = async () => {
    await signInAsGuest()
    router.replace('/(main)')
  }

  return (
    <AuthShell scroll>
      <AuthBackButton fallback="/(auth)/welcome" />

      <View style={styles.logoWrap}>
        <SourcePathLogoMark size={80} />
      </View>

      <Text style={styles.eyebrow}>Welcome to {brand.name}</Text>
      <Text style={styles.title}>Choose How To Continue</Text>
      <Text style={styles.sub}>
        Pick how you want to use SourcePath. Guest mode saves only your preview question count on
        this device—no email or password is stored.
      </Text>

      <View style={styles.sectionCard}>
        <AccessBadge variant="full" />
        <Text style={styles.sectionTitle}>Preview full access</Text>
        <Text style={styles.sectionHint}>
          Try unlimited Ask for this app session only. Real sign-in is not live yet—nothing you
          enter is saved on your device.
        </Text>
        <PrimaryButton
          label="Try preview sign-up"
          onPress={() => router.push('/(auth)/signup')}
          variant="onDark"
        />
        <PrimaryButton
          label="Try preview sign-in"
          onPress={() => router.push('/(auth)/login')}
          variant="secondary"
        />
      </View>

      <View style={styles.sectionCard}>
        <AccessBadge variant="limited" />
        <Text style={styles.sectionTitle}>Guest Mode</Text>
        <Text style={styles.sectionHint}>
          Limited access — explore the app without signing in. Some features stay restricted.
        </Text>
        <GuestModeButton onPress={handleGuest} />
      </View>
    </AuthShell>
  )
}

const styles = StyleSheet.create({
  logoWrap: {
    marginBottom: spacing.lg,
  },
  eyebrow: {
    fontFamily: fontFamily.body,
    fontSize: 11,
    fontWeight: '600',
    color: colors.brandBronzeLight,
    letterSpacing: 1,
    textTransform: 'uppercase',
    marginBottom: spacing.xs,
  },
  title: {
    fontFamily: fontFamily.heading,
    fontSize: 28,
    fontWeight: '600',
    color: colors.surfaceWhite,
    letterSpacing: -0.4,
    marginBottom: spacing.sm,
  },
  sub: {
    fontFamily: fontFamily.body,
    fontSize: 14,
    lineHeight: 22,
    color: colors.surfaceWhite,
    opacity: 0.88,
    marginBottom: spacing.lg,
  },
  sectionCard: {
    padding: spacing.md,
    marginBottom: spacing.md,
    borderRadius: radii.card,
    backgroundColor: 'rgba(255, 255, 255, 0.06)',
    borderWidth: 1,
    borderColor: 'rgba(156, 123, 92, 0.35)',
  },
  sectionTitle: {
    fontFamily: fontFamily.heading,
    fontSize: 16,
    fontWeight: '600',
    color: colors.surfaceWhite,
    marginBottom: spacing.xs,
  },
  sectionHint: {
    fontFamily: fontFamily.body,
    fontSize: 12,
    lineHeight: 18,
    color: colors.surfaceWhite,
    opacity: 0.72,
    marginBottom: spacing.md,
  },
})
