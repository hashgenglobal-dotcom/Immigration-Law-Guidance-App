import { StyleSheet, Text, View } from 'react-native'
import { useRouter } from 'expo-router'
import { AuthShell } from '@/components/auth/AuthShell'
import { WelcomeShowcase } from '@/components/welcome/WelcomeShowcase'
import { PrimaryButton } from '@/components'
import { FadeIn } from '@/components/digital'
import { useAuth } from '@/context/AuthContext'
import { colors, fontFamily, spacing } from '@/theme'

export default function WelcomeScreen() {
  const router = useRouter()
  const { completeOnboarding } = useAuth()

  const handleContinue = async () => {
    await completeOnboarding()
    router.replace('/(auth)/choice')
  }

  return (
    <AuthShell scroll>
      <WelcomeShowcase />
      <FadeIn delay={520} style={styles.ctaBlock}>
        <PrimaryButton label="Get started" onPress={handleContinue} variant="onDark" />
        <Text style={styles.legal}>
          General information only — not legal advice. By continuing you agree to our trust & privacy
          principles.
        </Text>
      </FadeIn>
    </AuthShell>
  )
}

const styles = StyleSheet.create({
  ctaBlock: {
    marginTop: 'auto',
    paddingTop: spacing.md,
  },
  legal: {
    fontFamily: fontFamily.body,
    fontSize: 11,
    lineHeight: 16,
    color: colors.surfaceWhite,
    opacity: 0.5,
    textAlign: 'center',
    marginTop: spacing.xs,
  },
})
