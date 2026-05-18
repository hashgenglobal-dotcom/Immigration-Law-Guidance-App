import { Pressable, StyleSheet, Text, View } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { colors, fontFamily, layout, radii, shadows, spacing } from '@/theme'

export function GuestModeButton({ onPress, disabled }: { onPress: () => void; disabled?: boolean }) {
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      style={({ pressed }) => [
        styles.btn,
        disabled && styles.disabled,
        pressed && !disabled && styles.pressed,
      ]}
      accessibilityRole="button"
      accessibilityLabel="Guest mode"
    >
      <Ionicons name="person-outline" size={18} color={colors.surfaceWhite} />
      <View style={styles.labelCol}>
        <Text style={styles.label}>GUEST MODE</Text>
        <Text style={styles.sublabel}>Limited access</Text>
      </View>
    </Pressable>
  )
}

const styles = StyleSheet.create({
  btn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    minHeight: layout.minTouchTarget,
    borderRadius: radii.button,
    backgroundColor: colors.brandBronze,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
    paddingHorizontal: spacing.lg,
    marginBottom: spacing.sm,
    ...shadows.soft,
  },
  disabled: {
    opacity: 0.45,
  },
  pressed: {
    opacity: 0.9,
    backgroundColor: colors.bronzeDark,
  },
  labelCol: {
    alignItems: 'center',
  },
  label: {
    fontFamily: fontFamily.body,
    fontSize: 14,
    fontWeight: '700',
    color: colors.surfaceWhite,
    letterSpacing: 1.2,
  },
  sublabel: {
    fontFamily: fontFamily.body,
    fontSize: 11,
    fontWeight: '500',
    color: colors.surfaceWhite,
    opacity: 0.85,
    marginTop: 2,
  },
})
