import { Pressable, StyleSheet, Text, View } from 'react-native'
import { useRouter } from 'expo-router'
import type { NativeStackHeaderProps } from '@react-navigation/native-stack'
import { getHeaderTitle } from '@react-navigation/elements'
import { Ionicons } from '@expo/vector-icons'
import { useSafeAreaInsets } from 'react-native-safe-area-context'
import { useAuth } from '@/context/AuthContext'
import { colors, fontFamily, spacing } from '@/theme'

/** Custom navy header with always-visible back control for guest sessions */
export function GuestStackHeader({ options, navigation }: NativeStackHeaderProps) {
  const insets = useSafeAreaInsets()
  const router = useRouter()
  const { signOut } = useAuth()
  const title = getHeaderTitle(options, '')

  const handleBack = async () => {
    if (navigation.canGoBack()) {
      navigation.goBack()
      return
    }
    await signOut()
    router.replace('/(auth)/choice')
  }

  return (
    <View style={[styles.wrap, { paddingTop: insets.top }]}>
      <View style={styles.bar}>
        <Pressable
          onPress={handleBack}
          style={({ pressed }) => [styles.backBtn, pressed && styles.pressed]}
          accessibilityRole="button"
          accessibilityLabel="Go back"
        >
          <Ionicons name="arrow-back" size={22} color={colors.onNavy} />
          <Text style={styles.backLabel}>Back</Text>
        </Pressable>

        <Text style={styles.title} numberOfLines={1}>
          {title}
        </Text>

        <View style={styles.guestPill}>
          <Text style={styles.guestPillText}>GUEST</Text>
        </View>
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: {
    backgroundColor: colors.brandNavy,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(156, 123, 92, 0.35)',
  },
  bar: {
    flexDirection: 'row',
    alignItems: 'center',
    minHeight: 48,
    paddingHorizontal: spacing.sm,
    paddingBottom: spacing.sm,
    gap: spacing.sm,
  },
  backBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingVertical: spacing.sm,
    paddingRight: spacing.sm,
    minWidth: 72,
  },
  pressed: {
    opacity: 0.7,
  },
  backLabel: {
    fontFamily: fontFamily.body,
    fontSize: 16,
    fontWeight: '600',
    color: colors.onNavy,
  },
  title: {
    flex: 1,
    fontFamily: fontFamily.heading,
    fontSize: 17,
    fontWeight: '600',
    color: colors.onNavy,
    textAlign: 'center',
  },
  guestPill: {
    paddingHorizontal: spacing.sm,
    paddingVertical: 5,
    borderRadius: 6,
    backgroundColor: colors.brandBronze,
    minWidth: 52,
    alignItems: 'center',
  },
  guestPillText: {
    fontFamily: fontFamily.body,
    fontSize: 10,
    fontWeight: '700',
    color: colors.surfaceWhite,
    letterSpacing: 0.6,
  },
})
