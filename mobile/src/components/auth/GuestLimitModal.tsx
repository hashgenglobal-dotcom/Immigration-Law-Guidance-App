import { Modal, Pressable, StyleSheet, Text, View } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { useRouter } from 'expo-router'
import { useAuth } from '@/context/AuthContext'
import { colors, fontFamily, radii, shadows, spacing, typography } from '@/theme'

export function GuestLimitModal({
  visible,
  onClose,
}: {
  visible: boolean
  onClose: () => void
}) {
  const router = useRouter()
  const { signOut } = useAuth()

  const goToAuthChoice = async () => {
    onClose()
    await signOut()
    router.replace('/choice')
  }

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <Pressable style={styles.backdrop} onPress={onClose}>
        <Pressable style={styles.card} onPress={(e) => e.stopPropagation()}>
          <View style={styles.iconSeal}>
            <Ionicons name="chatbubbles-outline" size={28} color={colors.surfaceWhite} />
          </View>
          <Text style={styles.title}>Guest mode limit</Text>
          <Text style={styles.body}>
            Sign up or sign in for full access this session—or stay in guest mode. Live accounts are
            not connected yet; nothing you enter is saved on your device.
          </Text>
          <Pressable
            style={({ pressed }) => [styles.primaryBtn, pressed && styles.pressed]}
            onPress={() => {
              onClose()
              router.push('/signup')
            }}
          >
            <Text style={styles.primaryLabel}>Sign up</Text>
          </Pressable>
          <Pressable
            style={({ pressed }) => [styles.secondaryBtn, pressed && styles.pressed]}
            onPress={() => {
              onClose()
              router.push('/login')
            }}
          >
            <Text style={styles.secondaryLabel}>Sign in</Text>
          </Pressable>
          <Pressable onPress={goToAuthChoice} style={styles.ghostBtn}>
            <Ionicons name="arrow-back" size={16} color={colors.brandBronze} />
            <Text style={styles.ghostLabel}>Back to sign in options</Text>
          </Pressable>
          <Pressable onPress={onClose} style={styles.ghostBtn}>
            <Text style={[styles.ghostLabel, styles.ghostMuted]}>Not now</Text>
          </Pressable>
        </Pressable>
      </Pressable>
    </Modal>
  )
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(17, 22, 32, 0.72)',
    justifyContent: 'center',
    padding: spacing.lg,
  },
  card: {
    backgroundColor: colors.surfaceWhite,
    borderRadius: radii.card,
    padding: spacing.lg,
    alignItems: 'center',
    ...shadows.soft,
  },
  iconSeal: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.brandNavy,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.md,
  },
  title: {
    fontFamily: fontFamily.heading,
    fontSize: typography.h3,
    fontWeight: '600',
    color: colors.brandNavy,
    textAlign: 'center',
    marginBottom: spacing.sm,
  },
  body: {
    fontFamily: fontFamily.body,
    fontSize: typography.small,
    lineHeight: 20,
    color: colors.brandNavy,
    opacity: 0.8,
    textAlign: 'center',
    marginBottom: spacing.lg,
  },
  primaryBtn: {
    alignSelf: 'stretch',
    backgroundColor: colors.brandNavy,
    borderRadius: radii.button,
    minHeight: 48,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.sm,
  },
  primaryLabel: {
    fontFamily: fontFamily.body,
    fontSize: typography.body,
    fontWeight: '600',
    color: colors.onNavy,
  },
  secondaryBtn: {
    alignSelf: 'stretch',
    borderWidth: 1.5,
    borderColor: colors.brandBronze,
    borderRadius: radii.button,
    minHeight: 48,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.sm,
  },
  secondaryLabel: {
    fontFamily: fontFamily.body,
    fontSize: typography.body,
    fontWeight: '600',
    color: colors.brandNavy,
  },
  ghostBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    padding: spacing.sm,
  },
  ghostLabel: {
    fontFamily: fontFamily.body,
    fontSize: typography.small,
    color: colors.brandBronze,
    fontWeight: '600',
  },
  ghostMuted: {
    fontWeight: '400',
    opacity: 0.7,
  },
  pressed: {
    opacity: 0.88,
  },
})
