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

export default function LoginScreen() {
  const router = useRouter()
  const { signIn } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const handleLogin = async () => {
    setError(null)
    setBusy(true)
    try {
      await signIn(email, password)
      router.replace('/')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not sign in.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthShell>
      <AuthBackButton />

      <FadeIn>
        <Text style={styles.title}>Preview sign-in</Text>
        <Text style={styles.sub}>
          Unlocks full access for this app session only. Not a real account—credentials are not
          saved.
        </Text>
        <Text style={styles.notice}>{AUTH_PREVIEW_NOTICE}</Text>
      </FadeIn>

      <FadeIn delay={100}>
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
          placeholder="••••••••"
          secureTextEntry
        />
        {error ? <Text style={styles.error}>{error}</Text> : null}
        <PrimaryButton
          label={busy ? 'Starting preview…' : 'Continue (preview)'}
          onPress={handleLogin}
          variant="onDark"
          disabled={busy}
        />
        <Pressable onPress={() => router.replace('/signup')} style={styles.linkWrap}>
          <Text style={styles.link}>Try preview sign-up instead</Text>
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
