import { Pressable, StyleSheet, Text, View } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { useRouter } from 'expo-router'
import { useAuth } from '@/context/AuthContext'
import { colors, fontFamily, radii, spacing } from '@/theme'

/** Shown on home only for guests — signals limited / restricted access */
export function SessionBanner() {
  const router = useRouter()
  const { isGuest, signOut } = useAuth()

  const exitGuestMode = async () => {
    await signOut()
    router.replace('/(auth)/choice')
  }

  if (!isGuest) return null

  return (
    <View style={[styles.banner, styles.guestBanner]}>
      <Pressable
        onPress={exitGuestMode}
        style={({ pressed }) => [styles.guestBack, pressed && styles.pressed]}
        accessibilityRole="button"
        accessibilityLabel="Back to sign in options"
      >
        <Ionicons name="arrow-back" size={20} color={colors.brandBronzeLight} />
      </Pressable>
      <Pressable
        style={styles.guestMain}
        onPress={() => router.push('/(auth)/signup')}
      >
        <View style={styles.guestBadge}>
          <Text style={styles.guestBadgeText}>GUEST MODE</Text>
        </View>
        <Text style={styles.guestSub}>Limited access · Tap to unlock full access</Text>
        <Ionicons name="chevron-forward" size={18} color={colors.brandBronzeLight} />
      </Pressable>
    </View>
  )
}

const styles = StyleSheet.create({
  banner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingVertical: spacing.sm + 2,
    paddingHorizontal: spacing.md,
    borderRadius: radii.card,
    marginBottom: spacing.md,
    borderWidth: 1,
  },
  guestBanner: {
    backgroundColor: colors.brandNavy,
    borderColor: 'rgba(156, 123, 92, 0.4)',
    paddingLeft: spacing.sm,
  },
  guestBack: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
  },
  guestMain: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  pressed: {
    opacity: 0.75,
  },
  guestBadge: {
    paddingHorizontal: spacing.sm,
    paddingVertical: 5,
    borderRadius: radii.sm,
    backgroundColor: colors.brandBronze,
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
    fontFamily: fontFamily.body,
    fontSize: 11,
    color: colors.surfaceWhite,
    opacity: 0.8,
  },
})
