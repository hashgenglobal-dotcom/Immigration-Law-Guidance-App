import { Pressable, StyleSheet, Text, View } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { colors, fontFamily, layout, radii, spacing } from '@/theme'

/**
 * Web-style assistant entry — tappable faux input that opens /ask (like Hero1 on web).
 */
export function HomeChatPrompt({ onPress }: { onPress: () => void }) {
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel="Open assistant to ask your immigration question"
      style={({ pressed }) => [styles.shell, pressed && styles.shellPressed]}
    >
      <View style={styles.leadingIcons}>
        <View style={styles.iconChip}>
          <Ionicons name="book-outline" size={18} color={colors.brandBronze} />
        </View>
        <View style={styles.iconChip}>
          <Ionicons name="sparkles" size={18} color={colors.brandBronze} />
        </View>
      </View>
      <Text style={styles.placeholder} numberOfLines={1}>
        Ask your immigration question…
      </Text>
      <View style={styles.openBadge}>
        <Ionicons name="chatbubble-ellipses" size={18} color={colors.surfaceWhite} />
        <Text style={styles.openLabel}>Ask</Text>
      </View>
    </Pressable>
  )
}

const styles = StyleSheet.create({
  shell: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: spacing.md,
    minHeight: layout.minTouchTarget,
    borderRadius: radii.full,
    borderWidth: 1,
    borderColor: 'rgba(156, 123, 92, 0.5)',
    backgroundColor: 'rgba(42, 53, 68, 0.94)',
    paddingVertical: 6,
    paddingLeft: 8,
    paddingRight: 6,
    gap: spacing.xs,
    shadowColor: '#1F2839',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 4,
  },
  shellPressed: {
    opacity: 0.92,
    transform: [{ scale: 0.995 }],
  },
  leadingIcons: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  iconChip: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.bronzeTint,
  },
  placeholder: {
    flex: 1,
    fontFamily: fontFamily.body,
    fontSize: 14,
    color: colors.surfaceWhite,
    opacity: 0.85,
    paddingHorizontal: spacing.xs,
  },
  openBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: colors.brandBronze,
    borderRadius: radii.full,
    paddingHorizontal: spacing.sm + 2,
    paddingVertical: spacing.sm,
    minHeight: 36,
  },
  openLabel: {
    fontFamily: fontFamily.body,
    fontSize: 13,
    fontWeight: '600',
    color: colors.surfaceWhite,
  },
})
