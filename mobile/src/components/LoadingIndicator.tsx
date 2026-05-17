import { ActivityIndicator, StyleSheet, Text, View } from 'react-native'
import { colors, spacing, typography } from '@/theme'

export function LoadingIndicator({ message = 'Retrieving information…' }: { message?: string }) {
  return (
    <View style={styles.wrap} accessibilityRole="progressbar">
      <ActivityIndicator size="large" color={colors.bronze} />
      <Text style={styles.text}>{message}</Text>
      <Text style={styles.hint}>Mock response — no network call in this build</Text>
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacing.xl,
    gap: spacing.md,
  },
  text: {
    fontSize: typography.body,
    fontWeight: '600',
    color: colors.text,
  },
  hint: {
    fontSize: typography.caption,
    color: colors.textMuted,
    textAlign: 'center',
    paddingHorizontal: spacing.lg,
  },
})
