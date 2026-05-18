import { useState } from 'react'
import { Pressable, StyleSheet, Text } from 'react-native'
import { useRouter } from 'expo-router'
import { AuthBackButton } from '@/components/auth/AuthBackButton'
import { AuthFormField } from '@/components/auth/AuthFormField'
import { AuthShell } from '@/components/auth/AuthShell'
import { PrimaryButton } from '@/components'
import { FadeIn } from '@/components/digital'
import { useAuth } from '@/context/AuthContext'
import { AUTH_PREVIEW_NOTICE } from '@/lib/legalCopy'
import { colors, fontFamily, spacing } from '@/theme'

export default function SignupScreen() {
  const router = useRouter()
  const { signUp } = useAuth()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const handleSignup = async () => {
    setError(null)
    setBusy(true)
    try {
      await signUp(name, email, password)
      router.replace('/')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not create account.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthShell>
      <AuthBackButton />

      <FadeIn>
        <Text style={styles.title}>Preview sign-up</Text>
        <Text style={styles.sub}>
          Unlocks full access for this app session only. Not a real account—nothing you enter is
          stored on this device.
        </Text>
        <Text style={styles.notice}>{AUTH_PREVIEW_NOTICE}</Text>
      </FadeIn>

      <FadeIn delay={100}>
        <AuthFormField
          label="Name"
          value={name}
          onChangeText={setName}
          placeholder="Your name"
          autoCapitalize="words"
        />
        <AuthFormField
          label="Email"
          value={email}
          onChangeText={setEmail}
          placeholder="you@example.com"
          keyboardType="email-address"
        />
        <AuthFormField
          label="Password"
          value={password}
          onChangeText={setPassword}
          placeholder="At least 6 characters"
          secureTextEntry
        />
        {error ? <Text style={styles.error}>{error}</Text> : null}
        <PrimaryButton
          label={busy ? 'Starting preview…' : 'Continue (preview)'}
          onPress={handleSignup}
          variant="onDark"
          disabled={busy}
        />
        <Pressable onPress={() => router.replace('/login')} style={styles.linkWrap}>
          <Text style={styles.link}>Try preview sign-in instead</Text>
        </Pressable>
      </FadeIn>
    </AuthShell>
  )
}

const styles = StyleSheet.create({
  title: {
    fontFamily: fontFamily.heading,
    fontSize: 28,
    fontWeight: '600',
    color: colors.surfaceWhite,
    marginBottom: spacing.xs,
  },
  sub: {
    fontFamily: fontFamily.body,
    fontSize: 14,
    color: colors.surfaceWhite,
    opacity: 0.75,
    marginBottom: spacing.sm,
  },
  notice: {
    fontFamily: fontFamily.body,
    fontSize: 11,
    lineHeight: 16,
    color: colors.surfaceWhite,
    opacity: 0.55,
    marginBottom: spacing.lg,
  },
  error: {
    fontFamily: fontFamily.body,
    fontSize: 13,
    color: '#FADBD8',
    marginBottom: spacing.sm,
  },
  linkWrap: {
    alignItems: 'center',
    padding: spacing.sm,
  },
  link: {
    fontFamily: fontFamily.body,
    fontSize: 14,
    color: colors.brandBronzeLight,
    fontWeight: '600',
  },
})
