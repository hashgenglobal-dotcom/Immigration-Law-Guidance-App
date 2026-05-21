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
    router.replace('/')
  }

  return (
    <AuthShell scroll>
      <AuthBackButton fallback="/welcome" />

      <View style={styles.logoWrap}>
        <SourcePathLogoMark size={80} />
      </View>

      <Text style={styles.eyebrow}>Welcome to {brand.name}</Text>
      <Text style={styles.title}>Choose How To Continue</Text>
      <Text style={styles.sub}>
        Pick how you want to use SourcePath. Guest mode only remembers how many questions you have
        asked on this device—no email or password is stored.
      </Text>

      <View style={styles.sectionCard}>
        <AccessBadge variant="full" />
        <Text style={styles.sectionTitle}>Account</Text>
        <Text style={styles.sectionHint}>
          Sign up or sign in with email. Your questions and answers are not stored on the server—a
          secure sign-in token is kept on this device only.
        </Text>
        <PrimaryButton
          label="Create account"
          onPress={() => router.push('/signup')}
          variant="onDark"
        />
        <PrimaryButton
          label="Sign in"
          onPress={() => router.push('/login')}
          variant="secondary"
        />
      </View>

      <View style={styles.sectionCard}>
        <AccessBadge variant="limited" />
        <Text style={styles.sectionTitle}>Guest mode</Text>
        <Text style={styles.sectionHint}>
          Limited access—try Ask without an account. A small number of questions per device; no sign-in
          required.
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
