import { Pressable, StyleSheet, Text } from 'react-native'
import { useRouter, type Href } from 'expo-router'
import { Ionicons } from '@expo/vector-icons'
import { colors, fontFamily, layout, spacing } from '@/theme'

export function AuthBackButton({ fallback = '/(auth)/choice' }: { fallback?: Href }) {
  const router = useRouter()

  const handleBack = () => {
    if (router.canGoBack()) {
      router.back()
    } else {
      router.replace(fallback)
    }
  }

  return (
    <Pressable
      onPress={handleBack}
      style={({ pressed }) => [styles.back, pressed && styles.pressed]}
      accessibilityRole="button"
      accessibilityLabel="Go back"
    >
      <Ionicons name="arrow-back" size={22} color={colors.surfaceWhite} />
      <Text style={styles.label}>Back</Text>
    </Pressable>
  )
}

const styles = StyleSheet.create({
  back: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    minHeight: layout.minTouchTarget,
    marginBottom: spacing.md,
    alignSelf: 'flex-start',
  },
  pressed: {
    opacity: 0.75,
  },
  label: {
    fontFamily: fontFamily.body,
    fontSize: 15,
    fontWeight: '500',
    color: colors.surfaceWhite,
    opacity: 0.92,
  },
})
