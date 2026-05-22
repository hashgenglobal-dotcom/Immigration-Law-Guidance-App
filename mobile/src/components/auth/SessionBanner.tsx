import { Pressable, StyleSheet, Text, View } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { useRouter } from 'expo-router'
import { useAuth } from '@/context/AuthContext'
import { colors, fontFamily, radii, spacing } from '@/theme'

/** Shown on home only for guests — signals limited access (no stack-style back control) */
export function SessionBanner() {
  const router = useRouter()
  const { isGuest, signOut } = useAuth()

  const openSignInOptions = async () => {
    await signOut()
    router.replace('/choice')
  }

  if (!isGuest) return null

  return (
    <View style={[styles.banner, styles.guestBanner]}>
      <Pressable
        style={({ pressed }) => [styles.guestMain, pressed && styles.pressed]}
        onPress={() => router.push('/signup')}
        accessibilityRole="button"
        accessibilityLabel="Guest mode, limited access. Tap for full access sign up"
      >
        <View style={styles.guestBadge}>
          <Text style={styles.guestBadgeText}>GUEST MODE</Text>
        </View>
        <Text style={styles.guestSub} numberOfLines={2}>
          Limited access · Tap to sign up for full access
        </Text>
        <Ionicons name="chevron-forward" size={18} color={colors.brandBronzeLight} />
      </Pressable>
      <Pressable
        onPress={openSignInOptions}
        style={({ pressed }) => [styles.signInLink, pressed && styles.pressed]}
        accessibilityRole="button"
        accessibilityLabel="Sign in options"
      >
        <Text style={styles.signInLinkText}>Sign in options</Text>
      </Pressable>
    </View>
  )
}

const styles = StyleSheet.create({
  banner: {
    borderRadius: radii.card,
    marginBottom: spacing.md,
    borderWidth: 1,
    overflow: 'hidden',
  },
  guestBanner: {
    backgroundColor: colors.brandNavy,
    borderColor: 'rgba(156, 123, 92, 0.4)',
  },
  guestMain: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingVertical: spacing.sm + 2,
    paddingHorizontal: spacing.md,
  },
  pressed: {
    opacity: 0.75,
  },
  guestBadge: {
    paddingHorizontal: spacing.sm,
    paddingVertical: 5,
    borderRadius: radii.sm,
    backgroundColor: colors.brandBronze,
    flexShrink: 0,
  },
  guestBadgeText: {
    fontFamily: fontFamily.body,
    fontSize: 10,
    fontWeight: '700',
    color: colors.surfaceWhite,
    letterSpacing: 0.8,
  },
  guestSub: {
    flex: 1,
    flexShrink: 1,
    fontFamily: fontFamily.body,
    fontSize: 11,
    lineHeight: 15,
    color: colors.surfaceWhite,
    opacity: 0.85,
  },
  signInLink: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.1)',
    minHeight: 40,
  },
  signInLinkText: {
    fontFamily: fontFamily.body,
    fontSize: 12,
    fontWeight: '600',
    color: colors.brandBronzeLight,
    textDecorationLine: 'underline',
  },
})
