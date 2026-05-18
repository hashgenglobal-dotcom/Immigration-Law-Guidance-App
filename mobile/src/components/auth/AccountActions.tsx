import { Pressable, StyleSheet, Text, View } from 'react-native'
import { useRouter } from 'expo-router'
import { Ionicons } from '@expo/vector-icons'
import { useAuth } from '@/context/AuthContext'
import { colors, fontFamily, radii, spacing, typography } from '@/theme'

export function AccountActions() {
  const router = useRouter()
  const { session, signOut } = useAuth()

  if (!session) return null

  const handleSignOut = async () => {
    await signOut()
    router.replace('/(auth)/choice')
  }

  return (
    <View style={styles.wrap}>
      <Pressable
        onPress={handleSignOut}
        style={({ pressed }) => [styles.btn, pressed && styles.pressed]}
        accessibilityRole="button"
      >
        <Ionicons name="log-out-outline" size={18} color={colors.brandNavy} />
        <Text style={styles.label}>Sign out</Text>
      </Pressable>
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: {
    marginBottom: spacing.lg,
    alignItems: 'center',
  },
  btn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    borderRadius: radii.full,
    backgroundColor: colors.surfaceWhite,
    borderWidth: 1,
    borderColor: 'rgba(31, 40, 57, 0.1)',
    minHeight: 48,
  },
  pressed: {
    opacity: 0.85,
  },
  label: {
    fontFamily: fontFamily.body,
    fontSize: typography.small,
    fontWeight: '600',
    color: colors.brandNavy,
  },
})
